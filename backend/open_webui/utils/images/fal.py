import asyncio
import logging
import random
import re
from copy import deepcopy
from typing import Any

from open_webui.env import AIOHTTP_CLIENT_SESSION_SSL
from open_webui.utils.images.fal_models import (
    FAL_DEFAULT_IMAGE_EDIT_MODEL,
    FAL_DEFAULT_IMAGE_MODEL,
    FAL_IMAGE_MODELS,
    normalize_fal_image_model_id,
)
from open_webui.utils.session_pool import get_session

log = logging.getLogger(__name__)

FAL_QUEUE_BASE_URL = 'https://queue.fal.run'
FAL_REQUEST_TIMEOUT_SECONDS = 180
FAL_POLL_INTERVAL_SECONDS = 1
FAL_MOCK_MODELS = {'fal-ai/z-image/turbo'}
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


class FalImageError(Exception):
    pass


def _headers(api_key: str) -> dict[str, str]:
    if not api_key:
        raise FalImageError('FAL API key is not configured')

    return {
        'Authorization': f'Key {api_key}',
        'Content-Type': 'application/json',
    }


def _endpoint(base_url: str, model: str) -> str:
    return f'{base_url.strip().rstrip("/")}/{model.lstrip("/")}'


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


def _safe_image_size(value: str | None, sizes: dict[str, str] | None) -> str | dict[str, int] | None:
    if not isinstance(value, str) or not sizes or value not in sizes.values():
        return None
    if value == 'auto':
        return value

    width_value, height_value = value.split('x', 1)
    return {'width': int(width_value), 'height': int(height_value)}


def _set_custom_image_size(
    data: dict[str, Any],
    field: str | None,
    form_data: Any,
    sizes: dict[str, str] | None,
) -> None:
    if not field:
        return

    requested_size = getattr(form_data, 'size', None) or getattr(form_data, 'resolution', None)
    if not requested_size:
        requested_size = (sizes or {}).get(getattr(form_data, 'aspect_ratio', None))

    image_size = _safe_image_size(requested_size, sizes)
    if image_size is not None:
        data[field] = image_size


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
    return deepcopy(FAL_IMAGE_MODELS)


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


def get_mock_fal_image_result(model: str | None, form_data: Any) -> dict[str, Any] | None:
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
        count_field = model_info.get('count_field', 'num_images')
        count = _safe_count(getattr(form_data, 'n', None), model_info.get('image_counts', []))
        if count_field and count:
            data[count_field] = count

        _set_option(
            data,
            model_info.get('aspect_ratio_field'),
            getattr(form_data, 'aspect_ratio', None),
            model_info.get('aspect_ratios', []),
            model_info.get('default_aspect_ratio'),
        )
        # Custom-size models carry their allowed pixel buckets either as a dedicated
        # `image_size_whitelist` (preferred, kept out of the public catalog) or, for
        # legacy aspect-ratio-driven models, as `aspect_ratio_sizes`.
        image_size_whitelist = model_info.get('image_size_whitelist') or model_info.get('aspect_ratio_sizes')
        if model_info.get('custom_size_field'):
            _set_custom_image_size(
                data,
                model_info.get('custom_size_field'),
                form_data,
                image_size_whitelist,
            )
        else:
            _set_option(
                data,
                model_info.get('resolution_field'),
                getattr(form_data, 'resolution', None) or getattr(form_data, 'size', None),
                model_info.get('resolutions', []),
                model_info.get('default_resolution'),
            )
        _set_option(
            data,
            'output_format' if model_info.get('output_formats') else None,
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

    if image_urls is not None:
        data['image_urls'] = image_urls

    if getattr(form_data, 'n', None):
        data['num_images'] = form_data.n

    aspect_ratio = getattr(form_data, 'aspect_ratio', None)
    if aspect_ratio:
        data['aspect_ratio'] = aspect_ratio

    resolution = getattr(form_data, 'resolution', None)
    if resolution:
        data['resolution'] = resolution

    output_format = getattr(form_data, 'output_format', None) or 'png'
    if output_format:
        data['output_format'] = output_format

    system_prompt = getattr(form_data, 'system_prompt', None)
    if system_prompt:
        data['system_prompt'] = system_prompt

    return data


async def _response_error(response) -> FalImageError:
    try:
        payload = await response.json(content_type=None)
    except Exception:
        payload = await response.text()

    if isinstance(payload, dict):
        detail = payload.get('detail') or payload.get('message') or payload.get('error') or payload
    else:
        detail = payload

    return FalImageError(f'fal.ai request failed: {detail}')


async def run_fal_queue(model: str, payload: dict[str, Any], api_key: str, base_url: str) -> dict[str, Any]:
    headers = _headers(api_key)
    session = await get_session()

    async with session.post(
        _endpoint(base_url or FAL_QUEUE_BASE_URL, model),
        json=payload,
        headers=headers,
        ssl=AIOHTTP_CLIENT_SESSION_SSL,
    ) as response:
        if response.status >= 400:
            raise await _response_error(response)
        submitted = await response.json(content_type=None)

    if isinstance(submitted, dict) and ('images' in submitted or 'image' in submitted or 'url' in submitted):
        return submitted

    status_url = submitted.get('status_url') if isinstance(submitted, dict) else None
    response_url = submitted.get('response_url') if isinstance(submitted, dict) else None

    if not response_url:
        raise FalImageError('fal.ai response did not include a response_url')

    deadline = asyncio.get_running_loop().time() + FAL_REQUEST_TIMEOUT_SECONDS

    while status_url and asyncio.get_running_loop().time() < deadline:
        async with session.get(status_url, headers=headers, ssl=AIOHTTP_CLIENT_SESSION_SSL) as response:
            if response.status >= 400:
                raise await _response_error(response)
            status = await response.json(content_type=None)

        request_status = status.get('status') if isinstance(status, dict) else None
        if request_status == 'COMPLETED':
            break
        if request_status in {'FAILED', 'CANCELLED'}:
            raise FalImageError(f'fal.ai request {request_status.lower()}: {status}')

        await asyncio.sleep(FAL_POLL_INTERVAL_SECONDS)
    else:
        if status_url:
            raise FalImageError('fal.ai request timed out')

    async with session.get(response_url, headers=headers, ssl=AIOHTTP_CLIENT_SESSION_SSL) as response:
        if response.status >= 400:
            raise await _response_error(response)
        return await response.json(content_type=None)


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
