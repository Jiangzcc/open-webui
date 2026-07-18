from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from contextlib import asynccontextmanager
from hashlib import sha256
from typing import Literal
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import HTTPException
from open_webui.constants import ERROR_MESSAGES
from open_webui.extensions.credits import compat
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.schemas import UserSnapshot
from open_webui.models.users import User
from open_webui.utils.access_control import has_permission
from sqlalchemy import select

Action = Literal['text-to-image', 'image-to-image']
_INTERNAL_IMAGE_URL = re.compile(r'^/api/v1/files/[A-Za-z0-9_-]{1,128}/content$')


@asynccontextmanager
async def credit_session() -> AsyncIterator[object]:
    from open_webui.extensions.credits.db import credit_session as open_credit_session

    async with open_credit_session() as session:
        yield session


async def begin_image_usage(session: object, user: UserSnapshot, context: object, idempotency_key: str) -> object:
    from open_webui.extensions.credits.service import begin_image_usage as begin

    return await begin(session, user, context, idempotency_key)


async def mark_usage_invoking(usage_id: str) -> int:
    from open_webui.extensions.credits.service import mark_usage_invoking as mark

    return await mark(usage_id)


async def mark_usage_succeeded(usage_id: str, urls: Sequence[str]) -> int:
    from open_webui.extensions.credits.service import mark_usage_succeeded as mark

    return await mark(usage_id, urls)


async def mark_usage_failed(usage_id: str, error: object) -> int:
    from open_webui.extensions.credits.service import mark_usage_failed as mark

    return await mark(usage_id, error)


def _unavailable(usage_id: str | None = None, *, reason: str | None = None) -> CreditError:
    context: dict[str, object] = {}
    if usage_id is not None:
        context['usage_id'] = usage_id
    if reason is not None:
        context['reason'] = reason
    return CreditError(code='credit_service_unavailable', context=context)


def _header_idempotency_key(request: object) -> str | None:
    headers = getattr(request, 'headers', {})
    if not isinstance(headers, Mapping):
        raise _unavailable(reason='invalid_request_headers')
    for name, value in headers.items():
        if isinstance(name, str) and name.lower() == 'idempotency-key':
            if not isinstance(value, str) or not value:
                raise CreditError(code='invalid_adjustment', context={'reason': 'invalid_idempotency_key'})
            return value
    return None


def _metadata_idempotency_key(identity: compat.BillingIdentity, action: Action, metadata: object) -> str | None:
    if metadata is None:
        return None
    if not isinstance(metadata, Mapping):
        raise _unavailable(reason='invalid_credit_metadata')

    call_instance_id = metadata.get('call_instance_id')
    if call_instance_id is None:
        return None
    channel = metadata.get('credit_channel')
    chat_id = metadata.get('chat_id')
    message_id = metadata.get('message_id')
    if (
        channel not in ('chat', 'tool')
        or not isinstance(call_instance_id, str)
        or not call_instance_id
        or (chat_id is not None and not isinstance(chat_id, str))
        or (message_id is not None and not isinstance(message_id, str))
    ):
        raise _unavailable(reason='invalid_credit_metadata')

    fields = (
        identity.user_id,
        action,
        channel,
        chat_id or '',
        message_id or '',
        call_instance_id,
    )
    material = '\x1f'.join(fields).encode('utf-8')
    return f'image:{sha256(material).hexdigest()}'


def _idempotency_key(request: object, metadata: object, identity: compat.BillingIdentity, action: Action) -> str:
    return _header_idempotency_key(request) or _metadata_idempotency_key(identity, action, metadata) or str(uuid4())


def _validate_internal_url(value: object) -> str:
    if not isinstance(value, str) or _INTERNAL_IMAGE_URL.fullmatch(value) is None:
        raise _unavailable(reason='invalid_usage_result')
    return value


def _normalize_internal_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme in ('http', 'https') and parsed.hostname in ('localhost', '127.0.0.1', '::1'):
        return parsed.path
    return value


def _result_urls(result: object) -> list[str]:
    if not isinstance(result, Sequence) or isinstance(result, (str, bytes)) or not result:
        raise CreditError(code='provider_failed', context={'reason': 'invalid_provider_result'})
    urls: list[str] = []
    for item in result:
        if not isinstance(item, Mapping) or not isinstance(item.get('url'), str):
            raise CreditError(code='provider_failed', context={'reason': 'invalid_provider_result'})
        urls.append(_normalize_internal_url(item['url']))
    return urls


def _replay_result(usage: object) -> list[dict[str, str]]:
    snapshot = getattr(usage, 'result_snapshot', None)
    if not isinstance(snapshot, Mapping) or not isinstance(snapshot.get('urls'), list):
        raise _unavailable(reason='invalid_usage_result')
    urls = [_validate_internal_url(url) for url in snapshot['urls']]
    if not urls:
        raise _unavailable(reason='invalid_usage_result')
    return [{'url': url} for url in urls]


def _replay_error(usage: object) -> CreditError:
    snapshot = getattr(usage, 'error_snapshot', None)
    provider_code = None
    if isinstance(snapshot, Mapping) and isinstance(snapshot.get('code'), str):
        provider_code = snapshot['code']
    context: dict[str, object] = {'usage_id': getattr(usage, 'id', '')}
    if provider_code is not None:
        context['provider_code'] = provider_code
    return CreditError(code='provider_failed', context=context)


async def _authorize_image_call(identity: compat.BillingIdentity, action: Action) -> UserSnapshot:
    try:
        async with credit_session() as session:
            row = await session.execute(
                select(User.id, User.name, User.email, User.role).where(User.id == identity.user_id)
            )
            current_user = row.one_or_none()
            if current_user is None or current_user.role not in ('user', 'admin') or current_user.role != identity.role:
                raise HTTPException(status_code=403, detail=ERROR_MESSAGES.ACCESS_PROHIBITED)

            config = await compat.get_runtime_image_config()
            enabled = (
                getattr(config, 'ENABLE_IMAGE_GENERATION', False)
                if action == 'text-to-image'
                else getattr(config, 'ENABLE_IMAGE_EDIT', False)
            )
            if not enabled:
                raise HTTPException(status_code=403, detail=ERROR_MESSAGES.ACCESS_PROHIBITED)
            if current_user.role != 'admin' and not await has_permission(
                current_user.id,
                'features.image_generation',
                getattr(config, 'USER_PERMISSIONS', {}),
                db=session,
            ):
                raise HTTPException(status_code=403, detail=ERROR_MESSAGES.ACCESS_PROHIBITED)
            return UserSnapshot(id=current_user.id, name=current_user.name, email=current_user.email)
    except (CreditError, HTTPException):
        raise
    except Exception:
        raise _unavailable(reason='authorization_failed') from None


async def _prepare_image_call(
    request: object,
    raw_form_data: object,
    metadata: dict | None,
    raw_user: object | None,
    action: Action,
) -> compat.PreparedImageCall:
    from open_webui.extensions.credits.image_adapter import prepare_edit_call, prepare_generation_call

    if action == 'text-to-image':
        image_input = compat.map_generation_form(raw_form_data)
        return await prepare_generation_call(request, image_input, metadata, raw_user)
    image_input = compat.map_edit_form(raw_form_data)
    return await prepare_edit_call(request, image_input, metadata, raw_user)


def _to_provider_form(prepared: compat.PreparedImageCall, action: Action) -> object:
    if action == 'text-to-image':
        return compat.to_generation_form(prepared.provider_input)
    return compat.to_edit_form(prepared.provider_input)


def _old_outcome(begin: object) -> list[dict[str, str]]:
    outcome = begin.outcome
    usage = begin.usage
    if outcome == 'succeeded':
        return _replay_result(usage)
    if outcome == 'failed':
        raise _replay_error(usage)
    if outcome == 'processing':
        raise CreditError(code='usage_processing', context={'usage_id': usage.id})
    if outcome == 'unknown':
        raise _unavailable(usage.id, reason='usage_unknown')
    raise _unavailable(getattr(usage, 'id', None), reason='invalid_usage_outcome')


def _safe_provider_error(error: Exception) -> object:
    from open_webui.extensions.credits.service import SafeProviderError

    if isinstance(error, HTTPException) and 100 <= error.status_code <= 599:
        code = f'http_{error.status_code}'
    elif isinstance(error, CreditError):
        code = error.code
    else:
        code = 'provider_failed'
    return SafeProviderError(code=code, summary='Image provider request failed')


async def _mark_failed_or_unavailable(usage_id: str, error: Exception) -> None:
    try:
        changed = await mark_usage_failed(usage_id, _safe_provider_error(error))
    except Exception:
        raise _unavailable(usage_id, reason='failed_status_write_failed') from None
    if changed != 1:
        raise _unavailable(usage_id, reason='failed_status_not_updated')


async def _mark_succeeded_or_unavailable(usage_id: str, urls: Sequence[str]) -> None:
    try:
        changed = await mark_usage_succeeded(usage_id, urls)
    except Exception:
        raise _unavailable(usage_id, reason='success_status_write_failed') from None
    if changed != 1:
        raise _unavailable(usage_id, reason='success_status_not_updated')


async def bill_image_call(
    *,
    request: object,
    raw_form_data: object,
    metadata: dict | None,
    raw_user: object | None,
    action: Action,
    invoke: Callable[[object], Awaitable[list[dict[str, str]]]],
) -> list[dict[str, str]]:
    """Prepare, prepay and invoke one image request without repeating terminal usages."""
    identity = compat.map_billing_identity(raw_user)
    user = await _authorize_image_call(identity, action)
    prepared = await _prepare_image_call(request, raw_form_data, metadata, raw_user, action)
    idempotency_key = _idempotency_key(request, metadata, identity, action)

    try:
        async with credit_session() as session:
            begin = await begin_image_usage(session, user, prepared.billing, idempotency_key)
    except CreditError:
        raise
    except Exception:
        raise _unavailable(reason='precharge_failed') from None

    if begin.outcome != 'new':
        return _old_outcome(begin)

    try:
        invoking = await mark_usage_invoking(begin.usage.id)
    except Exception:
        raise _unavailable(begin.usage.id, reason='invoking_status_write_failed') from None
    if invoking != 1:
        raise _unavailable(begin.usage.id, reason='invoking_status_not_updated')

    provider_form = _to_provider_form(prepared, action)
    try:
        result = await invoke(provider_form)
        urls = _result_urls(result)
    except asyncio.CancelledError:
        raise
    except Exception as error:
        await _mark_failed_or_unavailable(begin.usage.id, error)
        raise CreditError(code='provider_failed', context={'usage_id': begin.usage.id}) from None

    await _mark_succeeded_or_unavailable(begin.usage.id, urls)
    return [{'url': url} for url in urls]


__all__ = ['bill_image_call']
