"""Compatibility facade for the declarative fal.ai image model catalog.

New models belong in ``open_webui/extensions/fal_catalog/catalog/image``.  This
module keeps the legacy imports used by the image router, billing, creations,
and existing tests without retaining a second hard-coded model registry.
"""

from typing import Any

from open_webui.extensions.fal_catalog.loader import load_image_catalog

_CATALOG = load_image_catalog()

FAL_DEFAULT_IMAGE_MODEL = _CATALOG.generation_default
FAL_DEFAULT_IMAGE_EDIT_MODEL = _CATALOG.edit_default
FAL_IMAGE_MODELS: list[dict[str, Any]] = _CATALOG.legacy_models()

_FAL_INTERNAL_TO_PUBLIC_ID = dict(_CATALOG.internal_to_public)
_FAL_PUBLIC_TO_INTERNAL_ID = dict(_CATALOG.public_to_internal)
_FAL_PUBLIC_MODEL_FIELDS = {
    'id',
    'name',
    'provider',
    'task',
    'generation_model',
    'edit_model',
    'is_default',
    'image_counts',
    'aspect_ratios',
    'aspect_ratio_sizes',
    'resolutions',
    'default_aspect_ratio',
    'default_resolution',
    'output_formats',
    'default_output_format',
    'image_input_max_count',
    'custom_size',
    'quality_options',
    'default_quality',
    'hosting',
}

_PUBLIC_ADVANCED_FIELD_SOURCES = {
    'seed': 'seed',
    'negative_prompt': 'negative_prompt',
    'num_inference_steps': 'steps',
    'steps_num': 'steps',
    'guidance_scale': 'guidance_scale',
    'strength': 'strength',
}


def public_fal_image_advanced_fields(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the curated creative controls safe to advertise to end users.

    The catalog also contains transport, safety and provider-internal fields.
    Keep those server-controlled instead of leaking the raw dynamic envelopes.
    Provider-specific aliases such as ``steps_num`` are normalized to the
    stable request field consumed by the public image forms.
    """

    fields: list[dict[str, Any]] = []
    seen: set[str] = set()
    for kind, group in (
        ('integer', model.get('integer_fields')),
        ('number', model.get('number_fields')),
        ('text', model.get('text_fields')),
    ):
        for item in group or []:
            provider_field = item.get('field')
            public_field = _PUBLIC_ADVANCED_FIELD_SOURCES.get(provider_field)
            if public_field is None or public_field in seen:
                continue
            source = item.get('source')
            if provider_field != public_field and source != public_field:
                continue
            if provider_field == public_field and source is not None and source != public_field:
                continue
            public_item: dict[str, Any] = {'field': public_field, 'kind': kind}
            for key in ('min', 'max'):
                if key in item:
                    public_item[key] = item[key]
            fields.append(public_item)
            seen.add(public_field)
    return fields


def _extract_quality_option(model: dict[str, Any]) -> tuple[list[str], str] | None:
    for item in model.get('option_fields') or []:
        if item.get('field') == 'quality':
            options = item.get('options') or []
            default = item.get('default')
            if options and isinstance(options, list) and isinstance(default, str):
                return list(options), default
    return None


def public_fal_image_model_id(internal_id: str | None) -> str | None:
    if not isinstance(internal_id, str):
        return None
    return _FAL_INTERNAL_TO_PUBLIC_ID.get(internal_id.strip().strip('/'))


def internal_fal_image_model_id(public_id: str | None) -> str | None:
    if not isinstance(public_id, str):
        return None
    return _FAL_PUBLIC_TO_INTERNAL_ID.get(public_id.strip().strip('/'))


def normalize_fal_image_model_id(candidate: str | None) -> str | None:
    if not isinstance(candidate, str):
        return None
    normalized = candidate.strip().strip('/')
    if not normalized:
        return None
    mapped = _FAL_PUBLIC_TO_INTERNAL_ID.get(normalized)
    if mapped is not None:
        return mapped
    if normalized in _FAL_INTERNAL_TO_PUBLIC_ID:
        return normalized
    return None


def public_fal_image_models(default_model: str | None = None) -> list[dict[str, Any]]:
    public_models: list[dict[str, Any]] = []
    for model in FAL_IMAGE_MODELS:
        public_id = public_fal_image_model_id(model['id'])
        if public_id is None:
            continue
        public_model = {key: value for key, value in model.items() if key in _FAL_PUBLIC_MODEL_FIELDS}
        public_model['id'] = public_id
        for relation in ('generation_model', 'edit_model'):
            public_relation = public_fal_image_model_id(model.get(relation))
            if public_relation:
                public_model[relation] = public_relation
            else:
                public_model.pop(relation, None)
        public_model['is_default'] = model['id'] == default_model
        quality = _extract_quality_option(model)
        if quality is not None:
            public_model['quality_options'] = quality[0]
            public_model['default_quality'] = quality[1]
        advanced_fields = public_fal_image_advanced_fields(model)
        if advanced_fields:
            public_model['advanced_fields'] = advanced_fields
        public_models.append(public_model)
    return public_models
