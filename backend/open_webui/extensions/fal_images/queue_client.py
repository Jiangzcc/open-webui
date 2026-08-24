"""FAL queue transport with strict origin validation and recovery support."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING, Any

from open_webui.env import AIOHTTP_CLIENT_SESSION_SSL
from open_webui.extensions.fal_images.errors import FalImageError
from open_webui.extensions.url_security import normalize_https_base_url, require_same_https_origin
from open_webui.utils.session_pool import get_session

if TYPE_CHECKING:
    from open_webui.extensions.provider_ops.tracing import ProviderInvocationObserver

log = logging.getLogger(__name__)

FAL_QUEUE_BASE_URL = 'https://queue.fal.run'
FAL_REQUEST_TIMEOUT_SECONDS = 180
FAL_POLL_INTERVAL_SECONDS = 1


def _headers(api_key: str) -> dict[str, str]:
    if not api_key:
        raise FalImageError('FAL API key is not configured')
    return {'Authorization': f'Key {api_key}', 'Content-Type': 'application/json'}


def _endpoint(base_url: str, model: str) -> str:
    return f'{normalize_https_base_url(base_url)}/{model.lstrip("/")}'


def _queue_url(value: object, trusted_base_url: str, *, required: bool) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise FalImageError('fal.ai response contains an invalid queue URL')
    try:
        return require_same_https_origin(value, trusted_base_url)
    except ValueError as error:
        raise FalImageError('fal.ai response contains an invalid queue URL') from error


async def _response_error(response: Any) -> FalImageError:
    try:
        payload = await response.json(content_type=None)
    except Exception:
        payload = await response.text()
    provider_code = None
    if isinstance(payload, dict):
        raw_error = payload.get('error')
        candidate = raw_error.get('type') if isinstance(raw_error, dict) else payload.get('type')
        if isinstance(candidate, str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', candidate):
            provider_code = candidate
        detail = payload.get('detail') or payload.get('message') or payload.get('error') or payload
    else:
        detail = payload
    return FalImageError(
        f'fal.ai request failed: {detail}',
        status_code=response.status,
        code=provider_code,
    )


async def _notify_provider(observer: ProviderInvocationObserver | None, method: str, *args: object) -> None:
    if observer is None:
        return
    try:
        await getattr(observer, method)(*args)
    except Exception:
        # Diagnostics are best-effort and cannot invalidate paid generation.
        log.exception('Provider invocation observer failed during %s', method)


async def _cancel_fal_request(session: Any, cancel_url: str, headers: dict[str, str]) -> None:
    """Best-effort remote cancellation used only for local worker shutdown."""
    try:
        async with session.put(
            cancel_url,
            headers=headers,
            ssl=AIOHTTP_CLIENT_SESSION_SSL,
            allow_redirects=False,
        ) as response:
            if response.status >= 300:
                log.warning('FAL cancellation returned HTTP %s', response.status)
    except Exception:
        log.exception('Could not cancel the remote FAL request')


async def _poll_queue_status(
    session: Any,
    status_url: str | None,
    headers: dict[str, str],
    observer: ProviderInvocationObserver | None,
    timeout_seconds: float | None,
    *,
    completed_without_status: bool,
) -> bool:
    if status_url is None:
        return completed_without_status
    deadline = asyncio.get_running_loop().time() + (
        FAL_REQUEST_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    )
    while asyncio.get_running_loop().time() < deadline:
        async with session.get(
            status_url,
            headers=headers,
            ssl=AIOHTTP_CLIENT_SESSION_SSL,
            allow_redirects=False,
        ) as response:
            if response.status >= 300:
                raise await _response_error(response)
            status = await response.json(content_type=None)
        if isinstance(status, dict):
            await _notify_provider(observer, 'status', status)
        request_status = status.get('status') if isinstance(status, dict) else None
        if request_status == 'COMPLETED':
            return True
        if request_status in {'FAILED', 'CANCELLED'}:
            raise FalImageError(f'fal.ai request {request_status.lower()}: {status}')
        await asyncio.sleep(FAL_POLL_INTERVAL_SECONDS)
    raise FalImageError('fal.ai request timed out')


async def _fetch_queue_result(session: Any, response_url: str, headers: dict[str, str]) -> dict[str, Any]:
    async with session.get(
        response_url,
        headers=headers,
        ssl=AIOHTTP_CLIENT_SESSION_SSL,
        allow_redirects=False,
    ) as response:
        if response.status >= 300:
            raise await _response_error(response)
        return await response.json(content_type=None)


async def _record_provider_error(
    error: BaseException,
    observer: ProviderInvocationObserver | None,
    *,
    submitted: bool,
    completed: bool,
) -> None:
    setattr(error, 'provider_submitted', submitted)
    setattr(error, 'provider_completed', completed)
    await _notify_provider(observer, 'failed', error)


async def _submit_queue_request(
    session: Any,
    *,
    endpoint: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> object:
    async with session.post(
        endpoint,
        json=payload,
        headers=headers,
        ssl=AIOHTTP_CLIENT_SESSION_SSL,
        allow_redirects=False,
    ) as response:
        if response.status >= 300:
            raise await _response_error(response)
        return await response.json(content_type=None)


async def _wait_for_queue_result(
    session: Any,
    *,
    status_url: str | None,
    response_url: str | None,
    headers: dict[str, str],
    observer: ProviderInvocationObserver | None,
    timeout_seconds: float | None,
) -> dict[str, Any]:
    if not response_url:
        raise FalImageError('fal.ai response did not include a response_url')
    provider_completed = await _poll_queue_status(
        session,
        status_url,
        headers,
        observer,
        timeout_seconds,
        completed_without_status=False,
    )
    try:
        result = await _fetch_queue_result(session, response_url, headers)
    except BaseException as error:
        setattr(error, 'provider_completed', provider_completed)
        raise
    await _notify_provider(observer, 'succeeded')
    return result


async def _interpret_submission(
    submitted: object,
    trusted_base_url: str,
    observer: ProviderInvocationObserver | None,
) -> tuple[str | None, str | None, str | None, dict[str, Any] | None]:
    if not isinstance(submitted, dict):
        return None, None, None, None
    cancel_url = _queue_url(submitted.get('cancel_url'), trusted_base_url, required=False)
    status_url = _queue_url(submitted.get('status_url'), trusted_base_url, required=False)
    response_url = _queue_url(submitted.get('response_url'), trusted_base_url, required=False)
    await _notify_provider(observer, 'submitted', submitted)
    inline_result = submitted if {'images', 'image', 'video', 'url'} & submitted.keys() else None
    if inline_result is not None:
        await _notify_provider(observer, 'succeeded')
    return cancel_url, status_url, response_url, inline_result


async def run_fal_queue(
    model: str,
    payload: dict[str, Any],
    api_key: str,
    base_url: str,
    *,
    observer: ProviderInvocationObserver | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    headers = _headers(api_key)
    session: Any | None = None
    cancel_url: str | None = None
    provider_submitted = False
    provider_completed = False
    try:
        trusted_base_url = normalize_https_base_url(base_url or FAL_QUEUE_BASE_URL)
        session = await get_session()
        submitted = await _submit_queue_request(
            session,
            endpoint=_endpoint(trusted_base_url, model),
            payload=payload,
            headers=headers,
        )
        provider_submitted = isinstance(submitted, dict)
        cancel_url, status_url, response_url, inline_result = await _interpret_submission(
            submitted, trusted_base_url, observer
        )
        if inline_result is not None:
            provider_completed = True
            return inline_result
        result = await _wait_for_queue_result(
            session,
            status_url=status_url,
            response_url=response_url,
            headers=headers,
            observer=observer,
            timeout_seconds=timeout_seconds,
        )
        provider_completed = True
        return result
    except asyncio.CancelledError as error:
        if session is not None and cancel_url is not None and not provider_completed:
            await _cancel_fal_request(session, cancel_url, headers)
        completed = provider_completed or bool(getattr(error, 'provider_completed', False))
        await _record_provider_error(error, observer, submitted=provider_submitted, completed=completed)
        raise
    except Exception as error:
        completed = provider_completed or bool(getattr(error, 'provider_completed', False))
        await _record_provider_error(error, observer, submitted=provider_submitted, completed=completed)
        raise


async def resume_fal_queue(
    *,
    status_url: str | None,
    response_url: str,
    api_key: str,
    base_url: str = FAL_QUEUE_BASE_URL,
    observer: ProviderInvocationObserver | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Resume an accepted request without issuing another paid POST."""
    headers = _headers(api_key)
    provider_completed = False
    try:
        trusted_base_url = normalize_https_base_url(base_url)
        status_url = _queue_url(status_url, trusted_base_url, required=False)
        validated_response_url = _queue_url(response_url, trusted_base_url, required=True)
        assert validated_response_url is not None
        session = await get_session()
        provider_completed = await _poll_queue_status(
            session,
            status_url,
            headers,
            observer,
            timeout_seconds,
            completed_without_status=True,
        )
        result = await _fetch_queue_result(session, validated_response_url, headers)
        await _notify_provider(observer, 'succeeded')
        return result
    except asyncio.CancelledError as error:
        await _record_provider_error(error, observer, submitted=True, completed=provider_completed)
        raise
    except Exception as error:
        await _record_provider_error(error, observer, submitted=True, completed=provider_completed)
        raise


__all__ = ['FAL_QUEUE_BASE_URL', 'resume_fal_queue', 'run_fal_queue']
