from __future__ import annotations

import json
import math
from collections.abc import Mapping

from open_webui.extensions.credits.models import CreditPrice
from open_webui.extensions.fal_catalog import load_video_catalog_cached
from open_webui.extensions.fal_catalog.video_schemas import (
    FalVideoModelDefinition,
    VideoBooleanField,
    VideoIntegerField,
    VideoJsonField,
    VideoNumberField,
    VideoOptionField,
    VideoTextField,
)
from open_webui.extensions.model_ops.service import apply_model_operations
from open_webui.extensions.videos.schemas import VideoTaskSubmitForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class VideoInputError(ValueError):
    pass


_PUBLIC_ADVANCED_FIELD_KEYS = {
    'seed': 'seed',
    'negative_prompt': 'negative_prompt',
    'prompt_optimizer': 'prompt_enhancement',
    'enable_prompt_expansion': 'prompt_enhancement',
    'thinking_type': 'prompt_enhancement',
    'movement_amplitude': 'motion_amplitude',
    'cfg_scale': 'guidance_scale',
    'fps': 'fps',
    'bitrate_mode': 'output_quality',
    'loop': 'loop',
    'edit_strength': 'edit_strength',
    'retake_mode': 'retake_mode',
    'start_time': 'start_time',
    'ingredients_mode': 'ingredients_mode',
}
_PUBLIC_ADVANCED_FIELD_ORDER = tuple(dict.fromkeys(_PUBLIC_ADVANCED_FIELD_KEYS.values()))
_PROMPT_ENHANCEMENT_TO_PROVIDER = {
    'on': 'enabled',
    'off': 'disabled',
    'auto': 'auto',
}
_SERVER_CONTROLLED_DYNAMIC_FIELDS = {'safety_tolerance', 'auto_fix'}


def _advanced_public_key(field: object) -> str | None:
    provider_key = getattr(field, 'source', None) or getattr(field, 'field', None)
    return _PUBLIC_ADVANCED_FIELD_KEYS.get(provider_key)


def _public_advanced_value(value: object, public_key: str) -> object:
    if public_key != 'prompt_enhancement' or value is None:
        return value
    if isinstance(value, bool):
        return 'on' if value else 'off'
    return {'enabled': 'on', 'disabled': 'off', 'auto': 'auto'}.get(value, value)


def _public_advanced_default(field: object, public_key: str) -> object:
    return _public_advanced_value(getattr(field, 'default', None), public_key)


def _public_advanced_options(field: object, public_key: str) -> list[str] | None:
    if public_key == 'prompt_enhancement':
        if isinstance(field, VideoBooleanField):
            return ['on', 'off']
        provider_options = getattr(field, 'options', None) or ()
        return [{'enabled': 'on', 'disabled': 'off', 'auto': 'auto'}.get(option, option) for option in provider_options]
    options = getattr(field, 'options', None)
    return list(options) if options else None


def public_video_advanced_fields(definition: FalVideoModelDefinition) -> list[dict[str, object]]:
    fields: list[dict[str, object]] = []
    groups = (
        ('option', definition.option_fields),
        ('boolean', definition.boolean_fields),
        ('integer', definition.integer_fields),
        ('number', definition.number_fields),
        ('text', definition.text_fields),
    )
    for kind, group in groups:
        for field in group or ():
            descriptor = _public_video_advanced_field(field, kind)
            if descriptor is not None:
                fields.append(descriptor)
    order = {key: index for index, key in enumerate(_PUBLIC_ADVANCED_FIELD_ORDER)}
    return sorted(fields, key=lambda item: order[str(item['key'])])


def _public_video_advanced_field(field: object, kind: str) -> dict[str, object] | None:
    public_key = _advanced_public_key(field)
    if public_key is None or not field.advanced:
        return None
    descriptor: dict[str, object] = {
        'key': public_key,
        'kind': 'option' if public_key == 'prompt_enhancement' else kind,
    }
    options = _public_advanced_options(field, public_key)
    default = _public_advanced_default(field, public_key)
    if options:
        descriptor['options'] = options
    if default is not None:
        descriptor['default'] = default
    descriptor.update(
        {
            attribute: value
            for attribute in ('min', 'max', 'step', 'max_length')
            if (value := getattr(field, attribute, None)) is not None
        }
    )
    return descriptor


def _public_model(definition: FalVideoModelDefinition) -> dict[str, object]:
    payload = definition.model_dump(
        exclude={
            'id',
            'fixed_fields',
            'output_field',
            'output_mime_types',
            'option_fields',
            'boolean_fields',
            'integer_fields',
            'number_fields',
            'text_fields',
            'json_fields',
        }
    )
    payload['id'] = definition.public_id
    payload.pop('public_id', None)
    advanced_fields = public_video_advanced_fields(definition)
    if advanced_fields:
        payload['advanced_fields'] = advanced_fields
    return payload


def _supported_by_public_editor(definition: FalVideoModelDefinition) -> bool:
    return not any(field.required and field.primary_input for field in definition.json_fields or ())


def public_video_catalog() -> dict[str, object]:
    catalog = load_video_catalog_cached()
    defaults = {task: catalog.internal_to_public[model_id] for task, model_id in catalog.defaults.items()}
    return {
        'defaults': defaults,
        'models': [
            _public_model(definition) for definition in catalog.definitions if _supported_by_public_editor(definition)
        ],
    }


def _duration_pricing_is_proportional(rules: object) -> bool:
    """该模型的 duration 维度是否按秒（proportional）计费。

    proportional 规则用 unit_size 缩放时长，pricing._resolve_proportional 会
    调 _positive_decimal 解析维度值；'auto' 这类非数值无法解析（返回 None），
    导致 compute_price 抛 price_rule_incomplete、报价端点返回 configured=False。
    因此这类模型的公共目录必须隐藏 'auto' 时长选项，并把 default_duration
    重置为具体秒数，否则用户默认进入即看到"积分未配置"而模型名后却显示有价。

    用轻量 dict 判断而非 PriceRuleSet.model_validate，避免某条规则格式异常时
    拖垮整个目录加载——catalog 层只决定可见性，定价校验仍由 pricing 层兜底。
    """
    if not isinstance(rules, dict):
        return False
    dimensions = rules.get('dimensions')
    if not isinstance(dimensions, list):
        return False
    return any(
        isinstance(dimension, dict) and dimension.get('key') == 'duration' and dimension.get('kind') == 'proportional'
        for dimension in dimensions
    )


async def public_video_catalog_for_user(session: AsyncSession) -> dict[str, object]:
    payload = public_video_catalog()
    models = await apply_model_operations(
        session,
        payload['models'],
        admin=False,
        media_kind='video',
    )
    prices = (
        await session.scalars(
            select(CreditPrice).where(
                CreditPrice.service_type == 'video',
                CreditPrice.enabled.is_(True),
            )
        )
    ).all()
    price_by_model = {(price.resource_id, price.action): price.base_price for price in prices}
    rules_by_model = {(price.resource_id, price.action): price.rules for price in prices}
    catalog = load_video_catalog_cached()
    enriched: list[dict[str, object]] = []
    for model in models:
        enriched.append(_enriched_video_model(model, catalog, price_by_model, rules_by_model))
    return {**payload, 'models': enriched}


def _enriched_video_model(
    model: dict[str, object],
    catalog: object,
    prices: dict[tuple[object, object], int],
    rules: dict[tuple[object, object], object],
) -> dict[str, object]:
    enriched = dict(model)
    public_id = enriched.get('id')
    internal_id = catalog.public_to_internal.get(public_id) if isinstance(public_id, str) else None
    action = enriched.get('task')
    base_price = prices.get((internal_id, action))
    if base_price is not None:
        enriched['base_price'] = base_price
    if not _duration_pricing_is_proportional(rules.get((internal_id, action))):
        return enriched
    durations = enriched.get('durations')
    if not isinstance(durations, list) or 'auto' not in durations:
        return enriched
    filtered = [value for value in durations if value != 'auto']
    if not filtered:
        return enriched
    enriched['durations'] = filtered
    if enriched.get('default_duration') == 'auto':
        enriched['default_duration'] = filtered[0]
    return enriched


def resolve_video_model(public_id: str) -> FalVideoModelDefinition:
    catalog = load_video_catalog_cached()
    internal_id = catalog.public_to_internal.get(public_id)
    if internal_id is None:
        raise VideoInputError('unknown_video_model')
    return next(definition for definition in catalog.definitions if definition.id == internal_id)


def _set_supported_option(
    payload: dict[str, object],
    params: Mapping[str, object],
    *,
    public_key: str,
    field: str | None,
    options: list[str] | None,
    default: str | None,
) -> None:
    if field is None:
        if public_key in params:
            raise VideoInputError(f'unsupported_{public_key}')
        return
    value = params.get(public_key, default)
    if value is None:
        return
    if not isinstance(value, str) or (options is not None and value not in options):
        raise VideoInputError(f'invalid_{public_key}')
    payload[field] = value


def _apply_primary_options(
    definition: FalVideoModelDefinition,
    params: Mapping[str, object],
    payload: dict[str, object],
) -> dict[str, object]:
    options = (
        ('duration', definition.duration_field, definition.durations, definition.default_duration),
        ('aspect_ratio', definition.aspect_ratio_field, definition.aspect_ratios, definition.default_aspect_ratio),
        ('resolution', definition.resolution_field, definition.resolutions, definition.default_resolution),
    )
    safe_params = {key: value for key, value in params.items() if value is not None}
    for public_key, field, allowed, default in options:
        _set_supported_option(
            payload,
            params,
            public_key=public_key,
            field=field,
            options=allowed,
            default=default,
        )
        if field is not None and field in payload:
            safe_params[public_key] = payload[field]
    return safe_params


def _validate_freeform_duration(definition: FalVideoModelDefinition, payload: Mapping[str, object]) -> None:
    field = definition.duration_field
    if definition.durations is not None or field is None or field not in payload:
        return
    try:
        duration = float(payload[field])
    except (TypeError, ValueError) as error:
        raise VideoInputError('invalid_duration') from error
    if (definition.duration_min is not None and duration < definition.duration_min) or (
        definition.duration_max is not None and duration > definition.duration_max
    ):
        raise VideoInputError('invalid_duration')


def _apply_audio_mode(
    definition: FalVideoModelDefinition,
    params: Mapping[str, object],
    payload: dict[str, object],
    safe_params: dict[str, object],
) -> None:
    audio_mode = params.get('audio_mode', definition.default_audio_mode)
    if audio_mode is None:
        return
    audio_option = next((option for option in definition.audio_options or () if option.mode == audio_mode), None)
    if audio_option is None:
        raise VideoInputError('invalid_audio_mode')
    payload.update(audio_option.values)
    safe_params['audio_mode'] = str(audio_mode)


def _normalize_prompt_enhancement(
    field: object,
    value: object,
    public_key: str,
    submitted_key: str,
) -> object:
    if public_key != 'prompt_enhancement' or submitted_key != public_key:
        return value
    if isinstance(field, VideoBooleanField):
        if value not in {'on', 'off'}:
            raise VideoInputError(f'invalid_{public_key}')
        return value == 'on'
    if value not in _PROMPT_ENHANCEMENT_TO_PROVIDER:
        raise VideoInputError(f'invalid_{public_key}')
    return _PROMPT_ENHANCEMENT_TO_PROVIDER[str(value)]


def _validated_dynamic_value(field: object, value: object, public_key: str) -> object:
    if isinstance(field, VideoOptionField) and (not isinstance(value, str) or value not in field.options):
        raise VideoInputError(f'invalid_{public_key}')
    if isinstance(field, VideoBooleanField) and not isinstance(value, bool):
        raise VideoInputError(f'invalid_{public_key}')
    if isinstance(field, VideoIntegerField) and (
        isinstance(value, bool)
        or not isinstance(value, int)
        or (field.min is not None and value < field.min)
        or (field.max is not None and value > field.max)
    ):
        raise VideoInputError(f'invalid_{public_key}')
    if isinstance(field, VideoNumberField) and (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or (field.min is not None and value < field.min)
        or (field.max is not None and value > field.max)
    ):
        raise VideoInputError(f'invalid_{public_key}')
    if isinstance(field, VideoTextField) and (not isinstance(value, str) or len(value) > field.max_length):
        raise VideoInputError(f'invalid_{public_key}')
    return _validated_json_field(field, value, public_key)


def _validated_json_field(field: object, value: object, public_key: str) -> object:
    if not isinstance(field, VideoJsonField):
        return value
    if not isinstance(value, str) or len(value) > field.max_length:
        raise VideoInputError(f'invalid_{public_key}')
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise VideoInputError(f'invalid_{public_key}') from error
    if not isinstance(parsed, (dict, list)):
        raise VideoInputError(f'invalid_{public_key}')
    return parsed


def _apply_dynamic_field(
    field: object,
    params: Mapping[str, object],
    payload: dict[str, object],
    safe_params: dict[str, object],
) -> set[str]:
    legacy_key = field.source or field.field
    if legacy_key in _SERVER_CONTROLLED_DYNAMIC_FIELDS:
        if legacy_key in params:
            raise VideoInputError(f'unsupported_video_parameter:{legacy_key}')
        default = getattr(field, 'default', None)
        if default is not None:
            payload[field.field] = default
        return {legacy_key}
    public_key = _advanced_public_key(field) or legacy_key
    if public_key != legacy_key and public_key in params and legacy_key in params:
        raise VideoInputError(f'conflicting_video_parameter:{public_key}')
    if public_key != legacy_key:
        safe_params.pop(legacy_key, None)
    submitted_key = public_key if public_key in params else legacy_key
    value = params.get(submitted_key, getattr(field, 'default', None))
    if value is None:
        if isinstance(field, VideoJsonField) and field.required:
            raise VideoInputError(f'missing_{public_key}')
        return {legacy_key, public_key}
    value = _normalize_prompt_enhancement(field, value, public_key, submitted_key)
    provider_value = _validated_dynamic_value(field, value, public_key)
    payload[field.field] = provider_value
    safe_params[public_key] = (
        provider_value if isinstance(field, VideoJsonField) else _public_advanced_value(value, public_key)
    )
    return {legacy_key, public_key}


def _apply_dynamic_fields(
    definition: FalVideoModelDefinition,
    params: Mapping[str, object],
    payload: dict[str, object],
    safe_params: dict[str, object],
) -> set[str]:
    consumed = {'duration', 'aspect_ratio', 'resolution', 'audio_mode'}
    groups = (
        definition.option_fields,
        definition.boolean_fields,
        definition.integer_fields,
        definition.number_fields,
        definition.text_fields,
        definition.json_fields,
    )
    for group in groups:
        for field in group or ():
            consumed.update(_apply_dynamic_field(field, params, payload, safe_params))
    return consumed


def _validate_submitted_assets(definition: FalVideoModelDefinition, submission: VideoTaskSubmitForm) -> None:
    definitions_by_role = {asset.role: asset for asset in definition.asset_inputs or ()}
    asset_counts: dict[str, int] = {}
    for submitted_asset in submission.assets:
        role = submitted_asset.role
        if role not in definitions_by_role:
            raise VideoInputError(f'unsupported_video_asset:{role}')
        asset_counts[role] = asset_counts.get(role, 0) + 1
        constraint = definitions_by_role[role]
        if (not constraint.multiple and asset_counts[role] > 1) or asset_counts[role] > constraint.max_count:
            raise VideoInputError(f'too_many_video_assets:{role}')
    for asset in definition.asset_inputs or ():
        if asset.required and asset_counts.get(asset.role, 0) == 0:
            raise VideoInputError(f'missing_video_asset:{asset.role}')


def build_video_provider_payload(
    submission: VideoTaskSubmitForm,
) -> tuple[FalVideoModelDefinition, dict[str, object], dict[str, object]]:
    definition = resolve_video_model(submission.model)
    if definition.task != submission.task:
        raise VideoInputError('video_model_task_mismatch')
    # prompt 即用户输入的纯文本（标签点击时已在输入框插入 insert_text）。
    prompt = submission.prompt
    if definition.prompt_required and not prompt:
        raise VideoInputError('prompt_required')

    params: dict[str, object] = dict(submission.params)
    payload: dict[str, object] = dict(definition.fixed_fields)
    if prompt:
        payload['prompt'] = prompt

    safe_params = _apply_primary_options(definition, params, payload)
    _validate_freeform_duration(definition, payload)
    _apply_audio_mode(definition, params, payload, safe_params)
    consumed = _apply_dynamic_fields(definition, params, payload, safe_params)
    unknown = set(params) - consumed
    if unknown:
        raise VideoInputError(f'unsupported_video_parameter:{sorted(unknown)[0]}')
    _validate_submitted_assets(definition, submission)
    return definition, payload, safe_params


__all__ = [
    'VideoInputError',
    'build_video_provider_payload',
    'public_video_catalog',
    'public_video_catalog_for_user',
    'public_video_advanced_fields',
    'resolve_video_model',
]
