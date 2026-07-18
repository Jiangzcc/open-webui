from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from .errors import CreditError

_EXPLICIT_FIELDS = frozenset(
    {
        'model',
        'prompt',
        'image',
        'size',
        'resolution',
        'aspect_ratio',
        'quality',
        'n',
    }
)
_GEMINI_SUFFIXES = (':predict', ':generateContent')


class FrozenMapping(Mapping[str, object]):
    """Deep-frozen immutable mapping — does NOT inherit dict.

    ``dict.__setitem__(obj, ...)`` can bypass overridden methods on dict
    subclasses, so we implement ``collections.abc.Mapping`` directly and
    store data in a private ``_data`` attribute that no external code can
    reach without reflection.
    """

    __slots__ = ('_data', '_hash')

    def __init__(self, values: object = ()) -> None:
        source = values.items() if isinstance(values, Mapping) else values
        data = {key: _freeze(item) for key, item in source}
        object.__setattr__(self, '_data', data)
        object.__setattr__(self, '_hash', None)

    # Mapping interface — read-only delegation to _data

    def __getitem__(self, key: str) -> object:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        return f'FrozenMapping({self._data!r})'

    def __hash__(self) -> int:
        if self._hash is None:
            object.__setattr__(self, '_hash', hash(tuple(sorted(self._data.items()))))
        return self._hash

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FrozenMapping):
            return self._data == other._data
        if isinstance(other, Mapping):
            return dict(self._data) == dict(other)
        return NotImplemented

    # Explicitly reject mutation — TypeError for clarity

    def __setitem__(self, key: str, value: object) -> None:
        raise TypeError('FrozenMapping is immutable')

    def __delitem__(self, key: str) -> None:
        raise TypeError('FrozenMapping is immutable')

    # Prevent attribute-level mutation of _data/_hash

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError('FrozenMapping is immutable')

    def __delattr__(self, name: str) -> None:
        raise TypeError('FrozenMapping is immutable')

    def __deepcopy__(self, memo: dict[int, object]) -> FrozenMapping:
        return self

    # JSON serialization support — return plain dict representation

    def __json__(self) -> dict[str, object]:
        return {key: _json_value(item) for key, item in self._data.items()}


def _json_value(value: object) -> object:
    """Convert a frozen value to a JSON-safe plain representation."""
    if isinstance(value, FrozenMapping):
        return value.__json__()
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, frozenset):
        return sorted([_json_value(item) for item in value])
    return value


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return FrozenMapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, frozenset):
        return {_thaw(item) for item in value}
    return value


def thaw_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return {key: _thaw(item) for key, item in value.items()}


@dataclass(frozen=True)
class CompatImageInput:
    model: str | None
    prompt: str
    image: str | tuple[str, ...] | None
    size: str | None
    resolution: str | None
    aspect_ratio: str | None
    quality: str | None
    image_count: int
    extra: Mapping[str, object] = field(default_factory=lambda: FrozenMapping({}))

    def __post_init__(self) -> None:
        frozen_extra = _freeze(dict(self.extra)) if isinstance(self.extra, Mapping) else self.extra
        object.__setattr__(self, 'extra', frozen_extra)
        if isinstance(self.image, list):
            object.__setattr__(self, 'image', tuple(self.image))


@dataclass(frozen=True)
class BillingIdentity:
    user_id: str
    name: str
    email: str
    role: Literal['user', 'admin']


@dataclass(frozen=True)
class ImageBillingContext:
    service_type: Literal['image']
    resource_id: str
    action: Literal['text-to-image', 'image-to-image']
    channel: Literal['web', 'api', 'chat', 'tool']
    dimensions: Mapping[str, str | int]
    prompt_hash: str
    reference_hashes: tuple[str, ...]
    request_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, 'dimensions', _freeze(dict(self.dimensions)))


@dataclass(frozen=True)
class PreparedImageCall:
    billing: ImageBillingContext
    provider_input: CompatImageInput


@dataclass(frozen=True)
class ProviderModelResolution:
    engine: str
    resource_id: str
    transport_model: str


def _mapping_error(reason: str = 'invalid_image_form') -> CreditError:
    return CreditError(code='credit_service_unavailable', context={'reason': reason})


def _validated_dump(raw_form: object, expected_type: type) -> dict[str, object]:
    if isinstance(raw_form, expected_type):
        return raw_form.model_dump()
    if isinstance(raw_form, Mapping):
        raise _mapping_error()
    try:
        validated = expected_type.model_validate(raw_form, from_attributes=True)
    except Exception as error:
        raise _mapping_error() from error
    return validated.model_dump()


def _map_form(raw_form: object, expected_type: type, *, edit: bool) -> CompatImageInput:
    values = _validated_dump(raw_form, expected_type)
    image = values.get('image') if edit else None
    if isinstance(image, list):
        image = tuple(image)
    extra = {key: value for key, value in values.items() if key not in _EXPLICIT_FIELDS}
    count = values.get('n')
    return CompatImageInput(
        model=values.get('model'),
        prompt=values['prompt'],
        image=image,
        size=values.get('size'),
        resolution=values.get('resolution'),
        aspect_ratio=values.get('aspect_ratio'),
        quality=values.get('quality'),
        image_count=1 if count is None else count,
        extra=extra,
    )


def map_generation_form(raw_form: object) -> CompatImageInput:
    from open_webui.routers.images import CreateImageForm

    return _map_form(raw_form, CreateImageForm, edit=False)


def map_edit_form(raw_form: object) -> CompatImageInput:
    from open_webui.routers.images import EditImageForm

    return _map_form(raw_form, EditImageForm, edit=True)


def _form_values(image_input: CompatImageInput, *, edit: bool) -> dict[str, object]:
    values = thaw_mapping(image_input.extra)
    values.update(
        {
            'model': image_input.model,
            'prompt': image_input.prompt,
            'size': image_input.size,
            'resolution': image_input.resolution,
            'aspect_ratio': image_input.aspect_ratio,
            'quality': image_input.quality,
            'n': image_input.image_count,
        }
    )
    if edit:
        values['image'] = list(image_input.image) if isinstance(image_input.image, tuple) else image_input.image
    return values


def to_generation_form(image_input: CompatImageInput) -> object:
    from open_webui.routers.images import CreateImageForm

    return CreateImageForm(**_form_values(image_input, edit=False))


def to_edit_form(image_input: CompatImageInput) -> object:
    from open_webui.routers.images import EditImageForm

    return EditImageForm(**_form_values(image_input, edit=True))


def map_billing_identity(raw_user: object) -> BillingIdentity:
    if raw_user is None or isinstance(raw_user, Mapping):
        raise _mapping_error('invalid_billing_identity')
    fields = {name: getattr(raw_user, name, None) for name in ('id', 'name', 'email', 'role')}
    if any(not isinstance(fields[name], str) or not fields[name].strip() for name in ('id', 'name', 'email')) or fields[
        'role'
    ] not in ('user', 'admin'):
        raise _mapping_error('invalid_billing_identity')
    user_id = fields['id'].strip()
    name = fields['name'].strip()
    email = fields['email'].strip()
    # Enforce database column length limits: user_id ≤ 128, name ≤ 256, email ≤ 320
    if len(user_id) > 128 or len(name) > 256 or len(email) > 320:
        raise _mapping_error('invalid_billing_identity')
    return BillingIdentity(
        user_id=user_id,
        name=name,
        email=email,
        role=fields['role'],
    )


async def get_runtime_image_config() -> object:
    from open_webui.routers.images import get_image_config

    return await get_image_config()


async def get_credit_users(
    filters: dict[str, object],
    skip: int,
    limit: int,
    *,
    session: object,
) -> dict[str, object]:
    from open_webui.models.users import Users

    return await Users.get_users(filters, skip, limit, db=session)


def _price_error(reason: str, engine: str | None = None) -> CreditError:
    context: dict[str, object] = {'reason': reason}
    if engine is not None:
        context['engine'] = engine
    return CreditError(code='price_rule_incomplete', context=context)


def _clean_model(value: object) -> str:
    return value.strip() if isinstance(value, str) else ''


def _gemini_base(value: str) -> str:
    normalized = value.strip()
    for suffix in _GEMINI_SUFFIXES:
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


def _generation_model(engine: str, configured: str, requested: str) -> str:
    if engine == 'openai':
        return configured or 'dall-e-2'
    if engine == 'gemini':
        return _gemini_base(configured or 'imagen-3.0-generate-002')
    if engine == 'fal':
        from open_webui.utils.images.fal import get_fal_generation_model

        return get_fal_generation_model(requested or configured or None)
    if engine == 'comfyui':
        return configured
    return requested or configured


def _edit_model(engine: str, configured: str, requested: str) -> str:
    if engine == 'fal':
        from open_webui.utils.images.fal import get_fal_edit_model

        return get_fal_edit_model(requested or configured or None)
    if engine == 'gemini':
        return _gemini_base(requested or configured)
    return requested or configured


def resolve_provider_model(
    config: object,
    image_input: CompatImageInput,
    action: Literal['text-to-image', 'image-to-image'],
) -> ProviderModelResolution:
    if action == 'text-to-image':
        raw_engine = getattr(config, 'IMAGE_GENERATION_ENGINE', None)
        configured = _clean_model(getattr(config, 'IMAGE_GENERATION_MODEL', None))
        engine = 'automatic1111' if raw_engine == '' else raw_engine
        allowed = {'openai', 'gemini', 'fal', 'comfyui', 'automatic1111'}
    elif action == 'image-to-image':
        engine = getattr(config, 'IMAGE_EDIT_ENGINE', None)
        configured = _clean_model(getattr(config, 'IMAGE_EDIT_MODEL', None))
        allowed = {'openai', 'gemini', 'fal', 'comfyui'}
    else:
        raise _price_error('invalid_image_action')

    if engine not in allowed:
        raise _price_error('unsupported_image_engine', engine if isinstance(engine, str) else None)

    requested = _clean_model(image_input.model)
    model = (
        _generation_model(engine, configured, requested)
        if action == 'text-to-image'
        else _edit_model(engine, configured, requested)
    )

    model = _clean_model(model)
    if not model:
        raise _price_error('missing_provider_model', engine)
    return ProviderModelResolution(engine=engine, resource_id=model, transport_model=model)


def provider_transport_model(resolution: ProviderModelResolution, gemini_method: str) -> str:
    if resolution.engine != 'gemini':
        return resolution.resource_id
    method = gemini_method.lstrip(':')
    if method not in ('predict', 'generateContent'):
        raise _price_error('invalid_gemini_method', resolution.engine)
    return f'{_gemini_base(resolution.resource_id)}:{method}'


def validate_provider_resolution(resolution: ProviderModelResolution) -> None:
    """Ensure resource_id fits within the database column limit of 128 characters."""
    if len(resolution.resource_id) > 128:
        raise _price_error('invalid_resource_id', resolution.engine)


async def publish_credit_price_event(
    request: object,
    operation: Literal['created', 'updated', 'deleted'],
    *,
    actor: object,
    subject_id: str,
    data: dict[str, object],
) -> None:
    from open_webui.events import EVENTS, publish_event

    event = {
        'created': EVENTS.MODEL_PROVIDER_MODEL_CREATED,
        'updated': EVENTS.MODEL_PROVIDER_CONFIG_UPDATED,
        'deleted': EVENTS.MODEL_PROVIDER_MODEL_DELETED,
    }[operation]
    await publish_event(
        request,
        event,
        actor=actor,
        subject_id=subject_id,
        subject_type='credit_price',
        data={'credit_price_operation': operation, **data},
    )


__all__ = [
    'BillingIdentity',
    'CompatImageInput',
    'FrozenMapping',
    'ImageBillingContext',
    'PreparedImageCall',
    'ProviderModelResolution',
    'get_credit_users',
    'get_runtime_image_config',
    'map_billing_identity',
    'map_edit_form',
    'map_generation_form',
    'publish_credit_price_event',
    'provider_transport_model',
    'resolve_provider_model',
    'thaw_mapping',
    'to_edit_form',
    'to_generation_form',
    'validate_provider_resolution',
]
