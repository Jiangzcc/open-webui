from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from time import time
from typing import Literal
from urllib.parse import urlsplit
from uuid import uuid4

from open_webui.models.users import User
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from .compat import ImageBillingContext
from .constants import (
    MAX_IDEMPOTENCY_KEY_LENGTH,
    MAX_PROVIDER_ERROR_CODE_LENGTH,
    MAX_PROVIDER_ERROR_SUMMARY_LENGTH,
    MAX_USAGE_RESULT_URL_LENGTH,
    MAX_USAGE_RESULT_URLS,
)
from .db import credit_session
from .errors import CreditError
from .metrics import credit_metrics
from .models import CreditAccount, CreditLedger, CreditUsage
from .pricing import PriceQuote, compute_price
from .repository import (
    claim_usage_placeholder,
    get_enabled_price,
    get_or_create_account,
    get_usage_by_idempotency_key,
    insert_ledger,
    list_ledger,
    update_account_balance,
)
from .schemas import (
    AdjustmentRequest,
    AdminLedgerQuery,
    CompensationRequest,
    Page,
    ReconciliationItem,
    ReconciliationPage,
    ReconciliationQuery,
    RequestAuditContext,
    UserLedgerQuery,
    UserSnapshot,
)

_SECONDS_PER_YEAR = 365 * 24 * 60 * 60


@dataclass(frozen=True)
class BeginUsageResult:
    usage: CreditUsage
    outcome: Literal['new', 'processing', 'succeeded', 'failed', 'unknown']


@dataclass(frozen=True)
class SafeProviderError:
    code: str
    summary: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.code, str)
            or re.fullmatch(
                rf'[A-Za-z][A-Za-z0-9_.-]{{0,{MAX_PROVIDER_ERROR_CODE_LENGTH - 1}}}',
                self.code,
            )
            is None
        ):
            raise ValueError('provider error code must be a bounded canonical string')
        if not isinstance(self.summary, str):
            raise ValueError('provider error summary must be a string')
        safe_summary = ''.join(char for char in self.summary if ord(char) >= 32 and ord(char) != 127)
        object.__setattr__(self, 'summary', safe_summary[:MAX_PROVIDER_ERROR_SUMMARY_LENGTH])


def _now() -> int:
    return int(time())


async def _current_user_snapshot(session: AsyncSession, target_id: str) -> UserSnapshot:
    row = await session.execute(select(User.id, User.name, User.email).where(User.id == target_id))
    user = row.one_or_none()
    if user is None:
        raise CreditError(code='invalid_adjustment', context={'reason': 'target_user_not_found'})
    return UserSnapshot(id=user.id, name=user.name, email=user.email)


async def _current_user_for_usage(session: AsyncSession, user_id: str) -> tuple[UserSnapshot, str]:
    row = await session.execute(select(User.id, User.name, User.email, User.role).where(User.id == user_id))
    user = row.one_or_none()
    if user is None:
        raise CreditError(code='invalid_adjustment', context={'reason': 'target_user_not_found'})
    return UserSnapshot(id=user.id, name=user.name, email=user.email), user.role


async def _lock_and_verify_account_matches_ledger(session: AsyncSession, account_id: str) -> CreditAccount:
    account = await session.scalar(select(CreditAccount).where(CreditAccount.id == account_id).with_for_update())
    if account is None:
        credit_metrics.consistency_anomaly()
        raise CreditError(code='credit_service_unavailable', context={'reason': 'account_missing'})
    ledger_total = await session.scalar(
        select(func.coalesce(func.sum(CreditLedger.amount), 0)).where(CreditLedger.account_id == account.id)
    )
    if int(ledger_total) != account.balance:
        credit_metrics.consistency_anomaly()
        raise CreditError(code='credit_service_unavailable', context={'reason': 'account_ledger_mismatch'})
    return account


def _validate_idempotency_key(value: str) -> None:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= MAX_IDEMPOTENCY_KEY_LENGTH
        or any(not '\x20' <= char <= '\x7e' for char in value)
    ):
        raise CreditError(code='invalid_adjustment', context={'reason': 'invalid_idempotency_key'})


def _request_snapshot(context: ImageBillingContext) -> dict[str, object]:
    return {'request_hash': context.request_hash, 'dimensions': dict(context.dimensions)}


def _pricing_snapshot(quote: PriceQuote) -> dict[str, object]:
    return {
        'service_type': quote.service_type,
        'resource_id': quote.resource_id,
        'action': quote.action,
        'base_price': quote.base_price,
        'factors': [
            {'key': factor.key, 'value': factor.value, 'multiplier': factor.multiplier} for factor in quote.factors
        ],
        'raw_price': quote.raw_price,
        'charged_credits': quote.charged_credits,
        'rounding': 'ceiling',
    }


def _usage_metric_attributes(context: ImageBillingContext) -> dict[str, str]:
    return {
        'model': context.resource_id,
        'action': context.action,
        'channel': context.channel,
    }


def _existing_usage_result(usage: CreditUsage, request_hash: str) -> BeginUsageResult:
    attributes = {'model': usage.resource_id, 'action': usage.action, 'channel': usage.channel}
    if usage.request_hash != request_hash:
        credit_metrics.idempotency_conflict(**attributes)
        raise CreditError(code='idempotency_key_conflict')
    credit_metrics.idempotency_hit(**attributes)
    outcome: Literal['processing', 'succeeded', 'failed', 'unknown']
    if usage.status in ('debited', 'invoking'):
        outcome = 'processing'
    else:
        outcome = usage.status
    return BeginUsageResult(usage=usage, outcome=outcome)


async def begin_image_usage(
    session: AsyncSession,
    user: UserSnapshot,
    context: ImageBillingContext,
    idempotency_key: str,
) -> BeginUsageResult:
    """Atomically claim an image request and record its prepaid credit consumption."""
    _validate_idempotency_key(idempotency_key)
    created_at = _now()

    async with session.begin():
        current_user, _role = await _current_user_for_usage(session, user.id)
        usage_values = {
            'id': str(uuid4()),
            'user_id': current_user.id,
            'user_name_snapshot': current_user.name,
            'user_email_snapshot': current_user.email,
            'idempotency_key': idempotency_key,
            'request_hash': context.request_hash,
            'service_type': context.service_type,
            'resource_id': context.resource_id,
            'action': context.action,
            'channel': context.channel,
            'status': 'debited',
            'exempt': False,
            'charged_credits': 0,
            'request_snapshot': _request_snapshot(context),
            'created_at': created_at,
            'updated_at': created_at,
        }
        usage = await claim_usage_placeholder(session, usage_values)
        if usage is None:
            existing = await get_usage_by_idempotency_key(session, current_user.id, idempotency_key)
            if existing is None:
                raise RuntimeError('credit usage was not persisted after idempotency conflict')
            return _existing_usage_result(existing, context.request_hash)

        try:
            quote = compute_price(
                await get_enabled_price(
                    session,
                    context.service_type,
                    context.resource_id,
                    context.action,
                ),
                context.dimensions,
            )
        except CreditError as error:
            credit_metrics.debit_failed(
                **_usage_metric_attributes(context),
                error_code=error.code,
            )
            raise
        account = await get_or_create_account(session, current_user, now=created_at)
        account = await _lock_and_verify_account_matches_ledger(session, account.id)
        balance = await update_account_balance(session, account, -quote.charged_credits, now=created_at)
        if balance is None:
            credit_metrics.debit_insufficient(**_usage_metric_attributes(context))
            raise CreditError(code='insufficient_credits', context={'required': quote.charged_credits})
        balance_before, balance_after = balance
        pricing_snapshot = _pricing_snapshot(quote)
        ledger = await insert_ledger(
            session,
            {
                'id': str(uuid4()),
                'account_id': account.id,
                'usage_id': usage.id,
                'user_id': current_user.id,
                'user_name_snapshot': current_user.name,
                'user_email_snapshot': current_user.email,
                'amount': -quote.charged_credits,
                'balance_before': balance_before,
                'balance_after': balance_after,
                'entry_type': 'consumption',
                'request_source': 'api' if context.channel == 'api' else 'web',
                'request_id': idempotency_key,
                'idempotency_key': idempotency_key,
                'service_type': context.service_type,
                'resource_id': context.resource_id,
                'action': context.action,
                'pricing_snapshot': pricing_snapshot,
                'created_at': created_at,
            },
        )
        usage.ledger_id = ledger.id
        usage.charged_credits = quote.charged_credits
        usage.pricing_snapshot = pricing_snapshot
        await session.flush()
        result = BeginUsageResult(usage=usage, outcome='new')
    credit_metrics.debit_succeeded(
        **_usage_metric_attributes(context),
        charged_credits=quote.charged_credits,
    )
    credit_metrics.usage_status(status='debited', **_usage_metric_attributes(context))
    return result


def _safe_result_urls(urls: Sequence[str]) -> list[str]:
    if isinstance(urls, (str, bytes)) or not 1 <= len(urls) <= MAX_USAGE_RESULT_URLS:
        raise CreditError(code='provider_failed', context={'reason': 'invalid_provider_result'})
    normalized: list[str] = []
    for url in urls:
        if not isinstance(url, str) or not url or len(url) > MAX_USAGE_RESULT_URL_LENGTH:
            raise CreditError(code='provider_failed', context={'reason': 'invalid_provider_result'})
        if any(ord(char) < 32 or ord(char) == 127 for char in url) or '\\' in url or url.startswith('//'):
            raise CreditError(code='provider_failed', context={'reason': 'invalid_provider_result'})
        parsed = urlsplit(url)
        file_id = url.removeprefix('/api/v1/files/').removesuffix('/content')
        if (
            not url.startswith('/api/v1/files/')
            or not url.endswith('/content')
            or re.fullmatch(r'[A-Za-z0-9_-]{1,128}', file_id) is None
            or parsed.scheme
            or parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise CreditError(code='provider_failed', context={'reason': 'invalid_provider_result'})
        normalized.append(url)
    return normalized


def _safe_error_snapshot(error: SafeProviderError) -> dict[str, str]:
    summary = ''.join(char for char in error.summary if char.isprintable())
    return {'code': error.code, 'summary': summary[:MAX_PROVIDER_ERROR_SUMMARY_LENGTH]}


async def _update_usage_status(
    usage_id: str,
    allowed_statuses: tuple[str, ...],
    values: dict[str, object],
) -> int:
    async with credit_session() as session, session.begin():
        result = await session.execute(
            update(CreditUsage)
            .where(CreditUsage.id == usage_id, CreditUsage.status.in_(allowed_statuses))
            .values(**values, updated_at=_now())
        )
        return result.rowcount


async def mark_usage_invoking(usage_id: str) -> int:
    """Transition a committed prepaid usage from debited to invoking."""
    changed = await _update_usage_status(
        usage_id,
        ('debited',),
        {'status': 'invoking', 'invocation_started_at': _now()},
    )
    if changed == 1:
        credit_metrics.usage_status(status='invoking')
    return changed


async def mark_usage_succeeded_in_session(
    session: AsyncSession,
    usage_id: str,
    urls: Sequence[str],
) -> int:
    """Transition an invoking usage to succeeded within the caller's transaction.

    Unlike ``mark_usage_succeeded``, this neither opens nor commits a session; the
    caller owns the enclosing transaction so creation finalization and the success
    transition commit atomically.
    """
    safe_urls = _safe_result_urls(urls)
    result = await session.execute(
        update(CreditUsage)
        .where(CreditUsage.id == usage_id, CreditUsage.status == 'invoking')
        .values(
            status='succeeded',
            result_snapshot={'urls': safe_urls},
            completed_at=_now(),
            updated_at=_now(),
        )
    )
    return result.rowcount


async def mark_usage_succeeded(usage_id: str, urls: Sequence[str]) -> int:
    """Persist bounded internal result URLs only while a usage is invoking."""
    async with credit_session() as session, session.begin():
        changed = await mark_usage_succeeded_in_session(session, usage_id, urls)
    if changed == 1:
        credit_metrics.usage_status(status='succeeded')
    return changed


async def mark_usage_failed(
    usage_id: str,
    error: SafeProviderError,
    *,
    restore_prepaid: bool = False,
) -> int:
    """Fail an invoking usage and optionally restore its prepaid credits atomically.

    Provider failures remain prepaid by default for the existing reconciliation
    workflow. An explicit user cancellation is different: no completed result is
    delivered, so the cancellation path writes one idempotent compensating ledger
    row in the same transaction as the terminal usage state.
    """
    now = _now()
    async with credit_session() as session, session.begin():
        usage = await session.scalar(select(CreditUsage).where(CreditUsage.id == usage_id).with_for_update())
        if usage is None or usage.status != 'invoking':
            return 0

        if restore_prepaid and not usage.exempt and usage.charged_credits > 0 and usage.ledger_id:
            existing_refund = await session.scalar(
                select(CreditLedger).where(CreditLedger.related_ledger_id == usage.ledger_id)
            )
            if existing_refund is None:
                consumption = await session.scalar(select(CreditLedger).where(CreditLedger.id == usage.ledger_id))
                if consumption is None:
                    credit_metrics.consistency_anomaly()
                    raise CreditError(
                        code='credit_service_unavailable',
                        context={'reason': 'consumption_ledger_missing'},
                    )
                account = await _lock_and_verify_account_matches_ledger(session, consumption.account_id)
                balance = await update_account_balance(
                    session,
                    account,
                    usage.charged_credits,
                    now=now,
                )
                if balance is None:
                    raise CreditError(
                        code='credit_service_unavailable',
                        context={'reason': 'refund_balance_limit_exceeded'},
                    )
                balance_before, balance_after = balance
                cancellation_key = f'cancel:{usage.id}'[:MAX_IDEMPOTENCY_KEY_LENGTH]
                await insert_ledger(
                    session,
                    {
                        'id': str(uuid4()),
                        'account_id': account.id,
                        'usage_id': usage.id,
                        'user_id': usage.user_id,
                        'user_name_snapshot': usage.user_name_snapshot,
                        'user_email_snapshot': usage.user_email_snapshot,
                        'amount': usage.charged_credits,
                        'balance_before': balance_before,
                        'balance_after': balance_after,
                        'entry_type': 'system_adjustment',
                        'reason_code': 'accounting_correction',
                        'note': 'Generation cancelled before completion',
                        'request_source': 'internal_admin',
                        'request_id': cancellation_key,
                        'idempotency_key': cancellation_key,
                        'service_type': usage.service_type,
                        'resource_id': usage.resource_id,
                        'action': usage.action,
                        'pricing_snapshot': usage.pricing_snapshot,
                        'metadata_snapshot': {'reason': 'generation_cancelled'},
                        'related_ledger_id': usage.ledger_id,
                        'created_at': now,
                    },
                )

        usage.status = 'failed'
        usage.error_snapshot = _safe_error_snapshot(error)
        usage.completed_at = now
        usage.updated_at = now
        await session.flush()
        changed = 1
    if changed == 1:
        credit_metrics.usage_status(status='failed')
    return changed


async def mark_stale_usage_unknown(cutoff: int) -> int:
    """Mark stale unfinished usages unknown without changing their prepaid balance."""
    async with credit_session() as session, session.begin():
        result = await session.execute(
            update(CreditUsage)
            .where(
                CreditUsage.status.in_(('debited', 'invoking')),
                CreditUsage.updated_at < cutoff,
            )
            .values(status='unknown', updated_at=_now(), completed_at=_now())
        )
        changed = result.rowcount
        if changed > 0:
            credit_metrics.long_pending(count=changed)
            credit_metrics.usage_status(status='unknown', count=changed)
        return changed


async def get_balance(session: AsyncSession, user: UserSnapshot) -> int:
    """Lazily create an account and return its non-negative integer balance."""
    if session.in_transaction():
        account = await get_or_create_account(session, user)
        return account.balance
    async with session.begin():
        account = await get_or_create_account(session, user)
        return account.balance


async def adjust_balance(
    session: AsyncSession,
    target: UserSnapshot,
    operator: UserSnapshot,
    request: AdjustmentRequest,
    audit: RequestAuditContext,
) -> CreditLedger:
    """Atomically adjust a live user's account and append a corresponding immutable ledger row."""
    signed_amount = request.amount if request.direction == 'increase' else -request.amount
    created_at = _now()
    metadata_snapshot = (
        {'remote_address_hash': audit.remote_address_hash} if audit.remote_address_hash is not None else None
    )

    async with session.begin():
        current_target = await _current_user_snapshot(session, target.id)
        account = await get_or_create_account(session, current_target, now=created_at)
        balance = await update_account_balance(session, account, signed_amount, now=created_at)
        if balance is None:
            if signed_amount > 0:
                raise CreditError(code='invalid_adjustment', context={'reason': 'balance_limit_exceeded'})
            raise CreditError(code='insufficient_credits', context={'required': request.amount})
        balance_before, balance_after = balance
        ledger = await insert_ledger(
            session,
            {
                'id': str(uuid4()),
                'account_id': account.id,
                'user_id': current_target.id,
                'user_name_snapshot': current_target.name,
                'user_email_snapshot': current_target.email,
                'amount': signed_amount,
                'balance_before': balance_before,
                'balance_after': balance_after,
                'entry_type': 'admin_adjustment',
                'reason_code': request.reason_code,
                'note': request.note,
                'operator_id': operator.id,
                'operator_name_snapshot': operator.name,
                'operator_email_snapshot': operator.email,
                'request_source': audit.source,
                'request_id': audit.request_id,
                'metadata_snapshot': metadata_snapshot,
                'created_at': created_at,
            },
        )
    credit_metrics.admin_adjustment(amount=signed_amount)
    return ledger


async def list_user_ledger(
    session: AsyncSession,
    user_id: str,
    query: UserLedgerQuery,
) -> Page:
    """Return only the caller's supplied user id ledger rows, hard-clamped to one year."""
    now = _now()
    floor = now - _SECONDS_PER_YEAR
    effective_since = max(query.since or floor, floor)
    bounded_query = query.model_copy(update={'since': effective_since})
    items, next_cursor = await list_ledger(session, bounded_query, user_id=user_id)
    return Page(items=items, next_cursor=next_cursor)


async def list_admin_ledger(session: AsyncSession, query: AdminLedgerQuery) -> Page:
    """Return a permanently retained, bounded and filtered administrative ledger page."""
    items, next_cursor = await list_ledger(session, query)
    return Page(items=items, next_cursor=next_cursor)


async def list_reconciliation_cases(
    session: AsyncSession,
    query: ReconciliationQuery,
) -> ReconciliationPage:
    refund = aliased(CreditLedger)
    conditions = [
        CreditUsage.status.in_(('failed', 'unknown')),
        CreditUsage.exempt.is_(False),
        CreditUsage.charged_credits > 0,
        CreditUsage.ledger_id.is_not(None),
    ]
    if query.status is not None:
        conditions.append(CreditUsage.status == query.status)
    # compensated 过滤依赖 outerjoin 的 refund 别名：refund.id 非空表示已存在
    # manual_refund 补偿账本，为空则尚未补偿。True=只看已补偿，False=只看待补偿。
    if query.compensated is True:
        conditions.append(refund.id.is_not(None))
    elif query.compensated is False:
        conditions.append(refund.id.is_(None))
    if query.user_id is not None:
        conditions.append(CreditUsage.user_id == query.user_id)

    # compensated 过滤引用了 refund 别名；计数查询必须带上与行查询相同的 outerjoin，
    # 否则 WHERE 中的 refund.id 会引用未连接的表。未筛选补偿状态时不加 join，
    # 保持原有计数计划不变。
    refund_join = and_(
        refund.related_ledger_id == CreditUsage.ledger_id,
        refund.reason_code == 'manual_refund',
    )
    count_select = select(func.count()).select_from(CreditUsage)
    if query.compensated is not None:
        count_select = count_select.outerjoin(refund, refund_join)
    total = int(await session.scalar(count_select.where(*conditions)) or 0)
    rows = (
        await session.execute(
            select(CreditUsage, refund.id)
            .outerjoin(refund, refund_join)
            .where(*conditions)
            .order_by(CreditUsage.updated_at.desc(), CreditUsage.id.desc())
            .offset(query.skip)
            .limit(query.limit)
        )
    ).all()
    items = []
    for usage, refund_id in rows:
        error = usage.error_snapshot if isinstance(usage.error_snapshot, dict) else {}
        items.append(
            ReconciliationItem(
                usage_id=usage.id,
                user_id=usage.user_id,
                user_name_snapshot=usage.user_name_snapshot,
                user_email_snapshot=usage.user_email_snapshot,
                status=usage.status,
                charged_credits=usage.charged_credits,
                resource_id=usage.resource_id,
                action=usage.action,
                channel=usage.channel,
                error_code=error.get('code') if isinstance(error.get('code'), str) else None,
                error_summary=error.get('summary') if isinstance(error.get('summary'), str) else None,
                consumption_ledger_id=usage.ledger_id,
                compensation_ledger_id=refund_id,
                created_at=usage.created_at,
                completed_at=usage.completed_at,
            )
        )
    return ReconciliationPage(items=tuple(items), total=total)


async def compensate_reconciliation_case(
    session: AsyncSession,
    usage_id: str,
    operator: UserSnapshot,
    request: CompensationRequest,
    audit: RequestAuditContext,
) -> tuple[CreditLedger, bool]:
    now = _now()
    async with session.begin():
        usage = await session.scalar(select(CreditUsage).where(CreditUsage.id == usage_id).with_for_update())
        if usage is None:
            raise CreditError(code='invalid_adjustment', context={'reason': 'usage_not_found'})
        if usage.status not in {'failed', 'unknown'}:
            raise CreditError(code='invalid_adjustment', context={'reason': 'usage_not_reconcilable'})
        if usage.exempt or usage.charged_credits <= 0 or not usage.ledger_id:
            raise CreditError(code='invalid_adjustment', context={'reason': 'usage_not_charged'})
        existing = await session.scalar(select(CreditLedger).where(CreditLedger.related_ledger_id == usage.ledger_id))
        if existing is not None:
            return existing, False

        target = UserSnapshot(
            id=usage.user_id,
            name=usage.user_name_snapshot,
            email=usage.user_email_snapshot,
        )
        account = await get_or_create_account(session, target, now=now)
        account = await _lock_and_verify_account_matches_ledger(session, account.id)
        balance = await update_account_balance(session, account, usage.charged_credits, now=now)
        if balance is None:
            raise CreditError(code='invalid_adjustment', context={'reason': 'balance_limit_exceeded'})
        balance_before, balance_after = balance
        ledger = await insert_ledger(
            session,
            {
                'id': str(uuid4()),
                'account_id': account.id,
                'usage_id': usage.id,
                'user_id': usage.user_id,
                'user_name_snapshot': usage.user_name_snapshot,
                'user_email_snapshot': usage.user_email_snapshot,
                'amount': usage.charged_credits,
                'balance_before': balance_before,
                'balance_after': balance_after,
                'entry_type': 'admin_adjustment',
                'reason_code': 'manual_refund',
                'note': request.note,
                'operator_id': operator.id,
                'operator_name_snapshot': operator.name,
                'operator_email_snapshot': operator.email,
                'request_source': audit.source,
                'request_id': audit.request_id,
                'idempotency_key': f'reconciliation:{usage.id}',
                'service_type': usage.service_type,
                'resource_id': usage.resource_id,
                'action': usage.action,
                'pricing_snapshot': usage.pricing_snapshot,
                'metadata_snapshot': {'reconciliation_usage_id': usage.id},
                'related_ledger_id': usage.ledger_id,
                'created_at': now,
            },
        )
    credit_metrics.admin_adjustment(amount=usage.charged_credits)
    return ledger, True


__all__ = [
    'BeginUsageResult',
    'SafeProviderError',
    'adjust_balance',
    'begin_image_usage',
    'get_balance',
    'list_admin_ledger',
    'list_reconciliation_cases',
    'compensate_reconciliation_case',
    'list_user_ledger',
    'mark_stale_usage_unknown',
    'mark_usage_failed',
    'mark_usage_invoking',
    'mark_usage_succeeded',
    'mark_usage_succeeded_in_session',
]
