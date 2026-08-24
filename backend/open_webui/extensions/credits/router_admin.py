"""积分管理端路由（卡密批次、账户修复/调整、对账、定价管理）。

从 router.py 拆出（复盘：超长文件拆分）。公开用户端点与报价逻辑保留在
router.py；本模块的路由由 router.py 通过 include_router 挂载，共享前缀
/api/v1/credits 与共享助手见 router_support.py。
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from time import time
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from open_webui.extensions.credits.compat import get_credit_users, publish_credit_price_event
from open_webui.extensions.credits.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.models import CreditAccount, CreditPrice
from open_webui.extensions.credits.redemption import (
    create_redeem_batch,
    list_redeem_audit,
    list_redeem_batches,
    list_redeem_codes,
    void_redeem_batch,
    void_redeem_code,
)
from open_webui.extensions.credits.repair import CreditRepairError, repair_account_from_ledger
from open_webui.extensions.credits.router_support import (
    _IMAGE_DIMENSIONS,
    _adjustment_limiter,
    _audit_context,
    _enforce_rate_limit,
    _ledger_limiter,
    _public_error_response,
    _redeem_admin_limiter,
    _unexpected_error_response,
    _user_snapshot,
)
from open_webui.extensions.credits.schemas import (
    AdjustmentRequest,
    AdminLedgerQuery,
    CompensationRequest,
    CreditPriceQuery,
    PositivePrice,
    PriceRuleSet,
    ReconciliationQuery,
    RedeemBatchCreate,
    RequestAuditContext,
    UserSnapshot,
)
from open_webui.extensions.credits.service import (
    adjust_balance,
    compensate_reconciliation_case,
    list_admin_credit_prices,
    list_admin_ledger,
    list_reconciliation_cases,
)
from open_webui.internal.db import get_async_session
from open_webui.utils.auth import get_admin_user
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

admin_router = APIRouter(tags=['credits'])
log = logging.getLogger(__name__)


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


@admin_router.get('/admin/redeem-batches')
async def get_redeem_batches(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    await _enforce_rate_limit(_redeem_admin_limiter, f'credits:redeem-admin-list:{_user_snapshot(user).id}')
    try:
        return (await list_redeem_batches(session, skip=skip, limit=limit)).model_dump()
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


@admin_router.post('/admin/redeem-batches')
async def generate_redeem_batch(
    body: RedeemBatchCreate,
    request: Request,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    await _enforce_rate_limit(_redeem_admin_limiter, f'credits:redeem-admin-create:{_user_snapshot(user).id}')
    # Set this before generating any one-time plaintext. The shared ASGI scope is
    # server-owned, so a client cannot opt arbitrary responses out of audit logs.
    request.scope['audit_redact_bodies'] = frozenset({'response'})
    audit = _audit_context(request)
    try:
        result = await create_redeem_batch(session, body, _user_snapshot(user), audit)
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)
    return JSONResponse(
        status_code=201,
        content=result.model_dump(),
        headers={'Cache-Control': 'no-store, max-age=0'},
    )


@admin_router.get('/admin/redeem-batches/{batch_id}/codes')
async def get_redeem_batch_codes(
    batch_id: Annotated[str, Field(min_length=1, max_length=128)],
    request: Request,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    # The list exposes only irreversible-code metadata and a non-sensitive hint.
    # Keep it out of audit bodies and HTTP caches anyway, because redemption
    # status and operator activity are still administrative data.
    request.scope['audit_redact_bodies'] = frozenset({'response'})
    await _enforce_rate_limit(_redeem_admin_limiter, f'credits:redeem-admin-codes:{_user_snapshot(user).id}')
    try:
        page = await list_redeem_codes(session, batch_id, skip=skip, limit=limit)
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)
    return JSONResponse(
        content=page.model_dump(),
        headers={'Cache-Control': 'no-store, max-age=0'},
    )


@admin_router.get('/admin/redeem-batches/{batch_id}/audit')
async def get_redeem_batch_audit(
    batch_id: Annotated[str, Field(min_length=1, max_length=128)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    await _enforce_rate_limit(_redeem_admin_limiter, f'credits:redeem-admin-audit:{_user_snapshot(user).id}')
    try:
        return (await list_redeem_audit(session, batch_id, skip=skip, limit=limit)).model_dump()
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


@admin_router.post('/admin/redeem-batches/{batch_id}/void')
async def void_credit_redeem_batch(
    batch_id: Annotated[str, Field(min_length=1, max_length=128)],
    request: Request,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    await _enforce_rate_limit(_redeem_admin_limiter, f'credits:redeem-admin-void:{_user_snapshot(user).id}')
    audit = _audit_context(request)
    try:
        count = await void_redeem_batch(
            session,
            batch_id,
            _user_snapshot(user),
            audit,
        )
        return {'voided_count': count}
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


@admin_router.post('/admin/redeem-batches/{batch_id}/codes/{code_id}/void')
async def void_credit_redeem_code(
    batch_id: Annotated[str, Field(min_length=1, max_length=128)],
    code_id: Annotated[str, Field(min_length=1, max_length=128)],
    request: Request,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    await _enforce_rate_limit(_redeem_admin_limiter, f'credits:redeem-admin-void:{_user_snapshot(user).id}')
    audit = _audit_context(request)
    try:
        voided = await void_redeem_code(
            session,
            batch_id,
            code_id,
            _user_snapshot(user),
            audit,
        )
        return {'voided': voided}
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


class AccountRepairRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    incident_id: Annotated[str, Field(min_length=1, max_length=120)]
    expected_balance: Annotated[int, Field(ge=0)]
    note: Annotated[str, Field(min_length=1, max_length=1000)]
    backup_confirmed: bool = False


@admin_router.post('/admin/accounts/{user_id}/repair')
async def repair_credit_account_from_ledger(
    user_id: Annotated[str, Field(min_length=1, max_length=128)],
    body: AccountRepairRequest,
    request: Request,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    """账户-台账不一致时的管理员修复入口（审查发现 #9）。

    adjust_balance 的一致性校验会以 credit_service_unavailable/
    account_ledger_mismatch 拒绝一切调整；该端点在运维确认数据库备份后，
    按台账合计校准账户余额，让后续调整恢复可用。
    """
    await _enforce_rate_limit(_adjustment_limiter, f'credits:repair:{_user_snapshot(user).id}')
    try:
        ledger = await repair_account_from_ledger(
            session,
            user_id,
            _user_snapshot(user),
            body.incident_id,
            body.expected_balance,
            body.note,
            backup_confirmed=body.backup_confirmed,
        )
        return {
            'ledger_id': ledger.id,
            'balance_before': ledger.balance_before,
            'balance_after': ledger.balance_after,
            'request_id': ledger.request_id,
        }
    except CreditRepairError as error:
        raise HTTPException(status_code=422, detail={'code': 'invalid_repair_request', 'reason': str(error)})
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


@admin_router.get('/admin/ledger')
async def get_admin_credit_ledger(
    query: AdminLedgerQuery = Depends(),
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    await _enforce_rate_limit(_ledger_limiter, f'credits:admin-ledger:{_user_snapshot(_user).id}')
    try:
        page = await list_admin_ledger(session, query)
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)
    return page.model_dump()


@admin_router.get('/admin/reconciliation')
async def get_credit_reconciliation_cases(
    query: ReconciliationQuery = Depends(),
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    await _enforce_rate_limit(_ledger_limiter, f'credits:reconciliation:{_user_snapshot(user).id}')
    try:
        return (await list_reconciliation_cases(session, query)).model_dump()
    except CreditError as error:
        return _public_error_response(error)
    except Exception as error:
        return _unexpected_error_response(error)


@admin_router.post('/admin/reconciliation/{usage_id}/compensate')
async def compensate_credit_reconciliation_case(
    usage_id: Annotated[str, Field(min_length=1, max_length=128)],
    body: CompensationRequest,
    request: Request,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    await _enforce_rate_limit(_adjustment_limiter, f'credits:reconciliation-adjust:{_user_snapshot(user).id}')
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


@admin_router.post('/admin/accounts/{user_id}/adjustments')
async def create_credit_adjustment(
    user_id: Annotated[str, Field(min_length=1, max_length=128)],
    adjustment: AdjustmentRequest,
    request: Request,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    await _enforce_rate_limit(_adjustment_limiter, f'credits:adjustment:{_user_snapshot(user).id}')
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


@admin_router.get('/admin/accounts')
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


@admin_router.get('/admin/prices')
async def list_credit_prices(
    query: CreditPriceQuery = Depends(),
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    try:
        prices, total = await list_admin_credit_prices(session, query)
    except Exception as error:
        return _unexpected_error_response(error)
    return {'items': [_price_response(price) for price in prices], 'total': total}


@admin_router.post('/admin/prices')
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


@admin_router.put('/admin/prices/{price_id}')
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
                _apply_credit_price_update(price, body, changes, user)
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


def _apply_credit_price_update(
    price: CreditPrice,
    body: PriceUpdateRequest,
    changes: dict[str, object],
    user: object,
) -> None:
    next_rules = body.rules if body.rules is not None else PriceRuleSet.model_validate(price.rules)
    _validate_price_dimensions(price.service_type, price.action, next_rules)
    for field, value in changes.items():
        setattr(price, field, value)
    price.updated_at = max(int(time()), price.updated_at + 1)
    price.updated_by_id = getattr(user, 'id', None)
    price.updated_by_name_snapshot = getattr(user, 'name', None)
    price.updated_by_email_snapshot = getattr(user, 'email', None)


@admin_router.delete('/admin/prices/{price_id}')
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


@admin_router.get('/admin/dimensions/{service_type}')
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
