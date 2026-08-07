from __future__ import annotations

import json
from collections.abc import Mapping

from open_webui.extensions.credits.models import CreditPrice
from open_webui.extensions.fal_catalog import load_video_catalog
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


def _public_model(definition: FalVideoModelDefinition) -> dict[str, object]:
    payload = definition.model_dump(
        exclude={
            'id',
            'fixed_fields',
            'output_field',
            'output_mime_types',
        }
    )
    payload['id'] = definition.public_id
    payload.pop('public_id', None)
    return payload


def public_video_catalog() -> dict[str, object]:
    catalog = load_video_catalog()
    defaults = {task: catalog.internal_to_public[model_id] for task, model_id in catalog.defaults.items()}
    return {
        'defaults': defaults,
        'models': [_public_model(definition) for definition in catalog.definitions],
    }


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
    price_by_model = {
        (price.resource_id, price.action): price.base_price for price in prices if isinstance(price.base_price, str)
    }
    catalog = load_video_catalog()
    enriched: list[dict[str, object]] = []
    for model in models:
        copy = dict(model)
        public_id = copy.get('id')
        internal_id = catalog.public_to_internal.get(public_id) if isinstance(public_id, str) else None
        action = copy.get('task')
        base_price = price_by_model.get((internal_id, action))
        if base_price is not None:
            copy['base_price'] = base_price
        enriched.append(copy)
    return {**payload, 'models': enriched}


def resolve_video_model(public_id: str) -> FalVideoModelDefinition:
    catalog = load_video_catalog()
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


def build_video_provider_payload(  # noqa: C901
    submission: VideoTaskSubmitForm,
) -> tuple[FalVideoModelDefinition, dict[str, object], dict[str, object]]:
    definition = resolve_video_model(submission.model)
    if definition.task != submission.task:
        raise VideoInputError('video_model_task_mismatch')
    if definition.prompt_required and not submission.prompt:
        raise VideoInputError('prompt_required')

    params: dict[str, object] = dict(submission.params)
    payload: dict[str, object] = dict(definition.fixed_fields)
    if submission.prompt:
        payload['prompt'] = submission.prompt

    _set_supported_option(
        payload,
        params,
        public_key='duration',
        field=definition.duration_field,
        options=definition.durations,
        default=definition.default_duration,
    )
    _set_supported_option(
        payload,
        params,
        public_key='aspect_ratio',
        field=definition.aspect_ratio_field,
        options=definition.aspect_ratios,
        default=definition.default_aspect_ratio,
    )
    _set_supported_option(
        payload,
        params,
        public_key='resolution',
        field=definition.resolution_field,
        options=definition.resolutions,
        default=definition.default_resolution,
    )

    safe_params: dict[str, object] = {key: value for key, value in params.items() if value is not None}
    for public_key, field in (
        ('duration', definition.duration_field),
        ('aspect_ratio', definition.aspect_ratio_field),
        ('resolution', definition.resolution_field),
    ):
        if field is not None and field in payload:
            safe_params[public_key] = payload[field]

    if definition.durations is None and definition.duration_field is not None and definition.duration_field in payload:
        try:
            duration = float(payload[definition.duration_field])
        except (TypeError, ValueError) as error:
            raise VideoInputError('invalid_duration') from error
        if (definition.duration_min is not None and duration < definition.duration_min) or (
            definition.duration_max is not None and duration > definition.duration_max
        ):
            raise VideoInputError('invalid_duration')

    audio_mode = params.get('audio_mode', definition.default_audio_mode)
    if audio_mode is not None:
        audio_option = next(
            (option for option in definition.audio_options or () if option.mode == audio_mode),
            None,
        )
        if audio_option is None:
            raise VideoInputError('invalid_audio_mode')
        payload.update(audio_option.values)
        safe_params['audio_mode'] = str(audio_mode)

    consumed = {'duration', 'aspect_ratio', 'resolution', 'audio_mode'}
    for group in (
        definition.option_fields,
        definition.boolean_fields,
        definition.integer_fields,
        definition.number_fields,
        definition.text_fields,
        definition.json_fields,
    ):
        for field in group or ():
            public_key = field.source or field.field
            consumed.add(public_key)
            value = params.get(public_key, field.default if hasattr(field, 'default') else None)
            if value is None:
                if isinstance(field, VideoJsonField) and field.required:
                    raise VideoInputError(f'missing_{public_key}')
                continue
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
                or (field.min is not None and value < field.min)
                or (field.max is not None and value > field.max)
            ):
                raise VideoInputError(f'invalid_{public_key}')
            if isinstance(field, VideoTextField) and (not isinstance(value, str) or len(value) > field.max_length):
                raise VideoInputError(f'invalid_{public_key}')
            if isinstance(field, VideoJsonField):
                if not isinstance(value, str) or len(value) > field.max_length:
                    raise VideoInputError(f'invalid_{public_key}')
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError as error:
                    raise VideoInputError(f'invalid_{public_key}') from error
                if not isinstance(parsed_value, (dict, list)):
                    raise VideoInputError(f'invalid_{public_key}')
                payload[field.field] = parsed_value
                safe_params[public_key] = parsed_value
            else:
                payload[field.field] = value
                safe_params[public_key] = value

    unknown = set(params) - consumed
    if unknown:
        raise VideoInputError(f'unsupported_video_parameter:{sorted(unknown)[0]}')

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

    return definition, payload, safe_params


__all__ = [
    'VideoInputError',
    'build_video_provider_payload',
    'public_video_catalog',
    'public_video_catalog_for_user',
    'resolve_video_model',
]
