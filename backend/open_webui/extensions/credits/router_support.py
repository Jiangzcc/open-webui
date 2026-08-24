"""积分路由的共享支撑层：限流器、公开错误视图与审计上下文。

从 router.py 拆出（复盘：超长文件拆分）。公开用户端点与管理端点共用
这些助手；管理端路由见 router_admin.py。
"""

from __future__ import annotations

import hmac
import logging
from asyncio import to_thread
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from open_webui.env import WEBUI_SECRET_KEY
from open_webui.extensions.credits.constants import (
    CREDIT_ADJUSTMENT_RATE_LIMIT,
    CREDIT_LEDGER_RATE_LIMIT,
    CREDIT_QUOTE_RATE_LIMIT,
    CREDIT_RATE_LIMIT_WINDOW_SECONDS,
    CREDIT_REDEEM_ADMIN_RATE_LIMIT,
    CREDIT_REDEEM_RATE_LIMIT,
)
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.schemas import RequestAuditContext, UserSnapshot
from open_webui.utils.rate_limit import RateLimiter
from open_webui.utils.redis import get_redis_client
from opentelemetry import metrics

log = logging.getLogger(__name__)
_rate_limit_fallback_counter = metrics.get_meter(__name__).create_counter(
    'webui.credits.rate_limit.fallbacks',
    description='Counts credit API rate-limit checks that fell back to process memory.',
    unit='1',
)

# 各服务/动作允许的定价维度与取值形态（报价校验、定价管理、维度查询共用）。
_IMAGE_DIMENSIONS = {
    'image': {
        'text-to-image': {
            'size': ('exact_map',),
            'resolution': ('exact_map',),
            'aspect_ratio': ('exact_map',),
            'quality': ('exact_map',),
            'image_count': ('quantity',),
            'pixel_count': ('proportional',),
        },
        'image-to-image': {
            'size': ('exact_map',),
            'resolution': ('exact_map',),
            'aspect_ratio': ('exact_map',),
            'quality': ('exact_map',),
            'image_count': ('quantity',),
            'pixel_count': ('proportional',),
        },
    },
    'video': {
        'text-to-video': {
            'duration': ('exact_map', 'numeric_tier', 'unit_blocks'),
            'resolution': ('exact_map',),
            'aspect_ratio': ('exact_map',),
            'audio_mode': ('exact_map',),
            'fps': ('exact_map',),
            'output_quality': ('exact_map',),
        },
        'image-to-video': {
            'duration': ('exact_map', 'numeric_tier', 'unit_blocks'),
            'resolution': ('exact_map',),
            'aspect_ratio': ('exact_map',),
            'audio_mode': ('exact_map',),
            'fps': ('exact_map',),
            'output_quality': ('exact_map',),
        },
        'video-to-video': {
            'duration': ('exact_map', 'numeric_tier', 'unit_blocks'),
            'resolution': ('exact_map',),
            'aspect_ratio': ('exact_map',),
            'audio_mode': ('exact_map',),
            'fps': ('exact_map',),
            'output_quality': ('exact_map',),
        },
    },
}

class CreditRateLimiter(RateLimiter):
    def is_limited(self, key: str) -> bool:
        if not self.enabled:
            return False
        if self._redis_available():
            try:
                return self._is_limited_redis(key)
            except Exception:
                _record_rate_limit_fallback(key)
                return self._is_limited_memory(key)
        _record_rate_limit_fallback(key)
        return self._is_limited_memory(key)


def _rate_limit_operation(key: str) -> str:
    parts = key.split(':', 2)
    return parts[1] if len(parts) == 3 else 'unknown'


def _record_rate_limit_fallback(key: str) -> None:
    _rate_limit_fallback_counter.add(1, {'credit.rate_limit.operation': _rate_limit_operation(key)})
    _log_rate_limit_fallback_once(_rate_limit_operation(key))


@lru_cache(maxsize=32)
def _log_rate_limit_fallback_once(operation: str) -> None:
    log.warning(
        'Credit rate limiting is using single-process fallback',
        extra={'credit_rate_limit_fallback': True, 'credit_rate_limit_operation': operation},
    )


_sync_redis = get_redis_client(async_mode=False)
_quote_limiter = CreditRateLimiter(
    _sync_redis,
    limit=CREDIT_QUOTE_RATE_LIMIT,
    window=CREDIT_RATE_LIMIT_WINDOW_SECONDS,
)
_ledger_limiter = CreditRateLimiter(
    _sync_redis,
    limit=CREDIT_LEDGER_RATE_LIMIT,
    window=CREDIT_RATE_LIMIT_WINDOW_SECONDS,
)
_adjustment_limiter = CreditRateLimiter(
    _sync_redis,
    limit=CREDIT_ADJUSTMENT_RATE_LIMIT,
    window=CREDIT_RATE_LIMIT_WINDOW_SECONDS,
)
_redeem_limiter = CreditRateLimiter(
    _sync_redis,
    limit=CREDIT_REDEEM_RATE_LIMIT,
    window=CREDIT_RATE_LIMIT_WINDOW_SECONDS,
)
_redeem_admin_limiter = CreditRateLimiter(
    _sync_redis,
    limit=CREDIT_REDEEM_ADMIN_RATE_LIMIT,
    window=CREDIT_RATE_LIMIT_WINDOW_SECONDS,
)

async def _enforce_rate_limit(limiter: RateLimiter, key: str) -> None:
    # RateLimiter and its Redis client are synchronous upstream APIs. Running
    # them on the event loop can stall every request in this single-worker
    # deployment when Redis is slow, so isolate the entire check in a thread.
    if await to_thread(limiter.is_limited, key):
        raise HTTPException(status_code=429, detail={'code': 'rate_limit_exceeded'})


def _public_error_response(error: CreditError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content=error.to_envelope())


def _public_user_error_response(error: CreditError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content={**error.to_envelope(), 'context': {}})


def _public_pricing_snapshot(snapshot: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(snapshot, Mapping):
        return None
    return {key: value for key, value in snapshot.items() if key in {'factors', 'charged_credits', 'rounding'}}


def _public_user_ledger_resource_id(resource_id: object) -> str | None:
    """Map an internal billing resource id to the user-facing public id.

    图片和视频目录各自维护内部 ID → 公开 ID 的映射；都不命中时（非 fal 引擎、
    目录未收录的资源）保留原始 ID，避免明细里的资源信息被置空无法辨认。
    """
    if not isinstance(resource_id, str):
        return None

    from open_webui.extensions.fal_catalog import load_video_catalog_cached
    from open_webui.extensions.fal_images.models import public_fal_image_model_id

    public_id = public_fal_image_model_id(resource_id)
    if public_id is not None:
        return public_id
    return load_video_catalog_cached().internal_to_public.get(resource_id, resource_id)


def _public_user_ledger_item(item: object) -> dict[str, object]:
    serialized = item.model_dump(mode='json') if hasattr(item, 'model_dump') else dict(item)
    serialized['resource_id'] = _public_user_ledger_resource_id(serialized.get('resource_id'))
    serialized['pricing_snapshot'] = _public_pricing_snapshot(serialized.get('pricing_snapshot'))
    serialized['metadata_snapshot'] = None
    return serialized


def _public_user_ledger_page(page: object) -> dict[str, object]:
    if not hasattr(page, 'items'):
        return page.model_dump()
    return {
        'items': [_public_user_ledger_item(item) for item in page.items],
        'next_cursor': page.next_cursor.model_dump(mode='json') if page.next_cursor else None,
    }


def _unexpected_error_response(error: Exception) -> JSONResponse:
    correlation_id = str(uuid4())
    log.error(
        'Unexpected credit API failure',
        extra={
            'credit_correlation_id': correlation_id,
            'credit_error_type': type(error).__name__,
        },
    )
    return _public_error_response(CreditError(code='credit_service_unavailable'))


@dataclass(frozen=True)
class CreditUserSnapshot(UserSnapshot):
    role: str


def _user_snapshot(user: object) -> CreditUserSnapshot:
    return CreditUserSnapshot(
        id=getattr(user, 'id'),
        name=getattr(user, 'name', None),
        email=getattr(user, 'email', None),
        role=getattr(user, 'role', ''),
    )


def _request_credentials(request: Request) -> str:
    state_credentials = getattr(getattr(request.state, 'token', None), 'credentials', '')
    if isinstance(state_credentials, str) and state_credentials:
        return state_credentials
    authorization = request.headers.get('authorization', '').strip()
    if authorization.lower().startswith('bearer '):
        return authorization[7:]
    api_key = request.headers.get('x-api-key', '')
    return api_key if isinstance(api_key, str) else ''


def _request_id(request: Request) -> str:
    request_id = request.headers.get('X-Request-ID') or str(uuid4())
    try:
        RequestAuditContext(source='web', request_id=request_id, remote_address_hash=None)
    except ValueError:
        raise HTTPException(status_code=422, detail={'code': 'invalid_request_id'}) from None
    return request_id


def _request_source(request: Request, credentials: str) -> str:
    if credentials.startswith('sk-'):
        return 'api_key'
    if request.cookies.get('token'):
        return 'web'
    if request.headers.get('authorization'):
        return 'api'
    return 'internal_admin'


def _audit_context(request: Request) -> RequestAuditContext:
    credentials = _request_credentials(request)
    client_address = request.client.host if request.client is not None else None
    return RequestAuditContext(
        source=_request_source(request, credentials),
        request_id=_request_id(request),
        remote_address_hash=(
            hmac.new(WEBUI_SECRET_KEY.encode(), client_address.encode(), sha256).hexdigest() if client_address else None
        ),
    )


__all__ = [
    'CreditUserSnapshot',
    '_IMAGE_DIMENSIONS',
    '_adjustment_limiter',
    '_audit_context',
    '_enforce_rate_limit',
    '_ledger_limiter',
    '_public_error_response',
    '_public_pricing_snapshot',
    '_public_user_error_response',
    '_public_user_ledger_item',
    '_public_user_ledger_page',
    '_quote_limiter',
    '_redeem_admin_limiter',
    '_redeem_limiter',
    '_unexpected_error_response',
    '_user_snapshot',
]
