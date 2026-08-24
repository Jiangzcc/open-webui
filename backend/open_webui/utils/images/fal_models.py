"""Stable upstream import facade for the declarative FAL image catalog."""

from open_webui.extensions.fal_images.models import (
    FAL_DEFAULT_IMAGE_EDIT_MODEL,
    FAL_DEFAULT_IMAGE_MODEL,
    FAL_IMAGE_MODELS,
    normalize_fal_image_model_id,
    public_fal_image_advanced_fields,
    public_fal_image_model_id,
    public_fal_image_models,
)

__all__ = [
    'FAL_DEFAULT_IMAGE_EDIT_MODEL',
    'FAL_DEFAULT_IMAGE_MODEL',
    'FAL_IMAGE_MODELS',
    'normalize_fal_image_model_id',
    'public_fal_image_advanced_fields',
    'public_fal_image_model_id',
    'public_fal_image_models',
]
