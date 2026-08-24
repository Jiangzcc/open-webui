import logging
from collections.abc import Mapping
from time import time
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from open_webui.extensions.credits import quote_cache
from open_webui.extensions.credits.compat import CompatImageInput
from open_webui.extensions.credits.constants import (
    MAX_IMAGE_PROMPT_BYTES,
    MAX_IMAGE_REFERENCES,
)
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.image_adapter import prepare_edit_call, prepare_generation_call
from open_webui.extensions.credits.metrics import credit_metrics
from open_webui.extensions.credits.pricing import compute_price
from open_webui.extensions.credits.redemption import redeem_code
from open_webui.extensions.credits.repository import get_balance_if_exists, get_enabled_price
from open_webui.extensions.credits.router_admin import admin_router
from open_webui.extensions.credits.router_support import (
    CreditUserSnapshot,
    _audit_context,
    _enforce_rate_limit,
    _ledger_limiter,
    _public_user_error_response,
    _public_user_ledger_page,
    _quote_limiter,
    _redeem_limiter,
    _unexpected_error_response,
    _user_snapshot,
)
from open_webui.extensions.credits.schemas import UserLedgerQuery, UserSnapshot
from open_webui.extensions.credits.service import get_balance, list_user_ledger
from open_webui.extensions.videos.billing import normalize_video_duration_dimension
from open_webui.internal.db import get_async_session
from open_webui.utils.auth import get_verified_user
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/v1/credits', tags=['credits'])
log = logging.getLogger(__name__)
# 旧测试仍直接清理/注入 router._quote_cache；让它指向唯一的进程内缓存，
# 不再维护第二份生产缓存。
_quote_cache = quote_cache.memory_cache()


class ImageQuoteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)

    resource_id: str = Field(min_length=1, max_length=128)
    action: str = Field(pattern='^(text-to-image|image-to-image)$')
    prompt: str = Field(min_length=1, max_length=MAX_IMAGE_PROMPT_BYTES)
    image: str | Annotated[list[str], Field(max_length=MAX_IMAGE_REFERENCES)] | None = None
    dimensions: dict[str, str | int] = Field(default_factory=dict)


class VideoQuoteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)

    resource_id: str = Field(min_length=1, max_length=128)
    action: str = Field(pattern='^(text-to-video|image-to-video|video-to-video)$')
    dimensions: dict[str, str | int] = Field(default_factory=dict)


def _normalize_video_quote_dimensions(values: Mapping[str, str | int]) -> dict[str, str | int]:
    # 复盘 #18：duration 归一化与 videos/billing 统一为单一实现。
    dimensions = dict(values)
    if 'duration' in dimensions:
        dimensions['duration'] = normalize_video_duration_dimension(dimensions['duration'])
    return dimensions


def _quote_input_values(payload: Mapping[str, object]) -> tuple[str, Mapping[str, object], str, object]:
    resource_id = payload.get('resource_id')
    dimensions = payload.get('dimensions')
    prompt = payload.get('prompt')
    image = payload.get('image')
    if not isinstance(resource_id, str) or not isinstance(dimensions, Mapping) or not isinstance(prompt, str):
        raise CreditError(code='credit_service_unavailable')
    return resource_id, dimensions, prompt, image


def _quote_image_input(payload: Mapping[str, object]) -> CompatImageInput:
    resource_id, dimensions, prompt, image = _quote_input_values(payload)
    if isinstance(image, list):
        image = tuple(image)
    for dimension in ('size', 'resolution', 'aspect_ratio', 'quality'):
        if dimension in dimensions and not isinstance(dimensions[dimension], str):
            raise CreditError(code='price_rule_incomplete', context={'reason': f'invalid_{dimension}'})
    count = dimensions.get('image_count', 1)
    if not isinstance(count, int) or isinstance(count, bool):
        raise CreditError(code='price_rule_incomplete', context={'reason': 'invalid_image_count'})
    return CompatImageInput(
        model=resource_id,
        prompt=prompt,
        image=image,
        size=dimensions.get('size') if isinstance(dimensions.get('size'), str) else None,
        resolution=dimensions.get('resolution') if isinstance(dimensions.get('resolution'), str) else None,
        aspect_ratio=dimensions.get('aspect_ratio') if isinstance(dimensions.get('aspect_ratio'), str) else None,
        quality=dimensions.get('quality') if isinstance(dimensions.get('quality'), str) else None,
        image_count=count,
        extra={
            key: value
            for key, value in dimensions.items()
            if key not in {'size', 'resolution', 'aspect_ratio', 'quality', 'image_count'}
        },
    )


def _quote_response(
    balance: int,
    *,
    sufficient: bool,
    exempt: bool,
    configured: bool,
    factors: list[dict[str, object]],
    charged_credits: int | None,
    error: str | None,
) -> dict[str, object]:
    return {
        'balance': balance,
        'sufficient': sufficient,
        'exempt': exempt,
        'configured': configured,
        'factors': factors,
        'charged_credits': charged_credits,
        'error': error,
    }


def _unconfigured_quote(balance: int, error: str) -> dict[str, object]:
    return _quote_response(
        balance,
        sufficient=False,
        exempt=False,
        configured=False,
        factors=[],
        charged_credits=None,
        error=error,
    )


async def _prepare_quote_call(action: str, image_input: CompatImageInput, user: UserSnapshot):
    if action == 'text-to-image':
        return await prepare_generation_call(None, image_input, None, user)
    return await prepare_edit_call(None, image_input, None, user)


async def _cached_quote(
    cache_key: tuple[str, str, str, int],
    balance: int,
    now: float,
) -> dict[str, object] | None:
    return await quote_cache.get_cached_quote(cache_key, balance, now)


async def _cache_quote(cache_key: tuple[str, str, str, int], response: dict[str, object], now: float) -> None:
    await quote_cache.cache_quote(cache_key, response, now)


def _record_quote_success(resource_id: str, action: str, charged_credits: int) -> None:
    credit_metrics.quote_succeeded(model=resource_id, action=action, charged_credits=charged_credits)


async def quote_image(session: AsyncSession, user: UserSnapshot, payload: Mapping[str, object]) -> dict[str, object]:
    resource_id = payload.get('resource_id')
    action = payload.get('action')
    dimensions = payload.get('dimensions')
    if not isinstance(resource_id, str) or not isinstance(action, str) or not isinstance(dimensions, Mapping):
        raise CreditError(code='credit_service_unavailable')

    image_input = _quote_image_input(payload)
    prepared = await _prepare_quote_call(action, image_input, user)
    billing = prepared.billing
    price = await get_enabled_price(session, billing.service_type, billing.resource_id, billing.action)
    balance = await get_balance_if_exists(session, user.id)
    if price is None:
        credit_metrics.quote_rejected(
            model=billing.resource_id,
            action=billing.action,
            error_code='price_not_configured',
        )
        return _unconfigured_quote(balance, 'price_not_configured')
    cache_key = (user.id, str(getattr(price, 'id', '')), f'{billing.action}:{billing.request_hash}', price.updated_at)
    now = time()
    cached = await _cached_quote(cache_key, balance, now)
    if cached is not None:
        _record_quote_success(billing.resource_id, billing.action, int(cached['charged_credits']))
        return cached

    try:
        quote = compute_price(price, billing.dimensions)
    except CreditError as error:
        if error.code != 'price_rule_incomplete':
            raise
        credit_metrics.quote_rejected(
            model=billing.resource_id,
            action=billing.action,
            error_code=error.code,
        )
        return _unconfigured_quote(balance, error.code)
    quote_response = _quote_response(
        balance,
        sufficient=balance >= quote.charged_credits,
        exempt=False,
        configured=True,
        factors=[factor.__dict__ for factor in quote.factors],
        charged_credits=quote.charged_credits,
        error=None,
    )
    await _cache_quote(cache_key, quote_response, now)
    _record_quote_success(billing.resource_id, billing.action, quote.charged_credits)
    return quote_response


@router.post('/quotes/image')
async def get_image_credit_quote(
    quote_request: ImageQuoteRequest,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    snapshot = _user_snapshot(user)
    await _enforce_rate_limit(_quote_limiter, f'credits:quote:{snapshot.id}')
    payload = quote_request.model_dump()
    try:
        return await quote_image(session, snapshot, payload)
    except CreditError as error:
        return _public_user_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


async def quote_video(
    session: AsyncSession,
    snapshot: CreditUserSnapshot,
    quote_request: VideoQuoteRequest,
) -> dict[str, object]:
    from open_webui.extensions.fal_catalog import load_video_catalog_cached

    catalog = load_video_catalog_cached()
    internal_id = catalog.public_to_internal.get(quote_request.resource_id)
    if internal_id is None:
        raise CreditError(code='price_rule_incomplete', context={'reason': 'invalid_video_model'})
    definition = next((item for item in catalog.definitions if item.id == internal_id), None)
    if definition is None:
        raise CreditError(code='price_rule_incomplete', context={'reason': 'invalid_video_model'})
    if definition.task != quote_request.action:
        raise CreditError(code='price_rule_incomplete', context={'reason': 'video_model_task_mismatch'})
    dimensions = _normalize_video_quote_dimensions(quote_request.dimensions)
    balance = await get_balance_if_exists(session, snapshot.id)
    price = await get_enabled_price(session, 'video', internal_id, quote_request.action)
    if price is None:
        return _unconfigured_quote(balance, 'price_not_configured')
    quote = compute_price(price, dimensions)
    return _quote_response(
        balance,
        sufficient=balance >= quote.charged_credits,
        exempt=False,
        configured=True,
        factors=[factor.__dict__ for factor in quote.factors],
        charged_credits=quote.charged_credits,
        error=None,
    )


@router.post('/quotes/video')
async def get_video_credit_quote(
    quote_request: VideoQuoteRequest,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    snapshot = _user_snapshot(user)
    await _enforce_rate_limit(_quote_limiter, f'credits:quote:{snapshot.id}')
    try:
        return await quote_video(session, snapshot, quote_request)
    except CreditError as error:
        if error.code == 'price_rule_incomplete':
            try:
                balance = await get_balance_if_exists(session, snapshot.id)
                return _unconfigured_quote(balance, error.code)
            except Exception as balance_error:
                return _unexpected_error_response(balance_error)
        return _public_user_error_response(error)
    except (TypeError, ValueError) as error:
        return _unexpected_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


@router.get('/me')
async def get_my_credits(
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, int]:
    try:
        return {'balance': await get_balance(session, _user_snapshot(user))}
    except CreditError as error:
        return _public_user_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


@router.get('/me/ledger')
async def get_my_credit_ledger(
    query: UserLedgerQuery = Depends(),
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    await _enforce_rate_limit(_ledger_limiter, f'credits:ledger:{_user_snapshot(user).id}')
    try:
        page = await list_user_ledger(session, _user_snapshot(user).id, query)
    except CreditError as error:
        return _public_user_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)
    return _public_user_ledger_page(page)


@router.post('/redeem')
async def redeem_my_credit_code(
    request: Request,
    redeem_code_header: Annotated[
        str,
        Header(alias='X-Credit-Redeem-Code', min_length=1, max_length=64),
    ],
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    snapshot = _user_snapshot(user)
    await _enforce_rate_limit(_redeem_limiter, f'credits:redeem:{snapshot.id}')
    audit = _audit_context(request)
    try:
        result = await redeem_code(session, redeem_code_header, snapshot, audit)
        return result.model_dump()
    except CreditError as error:
        return _public_user_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


# 管理端路由（卡密批次/账户调整/对账/定价）与本路由共用 /api/v1/credits 前缀。
router.include_router(admin_router)
