import hmac
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from time import time
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from open_webui.env import WEBUI_SECRET_KEY
from open_webui.extensions.credits.compat import CompatImageInput, get_credit_users, publish_credit_price_event
from open_webui.extensions.credits.constants import (
    CREDIT_ADJUSTMENT_RATE_LIMIT,
    CREDIT_LEDGER_RATE_LIMIT,
    CREDIT_QUOTE_CACHE_MAX_ENTRIES,
    CREDIT_QUOTE_CACHE_TTL_SECONDS,
    CREDIT_QUOTE_RATE_LIMIT,
    CREDIT_RATE_LIMIT_WINDOW_SECONDS,
    DEFAULT_PAGE_SIZE,
    MAX_IMAGE_PROMPT_BYTES,
    MAX_IMAGE_REFERENCES,
    MAX_PAGE_SIZE,
)
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.image_adapter import prepare_edit_call, prepare_generation_call
from open_webui.extensions.credits.metrics import credit_metrics
from open_webui.extensions.credits.models import CreditAccount, CreditPrice
from open_webui.extensions.credits.pricing import compute_price
from open_webui.extensions.credits.repository import get_balance_if_exists, get_enabled_price
from open_webui.extensions.credits.schemas import (
    AdjustmentRequest,
    AdminLedgerQuery,
    CompensationRequest,
    PositivePrice,
    PriceRuleSet,
    ReconciliationQuery,
    RequestAuditContext,
    UserLedgerQuery,
    UserSnapshot,
)
from open_webui.extensions.credits.service import (
    adjust_balance,
    compensate_reconciliation_case,
    get_balance,
    list_admin_ledger,
    list_reconciliation_cases,
    list_user_ledger,
)
from open_webui.internal.db import get_async_session
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.rate_limit import RateLimiter
from open_webui.utils.redis import get_redis_client
from opentelemetry import metrics
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/v1/credits', tags=['credits'])
log = logging.getLogger(__name__)
_rate_limit_fallback_counter = metrics.get_meter(__name__).create_counter(
    'webui.credits.rate_limit.fallbacks',
    description='Counts credit API rate-limit checks that fell back to process memory.',
    unit='1',
)


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
    log.warning('Credit rate limiting is using single-process fallback', extra={'credit_rate_limit_fallback': True})


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
_quote_cache: dict[tuple[str, str, str, int], tuple[float, dict[str, object]]] = {}
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
    }
}


class ImageQuoteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)

    resource_id: str = Field(min_length=1, max_length=128)
    action: str = Field(pattern='^(text-to-image|image-to-image)$')
    prompt: str = Field(min_length=1, max_length=MAX_IMAGE_PROMPT_BYTES)
    image: str | Annotated[list[str], Field(max_length=MAX_IMAGE_REFERENCES)] | None = None
    dimensions: dict[str, str | int] = Field(default_factory=dict)


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


class PriceRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)

    service_type: str = Field(min_length=1, max_length=64)
    resource_id: str = Field(min_length=1, max_length=128)
    action: str = Field(min_length=1, max_length=64)
    base_price: PositivePrice
    rules: PriceRuleSet
    enabled: bool = True


class PriceUpdateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)

    base_price: PositivePrice | None = None
    rules: PriceRuleSet | None = None
    enabled: bool | None = None


def _enforce_rate_limit(limiter: RateLimiter, key: str) -> None:
    if limiter.is_limited(key):
        raise HTTPException(status_code=429, detail={'code': 'rate_limit_exceeded'})


def _public_error_response(error: CreditError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content=error.to_envelope())


def _public_user_error_response(error: CreditError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content={**error.to_envelope(), 'context': {}})


def _public_pricing_snapshot(snapshot: Mapping[str, object] | None) -> dict[str, object] | None:
    if not isinstance(snapshot, Mapping):
        return None
    return {
        key: value
        for key, value in snapshot.items()
        if key in {'factors', 'charged_credits', 'rounding'}
    }


def _public_user_ledger_item(item: object) -> dict[str, object]:
    from open_webui.utils.images.fal_models import public_fal_image_model_id

    serialized = item.model_dump(mode='json') if hasattr(item, 'model_dump') else dict(item)
    resource_id = serialized.get('resource_id')
    public_resource_id = public_fal_image_model_id(resource_id) if isinstance(resource_id, str) else None
    serialized['resource_id'] = public_resource_id
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
    if request.headers.get('authorization'):
        return 'api'
    if request.cookies.get('token'):
        return 'web'
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


def _admin_quote(balance: int, price: CreditPrice | None) -> dict[str, object]:
    return _quote_response(
        balance,
        sufficient=True,
        exempt=True,
        configured=price is not None,
        factors=[],
        charged_credits=0,
        error=None,
    )


async def _prepare_quote_call(action: str, image_input: CompatImageInput, user: UserSnapshot):
    if action == 'text-to-image':
        return await prepare_generation_call(None, image_input, None, user)
    return await prepare_edit_call(None, image_input, None, user)


def _cached_quote(cache_key: tuple[str, str, str, int], balance: int, now: float) -> dict[str, object] | None:
    cached = _quote_cache.get(cache_key)
    if cached is not None and cached[0] > now:
        response = dict(cached[1])
        response['balance'] = balance
        response['sufficient'] = balance >= response['charged_credits']
        return response
    if cached is not None:
        del _quote_cache[cache_key]
    return None


def _cache_quote(cache_key: tuple[str, str, str, int], response: dict[str, object], now: float) -> None:
    if len(_quote_cache) >= CREDIT_QUOTE_CACHE_MAX_ENTRIES:
        oldest_key = min(_quote_cache, key=lambda key: _quote_cache[key][0])
        del _quote_cache[oldest_key]
    _quote_cache[cache_key] = (now + CREDIT_QUOTE_CACHE_TTL_SECONDS, dict(response))


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
    if getattr(user, 'role', None) == 'admin':
        return _admin_quote(balance, price)
    if price is None:
        credit_metrics.quote_rejected(
            model=billing.resource_id,
            action=billing.action,
            error_code='price_not_configured',
        )
        return _unconfigured_quote(balance, 'price_not_configured')
    cache_key = (user.id, str(getattr(price, 'id', '')), f'{billing.action}:{billing.request_hash}', price.updated_at)
    now = time()
    cached = _cached_quote(cache_key, balance, now)
    if cached is not None:
        credit_metrics.quote_succeeded(
            model=billing.resource_id,
            action=billing.action,
            charged_credits=int(cached['charged_credits']),
        )
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
    _cache_quote(cache_key, quote_response, now)
    credit_metrics.quote_succeeded(
        model=billing.resource_id,
        action=billing.action,
        charged_credits=quote.charged_credits,
    )
    return quote_response


@router.post('/quotes/image')
async def get_image_credit_quote(
    quote_request: ImageQuoteRequest,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    snapshot = _user_snapshot(user)
    _enforce_rate_limit(_quote_limiter, f'credits:quote:{snapshot.id}')
    payload = quote_request.model_dump()
    try:
        return await quote_image(session, snapshot, payload)
    except CreditError as error:
        return _public_user_error_response(error)
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
    _enforce_rate_limit(_ledger_limiter, f'credits:ledger:{_user_snapshot(user).id}')
    try:
        page = await list_user_ledger(session, _user_snapshot(user).id, query)
    except CreditError as error:
        return _public_user_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)
    return _public_user_ledger_page(page)


@router.get('/admin/ledger')
async def get_admin_credit_ledger(
    query: AdminLedgerQuery = Depends(),
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    _enforce_rate_limit(_ledger_limiter, f'credits:admin-ledger:{_user_snapshot(_user).id}')
    try:
        page = await list_admin_ledger(session, query)
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)
    return page.model_dump()


@router.get('/admin/reconciliation')
async def get_credit_reconciliation_cases(
    query: ReconciliationQuery = Depends(),
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    _enforce_rate_limit(_ledger_limiter, f'credits:reconciliation:{_user_snapshot(user).id}')
    try:
        return (await list_reconciliation_cases(session, query)).model_dump()
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


@router.post('/admin/reconciliation/{usage_id}/compensate')
async def compensate_credit_reconciliation_case(
    usage_id: Annotated[str, Field(min_length=1, max_length=128)],
    body: CompensationRequest,
    request: Request,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    _enforce_rate_limit(_adjustment_limiter, f'credits:reconciliation-adjust:{_user_snapshot(user).id}')
    try:
        audit = _audit_context(request)
        ledger, created = await compensate_reconciliation_case(
            session,
            usage_id,
            _user_snapshot(user),
            body,
            audit,
        )
        return {'ledger_id': ledger.id, 'created': created, 'amount': ledger.amount}
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


@router.post('/admin/accounts/{user_id}/adjustments')
async def create_credit_adjustment(
    user_id: Annotated[str, Field(min_length=1, max_length=128)],
    adjustment: AdjustmentRequest,
    request: Request,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    _enforce_rate_limit(_adjustment_limiter, f'credits:adjustment:{_user_snapshot(user).id}')
    try:
        audit = _audit_context(request)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=422, detail={'code': 'invalid_request_id'}) from None
    try:
        ledger = await adjust_balance(
            session,
            UserSnapshot(id=user_id, name=None, email=None),
            _user_snapshot(user),
            adjustment,
            audit,
        )
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)
    return {'ledger_id': ledger.id, 'source': ledger.request_source, 'request_id': ledger.request_id}


def _allowed_dimensions(service_type: str, action: str) -> Mapping[str, tuple[str, ...]] | None:
    actions = _IMAGE_DIMENSIONS.get(service_type)
    return actions.get(action) if actions is not None else None


def _validate_price_dimensions(service_type: str, action: str, rules: PriceRuleSet) -> None:
    allowed = _allowed_dimensions(service_type, action)
    invalid_rule = (
        any(rule.key not in allowed or rule.kind not in allowed[rule.key] for rule in rules.dimensions)
        if allowed is not None
        else True
    )
    if invalid_rule:
        raise HTTPException(status_code=422, detail={'code': 'invalid_price_dimensions'})
    if any(rule.kind == 'exact_map' and 'default' not in rule.values for rule in rules.dimensions):
        raise HTTPException(status_code=422, detail={'code': 'incomplete_price_dimension'})


def _request_price_audit(request: Request) -> RequestAuditContext:
    try:
        return _audit_context(request)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=422, detail={'code': 'invalid_request_id'}) from None


async def _publish_price_event(
    request: Request,
    user: object,
    price: CreditPrice,
    operation: str,
    fields: list[str],
    audit: RequestAuditContext,
) -> None:
    await publish_credit_price_event(
        request,
        operation,
        actor=user,
        subject_id=price.id,
        data={
            'price_id': price.id,
            'service_type': price.service_type,
            'resource_id': price.resource_id,
            'action': price.action,
            'operator_id': getattr(user, 'id', None),
            'request_id': audit.request_id,
            'changed_fields': fields,
        },
    )


@router.get('/admin/accounts')
async def get_credit_accounts(
    query: str | None = None,
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    if skip < 0 or limit < 1 or limit > MAX_PAGE_SIZE:
        raise HTTPException(status_code=422, detail={'code': 'invalid_pagination'})
    try:
        users = await get_credit_users({'query': query} if query else {}, skip, limit, session=session)
        items = users.get('users', [])
        identifiers = [item.id for item in items]
        balances = {}
        if identifiers:
            statement = select(CreditAccount.user_id, CreditAccount.balance).where(
                CreditAccount.user_id.in_(identifiers)
            )
            balances = {user_id: balance for user_id, balance in (await session.execute(statement)).all()}
    except Exception as error:
        return _unexpected_error_response(error)
    return {
        'items': [
            {
                'user_id': item.id,
                'name': item.name,
                'email': item.email,
                'balance': balances.get(item.id, 0),
            }
            for item in items
        ],
        'total': users.get('total', 0),
    }


@router.get('/admin/prices')
async def list_credit_prices(
    skip: Annotated[int, Field(ge=0)] = 0,
    limit: Annotated[int, Field(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[dict[str, object]]:
    try:
        statement = select(CreditPrice).order_by(CreditPrice.updated_at.desc()).offset(skip).limit(limit)
        prices = (await session.scalars(statement)).all()
    except Exception as error:
        return _unexpected_error_response(error)
    return [_price_response(price) for price in prices]


@router.post('/admin/prices')
async def create_credit_price(
    body: PriceRequest,
    request: Request,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    now = int(time())
    audit = _request_price_audit(request)
    _validate_price_dimensions(body.service_type, body.action, body.rules)
    body_values = body.model_dump(mode='json')
    price = CreditPrice(
        id=str(uuid4()),
        **body_values,
        updated_by_id=getattr(user, 'id', None),
        updated_by_name_snapshot=getattr(user, 'name', None),
        updated_by_email_snapshot=getattr(user, 'email', None),
        created_at=now,
        updated_at=now,
    )
    try:
        async with session.begin():
            existing = await session.scalar(
                select(CreditPrice.id).where(
                    CreditPrice.service_type == body.service_type,
                    CreditPrice.resource_id == body.resource_id,
                    CreditPrice.action == body.action,
                )
            )
            if existing is not None:
                raise HTTPException(status_code=409, detail={'code': 'price_already_exists'})
            session.add(price)
            await session.flush()
    except HTTPException:
        raise
    except Exception as error:
        return _unexpected_error_response(error)
    try:
        await _publish_price_event(request, user, price, 'created', list(body_values), audit)
    except Exception as error:
        return _unexpected_error_response(error)
    return _price_response(price)


@router.put('/admin/prices/{price_id}')
async def update_credit_price(
    price_id: Annotated[str, Field(min_length=1, max_length=128)],
    body: PriceUpdateRequest,
    request: Request,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    changes = body.model_dump(exclude_none=True, mode='json')
    if not changes:
        raise HTTPException(status_code=422, detail={'code': 'empty_price_update'})
    audit = _request_price_audit(request)
    price = None
    try:
        async with session.begin():
            price = await session.get(CreditPrice, price_id)
            if price is not None:
                next_rules = body.rules if body.rules is not None else PriceRuleSet.model_validate(price.rules)
                _validate_price_dimensions(price.service_type, price.action, next_rules)
                for field, value in changes.items():
                    setattr(price, field, value)
                price.updated_at = max(int(time()), price.updated_at + 1)
                price.updated_by_id = getattr(user, 'id', None)
                price.updated_by_name_snapshot = getattr(user, 'name', None)
                price.updated_by_email_snapshot = getattr(user, 'email', None)
                await session.flush()
    except HTTPException:
        raise
    except Exception as error:
        return _unexpected_error_response(error)
    if price is None:
        raise HTTPException(status_code=404, detail={'code': 'price_not_found'})
    try:
        await _publish_price_event(request, user, price, 'updated', list(changes), audit)
    except Exception as error:
        return _unexpected_error_response(error)
    return _price_response(price)


@router.delete('/admin/prices/{price_id}')
async def delete_credit_price(
    price_id: Annotated[str, Field(min_length=1, max_length=128)],
    request: Request,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    audit = _request_price_audit(request)
    event_price: CreditPrice | None = None
    try:
        async with session.begin():
            price = await session.get(CreditPrice, price_id)
            if price is not None:
                event_price = CreditPrice(
                    id=price.id,
                    service_type=price.service_type,
                    resource_id=price.resource_id,
                    action=price.action,
                    base_price=price.base_price,
                    rules={},
                    enabled=price.enabled,
                    created_at=price.created_at,
                    updated_at=price.updated_at,
                )
                await session.delete(price)
    except Exception as error:
        return _unexpected_error_response(error)
    if event_price is None:
        raise HTTPException(status_code=404, detail={'code': 'price_not_found'})
    try:
        await _publish_price_event(request, user, event_price, 'deleted', [], audit)
    except Exception as error:
        return _unexpected_error_response(error)
    return {'id': price_id}


@router.get('/admin/dimensions/{service_type}')
async def get_credit_dimensions(
    service_type: Annotated[str, Field(min_length=1, max_length=64)],
    _user=Depends(get_admin_user),
) -> dict[str, object]:
    dimensions = _IMAGE_DIMENSIONS.get(service_type)
    if dimensions is None:
        raise HTTPException(status_code=404, detail={'code': 'service_type_not_found'})
    return {
        'service_type': service_type,
        'dimensions': {
            action: [{'key': key, 'rule_types': list(rule_types)} for key, rule_types in registered.items()]
            for action, registered in dimensions.items()
        },
    }


def _price_response(price: CreditPrice) -> dict[str, object]:
    return {
        'id': price.id,
        'service_type': price.service_type,
        'resource_id': price.resource_id,
        'action': price.action,
        'base_price': price.base_price,
        'rules': price.rules,
        'enabled': price.enabled,
        'updated_at': price.updated_at,
    }
