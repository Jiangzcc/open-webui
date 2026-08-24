from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import json
import mimetypes
import os
import re
from collections.abc import Mapping
from dataclasses import replace
from math import isfinite
from types import MappingProxyType
from typing import Literal

from open_webui.retrieval.web.utils import get_ssrf_safe_session, validate_url

from . import compat
from .compat import CompatImageInput, ImageBillingContext, PreparedImageCall
from .constants import (
    ALLOWED_REFERENCE_IMAGE_MIME_TYPES,
    MAX_CANONICAL_DEPTH,
    MAX_CANONICAL_NODES,
    MAX_CANONICAL_STRING_BYTES,
    MAX_CANONICAL_TOTAL_BYTES,
    MAX_CREDIT_VALUE,
    MAX_IMAGE_COUNT,
    MAX_IMAGE_DIMENSION_LENGTH,
    MAX_IMAGE_MODEL_LENGTH,
    MAX_IMAGE_PROMPT_BYTES,
    MAX_IMAGE_REFERENCES,
    MAX_REFERENCE_IMAGE_BYTES,
    MAX_REFERENCE_TOTAL_BYTES,
    REFERENCE_READ_TIMEOUT_SECONDS,
)
from .errors import CreditError

CancelledError = asyncio.CancelledError

_DATA_URL_PATTERN = re.compile(r'^data:([^;,]+);base64,(.*)$', re.DOTALL)
_FILE_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,128}$')
_FILE_ROUTE_PATTERN = re.compile(r'^/api/v1/files/([A-Za-z0-9_-]{1,128})/content$')
_PIXEL_SIZE_PATTERN = re.compile(r'^([1-9][0-9]{0,5})x([1-9][0-9]{0,5})$')
_READ_CHUNK_SIZE = 64 * 1024
get_file_content_by_id = None  # lazily bound; tests replace this module-level seam

# Image magic byte signatures for content validation
_PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
_JPEG_SIGNATURE = b'\xff\xd8\xff'
_WEBP_SIGNATURE_PREFIX = b'RIFF'
_WEBP_SIGNATURE_SUFFIX = b'WEBP'


def _error(
    code: Literal['price_rule_incomplete', 'credit_service_unavailable'], reason: str, **context: object
) -> CreditError:
    safe_context = {'reason': reason, **context}
    return CreditError(code=code, context=safe_context)


def _bounded_string(value: object, *, name: str, limit: int, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise _error('price_rule_incomplete', f'invalid_{name}')
    normalized = value.strip()
    if (required and not normalized) or len(normalized.encode('utf-8')) > limit:
        raise _error('price_rule_incomplete', f'invalid_{name}')
    return normalized


def _normalize_input(image_input: object) -> CompatImageInput:
    if not isinstance(image_input, CompatImageInput):
        raise _error('credit_service_unavailable', 'invalid_image_input')
    prompt = _bounded_string(image_input.prompt, name='prompt', limit=MAX_IMAGE_PROMPT_BYTES, required=True)
    model = _bounded_string(image_input.model, name='model', limit=MAX_IMAGE_MODEL_LENGTH)
    size = _bounded_string(image_input.size, name='size', limit=MAX_IMAGE_DIMENSION_LENGTH)
    resolution = _bounded_string(image_input.resolution, name='resolution', limit=MAX_IMAGE_DIMENSION_LENGTH)
    aspect_ratio = _bounded_string(image_input.aspect_ratio, name='aspect_ratio', limit=MAX_IMAGE_DIMENSION_LENGTH)
    quality = _bounded_string(image_input.quality, name='quality', limit=MAX_IMAGE_DIMENSION_LENGTH)
    if isinstance(image_input.image_count, bool) or not isinstance(image_input.image_count, int):
        raise _error('price_rule_incomplete', 'invalid_image_count')
    if not 1 <= image_input.image_count <= MAX_IMAGE_COUNT:
        raise _error('price_rule_incomplete', 'invalid_image_count')
    _canonical_json(image_input.extra, reason='invalid_extra')
    return CompatImageInput(
        model=model,
        prompt=prompt,
        image=image_input.image,
        size=size,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        quality=quality,
        image_count=image_input.image_count,
        extra=image_input.extra,
    )


def _track_canonical_bytes(value: str, byte_total: list[int], budget: int) -> None:
    byte_total[0] += len(value.encode('utf-8'))
    if byte_total[0] > budget:
        raise ValueError('canonical total bytes exceed budget')


def _canonical_mapping(
    value: Mapping,
    *,
    depth: int,
    counter: list[int],
    byte_total: list[int],
    budget: int,
) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError('canonical mapping keys must be strings')
        _track_canonical_bytes(key, byte_total, budget)
        normalized[key] = _canonical_value(
            item,
            depth=depth + 1,
            counter=counter,
            byte_total=byte_total,
            budget=budget,
        )
    return normalized


def _canonical_number(value: int | float) -> int | float:
    if isinstance(value, int):
        if abs(value) > MAX_CREDIT_VALUE:
            raise ValueError('canonical integer exceeds credit ceiling')
        return value
    if not isfinite(value):
        raise ValueError('non-finite number')
    return value


def _canonical_value(
    value: object,
    *,
    depth: int,
    counter: list[int],
    byte_total: list[int],
    budget: int,
) -> object:
    counter[0] += 1
    if counter[0] > MAX_CANONICAL_NODES or depth > MAX_CANONICAL_DEPTH:
        raise ValueError('canonical structure exceeds limits')
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        # 有限浮点参数（如 guidance_scale=3.5）合法：与视频侧 request_hash 的
        # json.dumps 行为一致，直接进入 canonical JSON（repr 确定性序列化）。
        # NaN/Inf 无稳定表示，仍拒绝。
        return _canonical_number(value)
    if isinstance(value, str):
        if len(value.encode('utf-8')) > MAX_CANONICAL_STRING_BYTES:
            raise ValueError('canonical string exceeds limit')
        _track_canonical_bytes(value, byte_total, budget)
        return value
    if isinstance(value, Mapping):
        return _canonical_mapping(
            value,
            depth=depth,
            counter=counter,
            byte_total=byte_total,
            budget=budget,
        )
    if isinstance(value, (list, tuple)):
        return [
            _canonical_value(item, depth=depth + 1, counter=counter, byte_total=byte_total, budget=budget)
            for item in value
        ]
    raise ValueError('unsupported canonical value')


# Module-level mutable reference so tests can monkeypatch the budget
_MAX_CANONICAL_TOTAL_BYTES_REF = MAX_CANONICAL_TOTAL_BYTES


def _canonical_json(value: object, *, reason: str, budget_override: int | None = None) -> bytes:
    budget = budget_override if budget_override is not None else _MAX_CANONICAL_TOTAL_BYTES_REF
    try:
        normalized = _canonical_value(value, depth=0, counter=[0], byte_total=[0], budget=budget)
        return json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(',', ':'),
            allow_nan=False,
        ).encode('utf-8')
    except (TypeError, ValueError, UnicodeError):
        raise _error('price_rule_incomplete', reason) from None


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _trusted_channel(metadata: object) -> Literal['chat', 'tool'] | None:
    if metadata is not None and not isinstance(metadata, Mapping):
        raise _error('credit_service_unavailable', 'invalid_credit_channel')
    trusted = metadata.get('credit_channel') if metadata else None
    if trusted is None:
        return None
    if trusted not in ('chat', 'tool'):
        raise _error('credit_service_unavailable', 'invalid_credit_channel')
    return trusted


def _headers_use_api_key(headers: Mapping) -> bool:
    authorization = headers.get('authorization', '')
    # Bearer scheme is case-insensitive per RFC 6750; credentials starting
    # with "sk-" indicate a service API key, not a JWT web session.
    if isinstance(authorization, str):
        stripped = authorization.strip()
        # Match "Bearer" case-insensitively at the start
        if stripped.lower().startswith('bearer '):
            credentials = stripped[len('bearer ') :]
            if credentials.startswith('sk-'):
                return True
    # x-api-key must be present and non-blank to count as API
    api_key = headers.get('x-api-key')
    return isinstance(api_key, str) and bool(api_key.strip())


def _request_credentials_use_api_key(request: object) -> bool:
    # Cookie token starting with "sk-" also indicates API
    cookies = getattr(request, 'cookies', {})
    if isinstance(cookies, Mapping):
        cookie_token = cookies.get('token', '')
        if isinstance(cookie_token, str) and cookie_token.startswith('sk-'):
            return True
    # request.state.token.credentials starting with "sk-"
    state = getattr(request, 'state', None)
    if state is not None:
        state_token = getattr(state, 'token', None)
        if state_token is not None:
            credentials = getattr(state_token, 'credentials', None)
            if isinstance(credentials, str) and credentials.startswith('sk-'):
                return True
    return False


def _request_uses_api_key(request: object) -> bool:
    headers = getattr(request, 'headers', {})
    if not isinstance(headers, Mapping):
        raise _error('credit_service_unavailable', 'invalid_credit_channel')
    return _headers_use_api_key(headers) or _request_credentials_use_api_key(request)


def _channel(request: object, metadata: object) -> Literal['web', 'api', 'chat', 'tool']:
    trusted = _trusted_channel(metadata)
    if trusted is not None:
        return trusted
    return 'api' if _request_uses_api_key(request) else 'web'


def _pixel_count(value: str | None) -> int | None:
    if value is None:
        return None
    match = _PIXEL_SIZE_PATTERN.fullmatch(value)
    if match is None:
        return None
    pixels = int(match.group(1)) * int(match.group(2))
    return pixels if pixels <= MAX_CREDIT_VALUE else None


def _ratio_pixel_count(model: str | None, aspect_ratio: str | None, resolution: str | None) -> int | None:
    """Resolve pixel count from the catalog's aspect-ratio baseline mapping.

    比例驱动的模型（用户只提交 aspect_ratio）没有 WxH 字符串可解析；从目录的
    aspect_ratio_sizes 基线按分辨率档乘数（如 2K → ×2）放大后计算像素，
    与 build_fal_image_payload 的组合规则同源。
    """
    if not model or not aspect_ratio:
        return None
    from open_webui.extensions.fal_images.models import (  # 延迟导入避免环
        FAL_IMAGE_MODELS,
        normalize_fal_image_model_id,
    )

    internal = normalize_fal_image_model_id(model) or model
    info = next((m for m in FAL_IMAGE_MODELS if m.get('id') == internal), None)
    if not info:
        return None
    baseline = (info.get('aspect_ratio_sizes') or {}).get(aspect_ratio)
    if not baseline:
        return None
    multiplier = (info.get('resolution_multipliers') or {}).get(resolution or '', 1)
    if not isinstance(multiplier, int) or multiplier < 1:
        multiplier = 1
    match = _PIXEL_SIZE_PATTERN.fullmatch(baseline)
    if match is None:
        return None
    pixels = int(match.group(1)) * multiplier * int(match.group(2)) * multiplier
    return pixels if pixels <= MAX_CREDIT_VALUE else None


def _dimensions(
    config: object,
    image_input: CompatImageInput,
    action: str,
    model: str | None = None,
) -> Mapping[str, str | int]:
    requested_non_size_dimension = bool(image_input.resolution or image_input.aspect_ratio)
    if action == 'text-to-image':
        configured_size = getattr(config, 'IMAGE_SIZE', None)
        size = (
            image_input.size
            or (
                'default'
                if requested_non_size_dimension
                else _bounded_string(configured_size, name='size', limit=MAX_IMAGE_DIMENSION_LENGTH)
            )
            or '512x512'
        )
    else:
        configured_size = getattr(config, 'IMAGE_EDIT_SIZE', None)
        size = (
            image_input.size
            or (
                'default'
                if requested_non_size_dimension
                else _bounded_string(configured_size, name='size', limit=MAX_IMAGE_DIMENSION_LENGTH)
            )
            or 'default'
        )
    dimensions: dict[str, str | int] = {
        'size': size,
        'resolution': image_input.resolution or 'default',
        'aspect_ratio': image_input.aspect_ratio or 'default',
        'quality': image_input.quality or 'default',
        'image_count': image_input.image_count,
    }
    # Same precedence as payload construction (复盘 P0-2 单一事实源): a
    # "WxH"-shaped resolution wins, then an explicit size; a resolution tier
    # ("2K"/"4K") is not a pixel string and falls through to the ratio mapping.
    # Never trust a client-supplied pixel_count from `extra`.
    pixels = _pixel_count(image_input.resolution) or _pixel_count(size)
    if pixels is None:
        # 比例驱动模型：无 WxH 字符串，按目录映射（基线 × 分辨率档乘数）计像素。
        pixels = _ratio_pixel_count(model, image_input.aspect_ratio, image_input.resolution)
    if pixels is not None:
        dimensions['pixel_count'] = pixels
    return MappingProxyType(dimensions)


def _validate_magic_bytes(payload: bytes, mime: str) -> None:
    """Verify that decoded bytes match the magic signature of the declared MIME type."""
    if not payload:
        raise _error('price_rule_incomplete', 'invalid_reference_image')
    if mime == 'image/png' and not payload.startswith(_PNG_SIGNATURE):
        raise _error('price_rule_incomplete', 'invalid_reference_image')
    if mime == 'image/jpeg' and not payload.startswith(_JPEG_SIGNATURE):
        raise _error('price_rule_incomplete', 'invalid_reference_image')
    invalid_webp = payload[:4] != _WEBP_SIGNATURE_PREFIX or payload[8:12] != _WEBP_SIGNATURE_SUFFIX
    if mime == 'image/webp' and invalid_webp:
        raise _error('price_rule_incomplete', 'invalid_reference_image')


def _decode_data_url(reference: str) -> tuple[bytes, str]:
    match = _DATA_URL_PATTERN.fullmatch(reference)
    if not match:
        raise _error('price_rule_incomplete', 'invalid_reference_image')
    mime = match.group(1).lower()
    encoded = match.group(2)
    if mime not in ALLOWED_REFERENCE_IMAGE_MIME_TYPES or len(encoded) > ((MAX_REFERENCE_IMAGE_BYTES + 2) // 3) * 4:
        reason = (
            'reference_too_large'
            if len(encoded) > ((MAX_REFERENCE_IMAGE_BYTES + 2) // 3) * 4
            else 'invalid_reference_image'
        )
        raise _error('price_rule_incomplete', reason)
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise _error('price_rule_incomplete', 'invalid_reference_image') from None
    if len(payload) > MAX_REFERENCE_IMAGE_BYTES:
        raise _error('price_rule_incomplete', 'reference_too_large')
    _validate_magic_bytes(payload, mime)
    return payload, mime


def _validated_mime(value: object, fallback_path: str | None = None) -> str:
    mime = value.split(';', 1)[0].strip().lower() if isinstance(value, str) else ''
    if not mime and fallback_path:
        mime = (mimetypes.guess_type(fallback_path)[0] or '').lower()
    if mime not in ALLOWED_REFERENCE_IMAGE_MIME_TYPES:
        raise _error('price_rule_incomplete', 'invalid_reference_image')
    return mime


def _validate_declared_reference_size(value: object) -> None:
    if value is None:
        return
    try:
        declared_size = int(value)
    except (TypeError, ValueError):
        raise _error('price_rule_incomplete', 'invalid_reference_image') from None
    if declared_size < 0:
        raise _error('price_rule_incomplete', 'invalid_reference_image')
    if declared_size > MAX_REFERENCE_IMAGE_BYTES:
        raise _error('price_rule_incomplete', 'reference_too_large')


async def _read_reference_response(response: object) -> tuple[bytes, str]:
    response.raise_for_status()
    mime = _validated_mime(response.headers.get('Content-Type'))
    _validate_declared_reference_size(response.headers.get('Content-Length'))
    chunks: list[bytes] = []
    total = 0
    async for chunk in response.content.iter_chunked(_READ_CHUNK_SIZE):
        total += len(chunk)
        if total > MAX_REFERENCE_IMAGE_BYTES:
            raise _error('price_rule_incomplete', 'reference_too_large')
        chunks.append(chunk)
    payload = b''.join(chunks)
    _validate_magic_bytes(payload, mime)
    return payload, mime


async def _read_url_reference(reference: str) -> tuple[bytes, str]:
    try:
        await asyncio.to_thread(validate_url, reference)
    except Exception:
        raise _error('price_rule_incomplete', 'invalid_reference_image') from None
    try:
        async with asyncio.timeout(REFERENCE_READ_TIMEOUT_SECONDS):
            return await _fetch_url_reference(reference)
    except CancelledError:
        raise
    except CreditError:
        raise
    except TimeoutError:
        raise _error('price_rule_incomplete', 'reference_fetch_failed') from None
    except Exception:
        raise _error('price_rule_incomplete', 'reference_fetch_failed') from None


async def _fetch_url_reference(reference: str) -> tuple[bytes, str]:
    async with get_ssrf_safe_session() as session:
        async with session.get(reference, allow_redirects=False) as response:
            return await _read_reference_response(response)


def _extract_file_id(reference: str) -> str:
    route_match = _FILE_ROUTE_PATTERN.fullmatch(reference)
    if route_match:
        return route_match.group(1)
    # Standalone file IDs: 1–128 ASCII letters/digits/underscores/hyphens only
    if not reference:
        raise _error('price_rule_incomplete', 'invalid_reference_image')
    if '/' in reference or '\\' in reference or reference in ('.', '..'):
        raise _error('price_rule_incomplete', 'invalid_reference_image')
    if not _FILE_ID_PATTERN.fullmatch(reference):
        raise _error('price_rule_incomplete', 'invalid_reference_image')
    return reference


def _read_file_bounded(path: str) -> bytes:
    with open(path, 'rb') as handle:
        payload = handle.read(MAX_REFERENCE_IMAGE_BYTES + 1)
    if len(payload) > MAX_REFERENCE_IMAGE_BYTES:
        raise _error('price_rule_incomplete', 'reference_too_large')
    return payload


async def _read_file_reference(reference: str, user: object) -> tuple[bytes, str]:
    global get_file_content_by_id
    file_id = _extract_file_id(reference)
    try:
        from starlette.responses import FileResponse

        if get_file_content_by_id is None:
            from open_webui.routers.files import get_file_content_by_id as upstream_get_file_content

            get_file_content_by_id = upstream_get_file_content
        response = await get_file_content_by_id(file_id, user)
        if not isinstance(response, FileResponse):
            raise _error('price_rule_incomplete', 'reference_fetch_failed')
        path = str(response.path)
        size = await asyncio.to_thread(os.path.getsize, path)
        if size > MAX_REFERENCE_IMAGE_BYTES:
            raise _error('price_rule_incomplete', 'reference_too_large')
        mime = _validated_mime(response.media_type, path)
        payload = await asyncio.to_thread(_read_file_bounded, path)
        _validate_magic_bytes(payload, mime)
        return payload, mime
    except CreditError:
        raise
    except Exception:
        raise _error('price_rule_incomplete', 'reference_fetch_failed') from None


async def _read_reference(reference: object, user: object) -> tuple[bytes, str]:
    if not isinstance(reference, str) or not reference:
        raise _error('price_rule_incomplete', 'invalid_reference_image')
    if reference.startswith('data:'):
        return _decode_data_url(reference)
    if reference.startswith(('http://', 'https://')):
        return await _read_url_reference(reference)
    return await _read_file_reference(reference, user)


def _normalized_data_url(payload: bytes, mime: str) -> str:
    return f'data:{mime};base64,{base64.b64encode(payload).decode("ascii")}'


async def _references(image: object, user: object) -> tuple[tuple[str, ...], tuple[str, ...]]:
    references = image if isinstance(image, tuple) else (image,) if isinstance(image, str) else ()
    if not 1 <= len(references) <= MAX_IMAGE_REFERENCES:
        raise _error('price_rule_incomplete', 'invalid_reference_count')
    try:
        async with asyncio.timeout(REFERENCE_READ_TIMEOUT_SECONDS):
            return await _read_references(references, user)
    except CreditError:
        raise
    except TimeoutError:
        raise _error('price_rule_incomplete', 'reference_fetch_failed') from None


async def _read_references(references: tuple[object, ...], user: object) -> tuple[tuple[str, ...], tuple[str, ...]]:
    normalized: list[str] = []
    hashes: list[str] = []
    total = 0
    for reference in references:
        payload, mime = await _read_reference(reference, user)
        total += len(payload)
        if total > MAX_REFERENCE_TOTAL_BYTES:
            raise _error('price_rule_incomplete', 'reference_too_large')
        normalized.append(_normalized_data_url(payload, mime))
        hashes.append(_sha256(payload))
    return tuple(normalized), tuple(hashes)


async def _provider_input(
    normalized: CompatImageInput,
    *,
    transport_model: str,
    dimensions: Mapping[str, str | int],
    user: object,
    action: Literal['text-to-image', 'image-to-image'],
) -> tuple[CompatImageInput, tuple[str, ...]]:
    size = dimensions.get('size') if dimensions.get('size') != 'default' else normalized.size
    image_count = dimensions.get('image_count', normalized.image_count)
    if action == 'text-to-image':
        if normalized.image is not None:
            raise _error('price_rule_incomplete', 'unexpected_reference_image')
        return replace(normalized, model=transport_model, size=size, image_count=image_count), ()
    normalized_images, reference_hashes = await _references(normalized.image, user)
    provider_image: str | tuple[str, ...] = (
        normalized_images[0] if isinstance(normalized.image, str) else normalized_images
    )
    return (
        replace(
            normalized,
            model=transport_model,
            image=provider_image,
            size=size,
            image_count=image_count,
        ),
        reference_hashes,
    )


def _prepared_billing_context(
    *,
    resource_id: str,
    action: str,
    channel: str,
    dimensions: Mapping[str, str | int],
    prompt_hash: str,
    reference_hashes: tuple[str, ...],
    extra: Mapping[str, object],
) -> ImageBillingContext:
    snapshot = {
        'schema_version': 1,
        'service_type': 'image',
        'resource_id': resource_id,
        'action': action,
        'channel': channel,
        'dimensions': dimensions,
        'prompt_hash': prompt_hash,
        'reference_hashes': reference_hashes,
        'extra_hash': _sha256(_canonical_json(extra, reason='invalid_extra')),
    }
    return ImageBillingContext(
        service_type='image',
        resource_id=resource_id,
        action=action,
        channel=channel,
        dimensions=dimensions,
        prompt_hash=prompt_hash,
        reference_hashes=reference_hashes,
        request_hash=_sha256(_canonical_json(snapshot, reason='invalid_request')),
    )


async def _prepare(
    request: object,
    image_input: object,
    metadata: object,
    user: object,
    action: Literal['text-to-image', 'image-to-image'],
) -> PreparedImageCall:
    normalized = _normalize_input(image_input)
    compat.map_billing_identity(user)
    channel = _channel(request, metadata)
    config = await compat.get_runtime_image_config()
    dynamic_model = await compat.resolve_dynamic_engine_model(request, config, normalized)
    resolution = compat.resolve_provider_model(config, normalized, action, dynamic_model=dynamic_model)
    resource_id = _bounded_string(resolution.resource_id, name='resource_id', limit=128, required=True)
    dimensions = _dimensions(config, normalized, action, model=normalized.model)
    prompt_hash = _sha256(normalized.prompt.encode('utf-8'))

    # A1111 的 model 不是每请求选择：provider 收到用户原始请求（通常为 None），
    # 避免 billing 层预填的解析值触发 set_image_model 静默切换实例级 checkpoint。
    transport_model = normalized.model if resolution.engine == 'automatic1111' else resolution.transport_model

    provider_input, reference_hashes = await _provider_input(
        normalized,
        transport_model=transport_model,
        dimensions=dimensions,
        user=user,
        action=action,
    )
    billing = _prepared_billing_context(
        resource_id=resource_id,
        action=action,
        channel=channel,
        dimensions=dimensions,
        prompt_hash=prompt_hash,
        reference_hashes=reference_hashes,
        extra=normalized.extra,
    )
    return PreparedImageCall(billing=billing, provider_input=provider_input)


async def prepare_generation_call(request, image_input, metadata, user) -> PreparedImageCall:
    return await _prepare(request, image_input, metadata, user, 'text-to-image')


async def prepare_edit_call(request, image_input, metadata, user) -> PreparedImageCall:
    return await _prepare(request, image_input, metadata, user, 'image-to-image')


__all__ = ['prepare_edit_call', 'prepare_generation_call']
