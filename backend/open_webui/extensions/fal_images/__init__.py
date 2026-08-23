"""FAL 图片生成客户端与静态模型注册表（复盘 A1：自上游 utils 目录迁入扩展层）。

- ``client``：FAL queue HTTP 客户端、mock 生图、尺寸校验与载荷构造。
- ``models``：静态图片模型注册表（默认模型、归一化、公开字段）。
"""

from open_webui.extensions.fal_images.client import (
    FAL_DEFAULT_IMAGE_EDIT_MODEL,
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
from open_webui.extensions.fal_images.models import (
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
    'FalImageError',
    'FalImageSizeError',
    'build_fal_image_payload',
    'extract_fal_image_urls',
    'get_fal_edit_model',
    'get_fal_generation_model',
    'get_fal_image_models',
    'get_mock_fal_image_result',
    'normalize_fal_image_model_id',
    'public_fal_image_advanced_fields',
    'public_fal_image_model_id',
    'public_fal_image_models',
    'resume_fal_queue',
    'run_fal_queue',
    'validate_fal_image_size',
]
