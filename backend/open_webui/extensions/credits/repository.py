from __future__ import annotations

from collections.abc import Sequence
from time import time
from typing import Any
from uuid import uuid4

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .constants import MAX_CREDIT_VALUE
from .models import CreditAccount, CreditLedger, CreditPrice, CreditUsage
from .schemas import (
    AdminLedgerQuery,
    CreditPriceQuery,
    LedgerCursor,
    LedgerItem,
    UserLedgerQuery,
    UserSnapshot,
)


def _now() -> int:
    return int(time())


def _dialect_insert(session: AsyncSession) -> Any:
    dialect_name = session.get_bind().dialect.name
    if dialect_name == 'sqlite':
        return sqlite_insert
    if dialect_name == 'postgresql':
        return postgresql_insert
    raise RuntimeError(f'unsupported credit account database dialect: {dialect_name}')


async def get_or_create_account(session: AsyncSession, user: UserSnapshot, *, now: int | None = None) -> CreditAccount:
    """Create one account with a dialect-aware upsert, then return the persisted row."""
    created_at = _now() if now is None else now
    insert_statement = _dialect_insert(session)(CreditAccount).values(
        id=str(uuid4()),
        user_id=user.id,
        balance=0,
        user_name_snapshot=user.name,
        user_email_snapshot=user.email,
        created_at=created_at,
        updated_at=created_at,
    )
    await session.execute(insert_statement.on_conflict_do_nothing(index_elements=[CreditAccount.user_id]))
    await session.execute(
        update(CreditAccount)
        .where(
            CreditAccount.user_id == user.id,
            or_(
                CreditAccount.user_name_snapshot.is_distinct_from(user.name),
                CreditAccount.user_email_snapshot.is_distinct_from(user.email),
            ),
        )
        .values(
            user_name_snapshot=user.name,
            user_email_snapshot=user.email,
            updated_at=created_at,
        )
    )
    account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
    if account is None:
        raise RuntimeError('credit account was not persisted after upsert')
    return account


async def update_account_balance(
    session: AsyncSession,
    account: CreditAccount,
    signed_amount: int,
    *,
    now: int | None = None,
) -> tuple[int, int] | None:
    """Apply one signed atomic balance update and return its before/after values."""
    if signed_amount == 0:
        raise ValueError('signed amount must not be zero')

    updated_at = _now() if now is None else now
    if signed_amount > 0:
        statement = (
            update(CreditAccount)
            .where(
                CreditAccount.id == account.id,
                CreditAccount.balance <= MAX_CREDIT_VALUE - signed_amount,
            )
            .values(balance=CreditAccount.balance + signed_amount, updated_at=updated_at)
        )
    else:
        debit_amount = -signed_amount
        statement = (
            update(CreditAccount)
            .where(CreditAccount.id == account.id, CreditAccount.balance >= debit_amount)
            .values(balance=CreditAccount.balance - debit_amount, updated_at=updated_at)
        )

    result = await session.execute(statement)
    if result.rowcount != 1:
        return None
    balance_after = await session.scalar(select(CreditAccount.balance).where(CreditAccount.id == account.id))
    if balance_after is None:
        raise RuntimeError('credit account disappeared after balance update')
    return balance_after - signed_amount, balance_after


async def insert_ledger(session: AsyncSession, values: dict[str, Any]) -> CreditLedger:
    """Append one immutable ledger row in the caller's active transaction."""
    ledger = CreditLedger(**values)
    session.add(ledger)
    await session.flush()
    return ledger


async def claim_usage_placeholder(
    session: AsyncSession,
    values: dict[str, Any],
) -> CreditUsage | None:
    """Claim one idempotency key without committing the caller's transaction."""
    if session.get_bind().dialect.name == 'sqlite':
        result = await session.execute(
            sqlite_insert(CreditUsage)
            .values(**values)
            .on_conflict_do_nothing(index_elements=[CreditUsage.user_id, CreditUsage.idempotency_key])
        )
        if result.rowcount != 1:
            return None
        usage = await session.get(CreditUsage, values['id'])
        if usage is None:
            raise RuntimeError('credit usage was not persisted after claim')
        return usage

    usage = CreditUsage(**values)
    try:
        async with session.begin_nested():
            session.add(usage)
            await session.flush()
    except IntegrityError:
        return None
    return usage


async def get_balance_if_exists(session: AsyncSession, user_id: str) -> int:
    """Return a persisted balance without creating or updating an account."""
    balance = await session.scalar(select(CreditAccount.balance).where(CreditAccount.user_id == user_id))
    return 0 if balance is None else balance


async def get_enabled_prices(session: AsyncSession, service_type: str) -> list[CreditPrice]:
    """Return all enabled prices for one billable service."""
    result = await session.scalars(
        select(CreditPrice).where(
            CreditPrice.service_type == service_type,
            CreditPrice.enabled.is_(True),
        )
    )
    return list(result.all())


async def get_enabled_price(
    session: AsyncSession, service_type: str, resource_id: str, action: str
) -> CreditPrice | None:
    """Return the enabled price for one billable service action."""
    return await session.scalar(
        select(CreditPrice).where(
            CreditPrice.service_type == service_type,
            CreditPrice.resource_id == resource_id,
            CreditPrice.action == action,
            CreditPrice.enabled.is_(True),
        )
    )


async def get_usage_by_idempotency_key(session: AsyncSession, user_id: str, idempotency_key: str) -> CreditUsage | None:
    """Return an existing usage record for one user-owned idempotency key."""
    return await session.scalar(
        select(CreditUsage).where(CreditUsage.user_id == user_id, CreditUsage.idempotency_key == idempotency_key)
    )


def _credit_price_query_conditions(query: CreditPriceQuery) -> list[Any]:
    """积分价格列表的过滤条件，供行查询与计数查询共用，避免两处分叉。"""
    conditions: list[Any] = []
    if query.service_type is not None:
        conditions.append(CreditPrice.service_type == query.service_type)
    if query.resource_id is not None:
        conditions.append(CreditPrice.resource_id == query.resource_id)
    if query.action is not None:
        conditions.append(CreditPrice.action == query.action)
    if query.enabled is not None:
        conditions.append(CreditPrice.enabled.is_(query.enabled))
    return conditions


async def list_credit_prices(
    session: AsyncSession,
    query: CreditPriceQuery,
) -> tuple[list[CreditPrice], int]:
    """Read one offset-based credit price page and the matching total count.

    价格表行数有限，页码分页 + total 足够；无需游标。按 updated_at 倒序，
    与原有 list_credit_prices 端点排序保持一致，避免既有 UI 的默认顺序跳变。
    """
    conditions = _credit_price_query_conditions(query)
    statement = (
        select(CreditPrice)
        .where(*conditions)
        .order_by(CreditPrice.updated_at.desc())
        .offset(max(query.skip, 0))
        .limit(query.limit)
    )
    rows = list((await session.scalars(statement)).all())
    total = await session.scalar(select(func.count()).select_from(CreditPrice).where(*conditions))
    return rows, int(total or 0)


def _query_conditions(query: UserLedgerQuery | AdminLedgerQuery) -> list[Any]:
    conditions: list[Any] = []
    if query.since is not None:
        conditions.append(CreditLedger.created_at >= query.since)
    if query.until is not None:
        conditions.append(CreditLedger.created_at <= query.until)
    if query.cursor_created_at is not None and query.cursor_id is not None:
        conditions.append(
            or_(
                CreditLedger.created_at < query.cursor_created_at,
                and_(CreditLedger.created_at == query.cursor_created_at, CreditLedger.id < query.cursor_id),
            )
        )
    return conditions


def _ledger_item(ledger: CreditLedger, usage_status: str | None) -> LedgerItem:
    metadata = ledger.metadata_snapshot
    pricing = ledger.pricing_snapshot
    return LedgerItem(
        id=ledger.id,
        user_id=ledger.user_id,
        amount=ledger.amount,
        balance_before=ledger.balance_before,
        balance_after=ledger.balance_after,
        entry_type=ledger.entry_type,
        reason_code=ledger.reason_code,
        note=ledger.note,
        user_name_snapshot=ledger.user_name_snapshot,
        user_email_snapshot=ledger.user_email_snapshot,
        operator_id=ledger.operator_id,
        operator_name_snapshot=ledger.operator_name_snapshot,
        operator_email_snapshot=ledger.operator_email_snapshot,
        request_source=ledger.request_source,
        request_id=ledger.request_id,
        service_type=ledger.service_type,
        resource_id=ledger.resource_id,
        action=ledger.action,
        usage_status=usage_status,
        pricing_snapshot=dict(pricing) if isinstance(pricing, dict) else None,
        metadata_snapshot=dict(metadata) if isinstance(metadata, dict) else None,
        created_at=ledger.created_at,
    )


async def list_ledger(
    session: AsyncSession,
    query: UserLedgerQuery | AdminLedgerQuery,
    *,
    user_id: str | None = None,
) -> tuple[tuple[LedgerItem, ...], LedgerCursor | None]:
    """Read a bounded descending keyset page without exposing ledger mutation operations."""
    conditions = _query_conditions(query)
    if user_id is not None:
        conditions.append(CreditLedger.user_id == user_id)
    if isinstance(query, UserLedgerQuery):
        conditions.extend(_user_ledger_conditions(query))
    if isinstance(query, AdminLedgerQuery):
        conditions.extend(_admin_ledger_conditions(query))

    statement = (
        select(CreditLedger, CreditUsage.status)
        .outerjoin(CreditUsage, CreditUsage.id == CreditLedger.usage_id)
        .where(*conditions)
        .order_by(CreditLedger.created_at.desc(), CreditLedger.id.desc())
        .limit(query.limit + 1)
    )
    ledger_rows: Sequence[tuple[CreditLedger, str | None]] = (await session.execute(statement)).all()
    has_next_page = len(ledger_rows) > query.limit
    page_rows = ledger_rows[: query.limit]
    next_cursor = None
    if has_next_page and page_rows:
        last = page_rows[-1][0]
        next_cursor = LedgerCursor(created_at=last.created_at, id=last.id)
    return tuple(_ledger_item(ledger, usage_status) for ledger, usage_status in page_rows), next_cursor


def _user_ledger_conditions(query: UserLedgerQuery) -> list:
    if query.category == 'income':
        return [CreditLedger.amount > 0]
    if query.category == 'consumption':
        return [CreditLedger.entry_type == 'consumption']
    if query.category == 'adjustment':
        return [CreditLedger.entry_type.in_(('admin_adjustment', 'system_adjustment'))]
    return []


def _admin_ledger_conditions(query: AdminLedgerQuery) -> list:
    filters = (
        (CreditLedger.user_id, query.user_id),
        (CreditLedger.entry_type, query.entry_type),
        (CreditLedger.reason_code, query.reason_code),
        (CreditLedger.service_type, query.service_type),
        (CreditLedger.resource_id, query.resource_id),
        (CreditLedger.action, query.action),
    )
    return [column == value for column, value in filters if value is not None]


async def list_admin_ledger_page(
    session: AsyncSession,
    query: AdminLedgerQuery,
) -> tuple[tuple[LedgerItem, ...], int]:
    """Read one offset-based admin ledger page and the matching total count.

    前端管理员流水用页码分页（可跳页、显示总数），因此用 skip/offset 而非游标。
    条件构造与 list_ledger 保持一致，避免两处分叉；唯一差异是去掉了 limit+1
    的“探下一页”技巧，改用单独的计数查询给出 total。
    """
    conditions = _query_conditions(query)
    for column, value in (
        (CreditLedger.user_id, query.user_id),
        (CreditLedger.entry_type, query.entry_type),
        (CreditLedger.reason_code, query.reason_code),
        (CreditLedger.service_type, query.service_type),
        (CreditLedger.resource_id, query.resource_id),
        (CreditLedger.action, query.action),
    ):
        if value is not None:
            conditions.append(column == value)

    statement = (
        select(CreditLedger, CreditUsage.status)
        .outerjoin(CreditUsage, CreditUsage.id == CreditLedger.usage_id)
        .where(*conditions)
        .order_by(CreditLedger.created_at.desc(), CreditLedger.id.desc())
        .offset(max(query.skip, 0))
        .limit(query.limit)
    )
    ledger_rows: Sequence[tuple[CreditLedger, str | None]] = (await session.execute(statement)).all()
    total = await session.scalar(select(func.count()).select_from(CreditLedger).where(*conditions))
    return tuple(_ledger_item(ledger, usage_status) for ledger, usage_status in ledger_rows), int(total or 0)


__all__ = [
    'claim_usage_placeholder',
    'get_balance_if_exists',
    'get_enabled_price',
    'get_or_create_account',
    'get_usage_by_idempotency_key',
    'insert_ledger',
    'list_admin_ledger_page',
    'list_credit_prices',
    'list_ledger',
    'update_account_balance',
]
