import logging
import random
import re
from typing import Any

from open_webui.extensions.fal_images.errors import FalImageError as FalImageError
from open_webui.extensions.fal_images.errors import FalImageSizeError as FalImageSizeError
from open_webui.extensions.fal_images.models import (
    FAL_DEFAULT_IMAGE_EDIT_MODEL,
    FAL_DEFAULT_IMAGE_MODEL,
    FAL_IMAGE_MODELS,
    normalize_fal_image_model_id,
)
from open_webui.extensions.fal_images.queue_client import resume_fal_queue as resume_fal_queue
from open_webui.extensions.fal_images.queue_client import run_fal_queue as run_fal_queue

log = logging.getLogger(__name__)

FAL_MOCK_IMAGE_BASE_URL = 'https://picsum.photos'
FAL_MOCK_DEFAULT_SIZE = (1024, 1024)
FAL_MOCK_ASPECT_RATIO_SIZES = {
    '1:1': (1024, 1024),
    '16:9': (1792, 1024),
    '9:16': (1024, 1792),
    '3:4': (768, 1024),
    '4:3': (1024, 768),
    '3:2': (1536, 1024),
    '2:3': (1024, 1536),
    '21:9': (1536, 640),
    '2:1': (1536, 768),
    '1:2': (768, 1536),
    '20:9': (1536, 691),
    '9:20': (691, 1536),
    '19.5:9': (1536, 709),
    '9:19.5': (709, 1536),
    '5:4': (1280, 1024),
    '4:5': (1024, 1280),
    '4:1': (1536, 384),
    '1:4': (384, 1536),
    '8:1': (1536, 192),
    '1:8': (192, 1536),
}


def _normalize_model_id(model: str | None) -> str:
    return (model or '').strip().strip('/')


def _get_fal_model_info(model: str | None) -> dict[str, Any] | None:
    normalized_model = _normalize_model_id(model)
    if not normalized_model:
        return None

    for item in FAL_IMAGE_MODELS:
        if item['id'] == normalized_model:
            return item

    for item in FAL_IMAGE_MODELS:
        if item.get('edit_model') == normalized_model:
            return item
        if item.get('generation_model') == normalized_model:
            return item

    return None


def _safe_option(value: str | None, options: list[str] | None, default: str | None) -> str | None:
    if options:
        return value if value in options else default

    return value or default


def _safe_count(value: int | None, options: list[int] | None) -> int | None:
    if not isinstance(value, int) or value <= 0:
        return None
    if options and value not in options:
        return None

    return value


def _set_option(
    data: dict[str, Any],
    field: str | None,
    value: str | None,
    options: list[str] | None,
    default: str | None,
) -> None:
    if not field:
        return

    option = _safe_option(value, options, default)
    if option:
        data[field] = int(option) if field == 'max_image_size' and option.isdigit() else option


def _parse_pixel_size(value: str) -> tuple[int, int] | None:
    """Parse a ``"WxH"`` string into a ``(width, height)`` int tuple."""
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r'(\d+)x(\d+)', value.strip())
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def _validate_custom_size(
    width: int,
    height: int,
    constraints: dict[str, Any] | None,
) -> str | None:
    """Return a localized reason string when a custom size violates the model's rules."""
    if width <= 0 or height <= 0:
        return 'width and height must be positive integers'
    if not constraints:
        return None
    min_w = constraints.get('min_width')
    max_w = constraints.get('max_width')
    min_h = constraints.get('min_height')
    max_h = constraints.get('max_height')
    pixels = width * height
    min_pixels = constraints.get('min_pixels')
    max_pixels = constraints.get('max_pixels')
    ratio = width / height
    ar_min = constraints.get('aspect_ratio_min')
    ar_max = constraints.get('aspect_ratio_max')
    bounds = (
        (min_w is None or width >= min_w, f'width {width} below minimum {min_w}'),
        (max_w is None or width <= max_w, f'width {width} above maximum {max_w}'),
        (min_h is None or height >= min_h, f'height {height} below minimum {min_h}'),
        (max_h is None or height <= max_h, f'height {height} above maximum {max_h}'),
        (min_pixels is None or pixels >= min_pixels, f'total pixels {pixels} below minimum {min_pixels}'),
        (max_pixels is None or pixels <= max_pixels, f'total pixels {pixels} above maximum {max_pixels}'),
        (ar_min is None or ratio >= ar_min, f'aspect ratio {ratio:.3f} below minimum {ar_min}'),
        (ar_max is None or ratio <= ar_max, f'aspect ratio {ratio:.3f} above maximum {ar_max}'),
    )
    for valid, reason in bounds:
        if not valid:
            return reason

    multiple_of = constraints.get('multiple_of')
    if multiple_of and (width % multiple_of or height % multiple_of):
        return f'dimensions must be multiples of {multiple_of}'
    return None


def validate_fal_image_size(model: str | None, form_data: Any) -> None:
    """Validate an explicit custom size before credit precharge/provider invocation."""
    normalized_model = normalize_fal_image_model_id(model) or _normalize_model_id(model)
    model_info = _get_fal_model_info(normalized_model)
    if not model_info or not model_info.get('custom_size_field'):
        return

    sizes = model_info.get('image_size_whitelist') or model_info.get('aspect_ratio_sizes')
    requested_size = _resolve_requested_size(form_data, sizes, model_info.get('resolution_multipliers'))
    if not requested_size or requested_size == 'auto':
        return

    parsed = _parse_pixel_size(requested_size)
    if parsed is None:
        if getattr(form_data, 'size', None):
            raise FalImageSizeError(f'unsupported image size {requested_size}: expected WIDTHxHEIGHT')
        # 无显式 size 且档位（'2K'/'4K'）无法折算出尺寸（缺比例基线）时，
        # 该值不属于 size 语义，交由载荷构造与选项校验处理，不再误拒合法档位请求。
        return
    if sizes and requested_size in sizes.values():
        return

    reason = _validate_custom_size(*parsed, model_info.get('custom_size'))
    if reason is not None:
        raise FalImageSizeError(f'unsupported image size {requested_size}: {reason}')


def _scale_pixel_size(wxh: str, multiplier: int) -> str:
    parsed = _parse_pixel_size(wxh)
    if parsed is None or multiplier <= 1:
        return wxh
    width, height = parsed
    return f'{width * multiplier}x{height * multiplier}'


def _resolve_requested_size(
    form_data: Any,
    sizes: dict[str, str] | None,
    multipliers: dict[str, int] | None = None,
) -> str | None:
    """Resolve the effective requested size (复盘 P0-2：校验、载荷构造、计价共用的单一规则).

    - A "WxH"-shaped resolution is the most explicit dimension statement and
      wins over ``size`` (mirrors the resolution_field path).
    - An explicit ``size`` comes next.
    - A resolution tier like "2K"/"4K" only scales the aspect-ratio baseline and
      never overrides an explicit dimension.
    """
    resolution = getattr(form_data, 'resolution', None)
    if resolution and _parse_pixel_size(resolution) is not None:
        return resolution

    requested_size = getattr(form_data, 'size', None)
    if not requested_size:
        baseline = (sizes or {}).get(getattr(form_data, 'aspect_ratio', None))
        if baseline:
            requested_size = _scale_pixel_size(baseline, (multipliers or {}).get(resolution, 1))
    return requested_size


def _set_custom_image_size(
    data: dict[str, Any],
    field: str | None,
    form_data: Any,
    sizes: dict[str, str] | None,
    constraints: dict[str, Any] | None,
    multipliers: dict[str, int] | None = None,
) -> None:
    if not field:
        return

    requested_size = _resolve_requested_size(form_data, sizes, multipliers)

    if not requested_size:
        return

    # 'auto' is a model-side hint ("infer from input"), not a dimension; pass through
    # as the enum string. Every other value is normalized to a {width, height} object.
    if requested_size == 'auto':
        data[field] = 'auto'
        return

    parsed = _parse_pixel_size(requested_size)
    if parsed is None:
        return
    width, height = parsed

    # Curated presets (declared in image_size_whitelist) are known-good; skip the
    # custom-rule check so legacy whitelists stay authoritative. Any other size must
    # satisfy the model's custom_size constraints.
    in_whitelist = bool(sizes) and requested_size in sizes.values()
    if not in_whitelist:
        reason = _validate_custom_size(width, height, constraints)
        if reason is not None:
            raise FalImageSizeError(f'unsupported image size {requested_size}: {reason}')

    data[field] = {'width': width, 'height': height}


def _set_image_input(
    data: dict[str, Any],
    field: str,
    image_urls: list[str],
    max_count: int | None = None,
) -> None:
    images = image_urls[:max_count] if max_count else image_urls

    if field == 'image_url':
        if images:
            data[field] = images[0]
        return

    data[field] = images


def _get_field_value(form_data: Any, source: str | None, field: str) -> Any:
    return getattr(form_data, source or field, None)


def _set_option_fields(data: dict[str, Any], form_data: Any, fields: list[dict[str, Any]] | None) -> None:
    for item in fields or []:
        field = item.get('field')
        if not field:
            continue

        _set_option(
            data,
            field,
            _get_field_value(form_data, item.get('source'), field),
            item.get('options', []),
            item.get('default'),
        )


def _set_boolean_fields(data: dict[str, Any], form_data: Any, fields: list[dict[str, Any]] | None) -> None:
    for item in fields or []:
        field = item.get('field')
        if not field:
            continue

        value = _get_field_value(form_data, item.get('source'), field)
        if value is None:
            value = item.get('default')
        if isinstance(value, bool):
            data[field] = value


def _set_integer_fields(data: dict[str, Any], form_data: Any, fields: list[dict[str, Any]] | None) -> None:
    for item in fields or []:
        field = item.get('field')
        if not field:
            continue

        value = _get_field_value(form_data, item.get('source'), field)
        if not isinstance(value, int):
            continue

        minimum = item.get('min')
        maximum = item.get('max')
        if isinstance(minimum, int) and value < minimum:
            continue
        if isinstance(maximum, int) and value > maximum:
            continue

        data[field] = value


def _set_number_fields(data: dict[str, Any], form_data: Any, fields: list[dict[str, Any]] | None) -> None:
    for item in fields or []:
        field = item.get('field')
        if not field:
            continue

        value = _get_field_value(form_data, item.get('source'), field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue

        minimum = item.get('min')
        maximum = item.get('max')
        if isinstance(minimum, (int, float)) and value < minimum:
            continue
        if isinstance(maximum, (int, float)) and value > maximum:
            continue

        data[field] = value


def _set_text_fields(data: dict[str, Any], form_data: Any, fields: list[dict[str, Any]] | None) -> None:
    for item in fields or []:
        field = item.get('field')
        if not field:
            continue

        value = _get_field_value(form_data, item.get('source'), field)
        if isinstance(value, str) and value.strip():
            data[field] = value.strip()


def get_fal_image_models() -> list[dict[str, Any]]:
    """管理端模型列表（只读共享常量）。

    复盘 P2：原先每次调用全量 deepcopy（约 5ms/次），而唯一生产调用方
    （routers/images.py 管理端列表）只读遍历（``{**model, ...}`` 浅展开）。
    调用方不得原地修改返回结构——需要可变副本时自行 copy。
    """
    return FAL_IMAGE_MODELS


def _mock_named_resolution_size(resolution: object, aspect_ratio: object) -> tuple[int, int] | None:
    if not isinstance(resolution, str):
        return None
    resolution_match = re.fullmatch(r'(\d+(?:\.\d+)?)K', resolution.strip(), re.IGNORECASE)
    if resolution_match is None:
        return None

    longest_edge = round(float(resolution_match.group(1)) * 1024)
    ratio_match = (
        re.fullmatch(r'(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)', aspect_ratio.strip())
        if isinstance(aspect_ratio, str)
        else None
    )
    if ratio_match is None:
        return longest_edge, longest_edge

    ratio_width, ratio_height = map(float, ratio_match.groups())
    if ratio_width >= ratio_height:
        return longest_edge, max(1, round(longest_edge * ratio_height / ratio_width))
    return max(1, round(longest_edge * ratio_width / ratio_height)), longest_edge


def _mock_image_size(form_data: Any) -> tuple[int, int]:
    for value in (getattr(form_data, 'size', None), getattr(form_data, 'resolution', None)):
        if not isinstance(value, str):
            continue
        match = re.fullmatch(r'(\d{1,4})x(\d{1,4})', value.strip(), re.IGNORECASE)
        if match:
            width, height = map(int, match.groups())
            if width > 0 and height > 0:
                return width, height

    aspect_ratio = getattr(form_data, 'aspect_ratio', None)
    named_resolution_size = _mock_named_resolution_size(getattr(form_data, 'resolution', None), aspect_ratio)
    if named_resolution_size is not None:
        return named_resolution_size
    if isinstance(aspect_ratio, str):
        return FAL_MOCK_ASPECT_RATIO_SIZES.get(aspect_ratio.strip(), FAL_MOCK_DEFAULT_SIZE)
    return FAL_MOCK_DEFAULT_SIZE


def get_mock_fal_image_result(model: str | None, form_data: Any) -> dict[str, Any]:
    width, height = _mock_image_size(form_data)
    requested_count = getattr(form_data, 'n', 1)
    count = requested_count if isinstance(requested_count, int) and requested_count > 0 else 1
    batch_seed = random.getrandbits(64)
    seeds = [f'{batch_seed}-{index}' for index in range(count)]

    return {
        'images': [
            {
                'url': f'{FAL_MOCK_IMAGE_BASE_URL}/seed/{seed}/{width}/{height}',
                'content_type': 'image/jpeg',
                'file_name': f'{seed}.jpg',
                'file_size': None,
            }
            for seed in seeds
        ],
        'timings': {
            'inference': 0.7322960860001331,
            'safety_checker': 0.014431928999329102,
        },
        'seed': seeds[0],
        'has_nsfw_concepts': [False] * count,
    }


def get_fal_generation_model(model: str | None) -> str:
    normalized_model = _normalize_model_id(model)
    if not normalized_model:
        return FAL_DEFAULT_IMAGE_MODEL

    internal_model = normalize_fal_image_model_id(normalized_model)
    if internal_model is not None:
        normalized_model = internal_model

    model_info = _get_fal_model_info(normalized_model)
    if model_info and model_info.get('task') == 'image-to-image':
        return model_info.get('generation_model') or FAL_DEFAULT_IMAGE_MODEL

    return normalized_model


def get_fal_edit_model(model: str | None) -> str:
    normalized_model = _normalize_model_id(model)
    if not normalized_model:
        return FAL_DEFAULT_IMAGE_EDIT_MODEL

    internal_model = normalize_fal_image_model_id(normalized_model)
    if internal_model is not None:
        normalized_model = internal_model

    model_info = _get_fal_model_info(normalized_model)
    if model_info and model_info.get('task') == 'image-to-image':
        return model_info['id']
    if model_info:
        return model_info.get('edit_model') or FAL_DEFAULT_IMAGE_EDIT_MODEL
    if normalized_model.endswith('/edit'):
        return normalized_model

    return f'{normalized_model}/edit'


def _set_known_model_size(data: dict[str, Any], form_data: Any, model_info: dict[str, Any]) -> None:
    _set_option(
        data,
        model_info.get('aspect_ratio_field'),
        getattr(form_data, 'aspect_ratio', None),
        model_info.get('aspect_ratios', []),
        model_info.get('default_aspect_ratio'),
    )
    image_size_whitelist = model_info.get('image_size_whitelist') or model_info.get('aspect_ratio_sizes')
    if model_info.get('custom_size_field'):
        # Custom-size models carry their allowed pixel buckets either as a dedicated
        # `image_size_whitelist` (preferred, kept out of the public catalog) or, for
        # legacy aspect-ratio-driven models, as `aspect_ratio_sizes`.
        _set_custom_image_size(
            data,
            model_info.get('custom_size_field'),
            form_data,
            image_size_whitelist,
            model_info.get('custom_size'),
            model_info.get('resolution_multipliers'),
        )
        return
    _set_option(
        data,
        model_info.get('resolution_field'),
        getattr(form_data, 'resolution', None) or getattr(form_data, 'size', None),
        model_info.get('resolutions', []),
        model_info.get('default_resolution'),
    )


def _build_known_model_payload(
    data: dict[str, Any],
    form_data: Any,
    model_info: dict[str, Any],
) -> dict[str, Any]:
    count_field = model_info.get('count_field', 'num_images')
    count = _safe_count(getattr(form_data, 'n', None), model_info.get('image_counts', []))
    if count_field and count:
        data[count_field] = count
    _set_known_model_size(data, form_data, model_info)
    _set_option(
        data,
        (model_info.get('output_format_field') or 'output_format')
        if model_info.get('output_formats')
        else None,
        getattr(form_data, 'output_format', None),
        model_info.get('output_formats', []),
        model_info.get('default_output_format'),
    )
    _set_option_fields(data, form_data, model_info.get('option_fields'))
    _set_boolean_fields(data, form_data, model_info.get('boolean_fields'))
    _set_integer_fields(data, form_data, model_info.get('integer_fields'))
    _set_number_fields(data, form_data, model_info.get('number_fields'))
    _set_text_fields(data, form_data, model_info.get('text_fields'))

    system_prompt = getattr(form_data, 'system_prompt', None)
    if model_info.get('supports_system_prompt') and system_prompt:
        data['system_prompt'] = system_prompt
    return data


def _build_unknown_model_payload(data: dict[str, Any], form_data: Any) -> dict[str, Any]:
    optional_fields = (
        ('num_images', getattr(form_data, 'n', None)),
        ('aspect_ratio', getattr(form_data, 'aspect_ratio', None)),
        ('resolution', getattr(form_data, 'resolution', None)),
        ('output_format', getattr(form_data, 'output_format', None) or 'png'),
        ('system_prompt', getattr(form_data, 'system_prompt', None)),
    )
    data.update({key: value for key, value in optional_fields if value})
    return data


def build_fal_image_payload(form_data: Any, model: str | None, image_urls: list[str] | None = None) -> dict[str, Any]:
    model_info = _get_fal_model_info(model)
    data = {}
    if model_info is None or model_info.get('supports_prompt', True) is not False:
        data['prompt'] = form_data.prompt
    if image_urls is not None:
        image_input_field = model_info.get('image_input_field', 'image_urls') if model_info else 'image_urls'
        max_count = model_info.get('image_input_max_count') if model_info else None
        _set_image_input(data, image_input_field, image_urls, max_count if isinstance(max_count, int) else None)
    if model_info:
        return _build_known_model_payload(data, form_data, model_info)
    if image_urls is not None:
        data['image_urls'] = image_urls
    return _build_unknown_model_payload(data, form_data)


def extract_fal_image_urls(result: Any) -> list[str]:
    if isinstance(result, dict) and isinstance(result.get('data'), dict):
        result = result['data']

    if isinstance(result, dict):
        candidates = []
        if isinstance(result.get('images'), list):
            candidates.extend(result['images'])
        if result.get('image'):
            candidates.append(result['image'])
        if result.get('url'):
            candidates.append(result)
    elif isinstance(result, list):
        candidates = result
    else:
        candidates = []

    urls = []
    for item in candidates:
        if isinstance(item, str):
            urls.append(item)
        elif isinstance(item, dict) and isinstance(item.get('url'), str):
            urls.append(item['url'])

    return urls
