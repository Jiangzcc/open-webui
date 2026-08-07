"""Compatibility facade for the declarative fal.ai image model catalog.

New models belong in ``open_webui/extensions/fal_catalog/catalog/image``.  This
module keeps the legacy imports used by the image router, billing, creations,
and existing tests without retaining a second hard-coded model registry.
"""

from typing import Any

from open_webui.extensions.fal_catalog.legacy_builders import (  # noqa: F401 - compatibility re-exports
    FAL_ALIBABA_ACCELERATION_OPTIONS,
    FAL_ALIBABA_NAMED_SIZES,
    FAL_BACKGROUND_OPTIONS,
    FAL_COMMON_IMAGE_ASPECT_RATIO_SIZES,
    FAL_GOOGLE_AUTO_IMAGE_RATIOS,
    FAL_GOOGLE_EXTREME_IMAGE_RATIOS,
    FAL_GOOGLE_IMAGE_RATIOS,
    FAL_GOOGLE_NANO_BANANA_2_RESOLUTIONS,
    FAL_GOOGLE_PRO_RESOLUTIONS,
    FAL_GOOGLE_SAFETY_TOLERANCE_OPTIONS,
    FAL_GOOGLE_THINKING_LEVEL_OPTIONS,
    FAL_IMAGE_COUNTS,
    FAL_OPENAI_GPT_IMAGE_2_EDIT_ASPECT_RATIO_SIZES,
    FAL_OPENAI_GPT_IMAGE_15_SIZES,
    FAL_OPENAI_GPT_IMAGE_SIZES,
    FAL_OPENAI_INPUT_FIDELITY_OPTIONS,
    FAL_OPENAI_QUALITY_OPTIONS_WITHOUT_AUTO,
    FAL_OUTPUT_FORMATS,
    FAL_XAI_EDIT_IMAGE_RATIOS,
    FAL_XAI_IMAGE_RATIOS,
    FAL_XAI_RESOLUTIONS,
    _alibaba_model,
    _alibaba_qwen2_model,
    _alibaba_wan_model,
    _apply_image_input,
    _base_model,
    _boolean_field,
    _custom_size_model,
    _google_model,
    _integer_field,
    _openai_model,
    _option_field,
    _text_field,
    _xai_model,
)
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
        public_models.append(public_model)
    return public_models
