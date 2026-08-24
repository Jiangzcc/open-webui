"""Stable upstream import facade for the isolated FAL image extension.

The implementation lives under ``extensions`` so upstream router merges keep
this historical public import path and need only a thin bridge.
"""

from open_webui.extensions.fal_images.client import (
    FAL_DEFAULT_IMAGE_MODEL,
    FalImageError,
    FalImageSizeError,
    build_fal_image_payload,
    extract_fal_image_urls,
    get_fal_edit_model,
    get_fal_generation_model,
    get_fal_image_models,
    get_mock_fal_image_result,
    resume_fal_queue,
    run_fal_queue,
    validate_fal_image_size,
)

__all__ = [
    'FAL_DEFAULT_IMAGE_MODEL',
    'FalImageError',
    'FalImageSizeError',
    'build_fal_image_payload',
    'extract_fal_image_urls',
    'get_fal_edit_model',
    'get_fal_generation_model',
    'get_fal_image_models',
    'get_mock_fal_image_result',
    'resume_fal_queue',
    'run_fal_queue',
    'validate_fal_image_size',
]
