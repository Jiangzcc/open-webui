import asyncio
import logging
import random
from copy import deepcopy
from typing import Any

from open_webui.env import AIOHTTP_CLIENT_SESSION_SSL
from open_webui.utils.images.fal_models import (
    FAL_DEFAULT_IMAGE_EDIT_MODEL,
    FAL_DEFAULT_IMAGE_MODEL,
    FAL_IMAGE_MODELS,
)
from open_webui.utils.session_pool import get_session

log = logging.getLogger(__name__)

FAL_QUEUE_BASE_URL = 'https://queue.fal.run'
FAL_REQUEST_TIMEOUT_SECONDS = 180
FAL_POLL_INTERVAL_SECONDS = 1
FAL_MOCK_MODELS = {'fal-ai/z-image/turbo'}
FAL_MOCK_IMAGE_URLS = [
    'http://localhost:8080/api/v1/files/2f41a8f7-a7e9-4b91-8978-b1782b94558e/content',
    'http://localhost:8080/api/v1/files/2618b65c-0ab5-40fb-bafb-00287e4ef21e/content',
    'http://localhost:8080/api/v1/files/320b1eee-9bfc-42ac-9279-be088967e27b/content',
]
FAL_MOCK_IMAGE_COUNT_RANGE = (1, 3)


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


def get_mock_fal_image_result(model: str | None) -> dict[str, Any] | None:
    normalized_model = _normalize_model_id(model)
    if normalized_model not in FAL_MOCK_MODELS:
        return None

    count = random.randint(*FAL_MOCK_IMAGE_COUNT_RANGE)
    urls = random.sample(FAL_MOCK_IMAGE_URLS, k=count)

    return {
        'images': [
            {
                'url': url,
                'content_type': 'image/png',
                'file_name': url.rsplit('/', 2)[-2] + '.png',
                'file_size': None,
            }
            for url in urls
        ],
        'timings': {
            'inference': 0.7322960860001331,
            'safety_checker': 0.014431928999329102,
        },
        'seed': random.randint(0, 2**31 - 1),
        'has_nsfw_concepts': [False] * count,
    }


def get_fal_generation_model(model: str | None) -> str:
    normalized_model = _normalize_model_id(model)
    if not normalized_model:
        return FAL_DEFAULT_IMAGE_MODEL

    model_info = _get_fal_model_info(normalized_model)
    if model_info and model_info.get('task') == 'image-to-image':
        return model_info.get('generation_model') or FAL_DEFAULT_IMAGE_MODEL

    return normalized_model


def get_fal_edit_model(model: str | None) -> str:
    normalized_model = _normalize_model_id(model)
    if not normalized_model:
        return FAL_DEFAULT_IMAGE_EDIT_MODEL

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
    data = {
        'prompt': form_data.prompt,
    }

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
        if model_info.get('custom_size_field'):
            _set_custom_image_size(
                data,
                model_info.get('custom_size_field'),
                form_data,
                model_info.get('aspect_ratio_sizes'),
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
