from __future__ import annotations

import asyncio
import os
import time
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import open_webui.extensions.credits.repository as credit_repository
import pytest
import pytest_asyncio
from fastapi.encoders import jsonable_encoder
from open_webui.extensions.credits.constants import MAX_CREDIT_VALUE
from open_webui.extensions.credits.db import CreditBase
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.models import CreditAccount, CreditLedger, CreditUsage
from open_webui.extensions.credits.repository import get_or_create_account, update_account_balance
from open_webui.extensions.credits.schemas import (
    AdjustmentRequest,
    AdminLedgerQuery,
    CreditPriceQuery,
    ReconciliationQuery,
    RequestAuditContext,
    UserLedgerQuery,
    UserSnapshot,
)
from open_webui.extensions.credits.service import (
    adjust_balance,
    get_balance,
    list_admin_ledger,
    list_user_ledger,
)
from open_webui.internal.db import _make_async_url
from open_webui.models.users import User
from pydantic import ValidationError
from sqlalchemy import event, func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def service_database(tmp_path: Path):
    database_path = tmp_path / 'service.sqlite'
    engine = create_async_engine(f'sqlite+aiosqlite:///{database_path}', connect_args={'timeout': 10})

    @event.listens_for(engine.sync_engine, 'connect')
    def set_busy_timeout(connection, _record) -> None:
        connection.execute('PRAGMA busy_timeout = 10000')

    async with engine.begin() as connection:
        await connection.run_sync(User.__table__.create)
        await connection.run_sync(CreditBase.metadata.create_all)

    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield sessions
    finally:
        await engine.dispose()


def audit(request_id: str = 'request-1') -> RequestAuditContext:
    return RequestAuditContext(source='internal_admin', request_id=request_id, remote_address_hash='a0' * 32)


@asynccontextmanager
async def credit_session_for_test(sessions):
    async with sessions() as session:
        yield session


def adjustment(
    direction: str,
    amount: int,
    reason_code: str = 'accounting_correction',
    note: str | None = None,
) -> AdjustmentRequest:
    return AdjustmentRequest(direction=direction, amount=amount, reason_code=reason_code, note=note)


from .service_test_support import add_price, create_user


async def add_ledger(
    sessions,
    *,
    user_id: str,
    entry_id: str,
    created_at: int,
    entry_type: str = 'admin_adjustment',
    reason_code: str = 'accounting_correction',
    service_type: str | None = None,
    resource_id: str | None = None,
    action: str | None = None,
    metadata_snapshot: dict[str, object] | None = None,
    user_name_snapshot: str | None = None,
    user_email_snapshot: str | None = None,
) -> None:
    async with sessions() as session, session.begin():
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user_id))
        if account is None:
            account = CreditAccount(
                id=f'account-{user_id}',
                user_id=user_id,
                balance=10,
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(account)
            await session.flush()
        session.add(
            CreditLedger(
                id=entry_id,
                account_id=account.id,
                user_id=user_id,
                amount=0,
                balance_before=account.balance,
                balance_after=account.balance,
                entry_type=entry_type,
                reason_code=reason_code,
                request_source='internal_admin',
                request_id=f'request-{entry_id}',
                service_type=service_type,
                resource_id=resource_id,
                action=action,
                metadata_snapshot=metadata_snapshot,
                user_name_snapshot=user_name_snapshot,
                user_email_snapshot=user_email_snapshot,
                created_at=created_at,
            )
        )


def test_user_snapshot_enforces_persisted_identity_boundaries() -> None:
    assert UserSnapshot(id='u' * 128, name='n' * 256, email='e' * 320).id == 'u' * 128
    for values in (
        {'id': '', 'name': 'Name', 'email': 'email@example.test'},
        {'id': 'u' * 129, 'name': 'Name', 'email': 'email@example.test'},
        {'id': 'user-1', 'name': 'n' * 257, 'email': 'email@example.test'},
        {'id': 'user-1', 'name': 'Name', 'email': 'e' * 321},
    ):
        with pytest.raises(ValueError):
            UserSnapshot(**values)


@pytest.mark.asyncio
async def test_account_repository_rejects_unknown_dialect_and_zero_update(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'user-1')
    async with service_database() as session, session.begin():
        with monkeypatch.context() as patch:
            patch.setattr(session.get_bind().dialect, 'name', 'unsupported-credit-test')
            with pytest.raises(RuntimeError, match='unsupported credit account database dialect'):
                await get_or_create_account(session, user)

        account = await get_or_create_account(session, user)
        with pytest.raises(ValueError, match='signed amount must not be zero'):
            await update_account_balance(session, account, 0)


@pytest.mark.asyncio
async def test_claim_usage_placeholder_returns_none_after_postgresql_unique_conflict(monkeypatch) -> None:
    values = {
        'id': 'usage-1',
        'user_id': 'user-1',
        'idempotency_key': 'key-1',
        'request_hash': 'a' * 64,
        'service_type': 'image',
        'resource_id': 'model-a',
        'action': 'text-to-image',
        'channel': 'web',
        'status': 'debited',
        'exempt': False,
        'charged_credits': 0,
        'created_at': 1,
        'updated_at': 1,
    }

    class FailingNestedTransaction:
        async def __aenter__(self) -> None:
            return None

        async def __aexit__(self, *args) -> None:
            raise credit_repository.IntegrityError('statement', {}, Exception('unique violation'))

    class PostgresSession:
        def get_bind(self):
            return SimpleNamespace(dialect=SimpleNamespace(name='postgresql'))

        def begin_nested(self) -> FailingNestedTransaction:
            return FailingNestedTransaction()

        def add(self, _usage) -> None:
            return None

        async def flush(self) -> None:
            raise AssertionError('flush should not run when savepoint entry fails')

    result = await credit_repository.claim_usage_placeholder(PostgresSession(), values)

    assert result is None


@pytest.mark.asyncio
async def test_claim_usage_placeholder_raises_when_sqlite_claim_cannot_be_loaded(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'usage-load-user')
    values = {
        'id': 'usage-load-failure',
        'user_id': user.id,
        'idempotency_key': 'usage-load-key',
        'request_hash': 'a' * 64,
        'service_type': 'image',
        'resource_id': 'model-a',
        'action': 'text-to-image',
        'channel': 'web',
        'status': 'debited',
        'exempt': False,
        'charged_credits': 0,
        'created_at': 1,
        'updated_at': 1,
    }

    async with service_database() as session, session.begin():
        original_get = session.get

        async def missing_usage(model, identity, *args, **kwargs):
            if model is CreditUsage:
                return None
            return await original_get(model, identity, *args, **kwargs)

        monkeypatch.setattr(session, 'get', missing_usage)
        with pytest.raises(RuntimeError, match='credit usage was not persisted after claim'):
            await credit_repository.claim_usage_placeholder(session, values)


@pytest.mark.asyncio
async def test_postgresql_placeholder_savepoint_returns_claimed_usage() -> None:
    values = {
        'id': 'postgres-usage',
        'user_id': 'user-1',
        'idempotency_key': 'postgres-key',
        'request_hash': 'a' * 64,
        'service_type': 'image',
        'resource_id': 'model-a',
        'action': 'text-to-image',
        'channel': 'web',
        'status': 'debited',
        'exempt': False,
        'charged_credits': 0,
        'created_at': 1,
        'updated_at': 1,
    }

    class SuccessfulNestedTransaction:
        async def __aenter__(self) -> None:
            return None

        async def __aexit__(self, *args) -> None:
            return None

    class PostgresSession:
        def __init__(self) -> None:
            self.added_usage = None

        def get_bind(self):
            return SimpleNamespace(dialect=SimpleNamespace(name='postgresql'))

        def begin_nested(self) -> SuccessfulNestedTransaction:
            return SuccessfulNestedTransaction()

        def add(self, usage) -> None:
            self.added_usage = usage

        async def flush(self) -> None:
            return None

    session = PostgresSession()

    assert credit_repository._dialect_insert(session) is postgresql_insert
    usage = await credit_repository.claim_usage_placeholder(session, values)
    assert usage is session.added_usage
    assert usage.id == values['id']


@pytest.mark.asyncio
async def test_update_account_balance_raises_if_account_disappears_after_atomic_update(
    service_database, monkeypatch
) -> None:
    user = await create_user(service_database, 'disappearing-account-user')
    async with service_database() as session, session.begin():
        account = await get_or_create_account(session, user)

        async def missing_balance(*_args, **_kwargs):
            return None

        monkeypatch.setattr(session, 'scalar', missing_balance)
        with pytest.raises(RuntimeError, match='credit account disappeared after balance update'):
            await update_account_balance(session, account, 1)


@pytest.mark.asyncio
async def test_get_balance_uses_existing_caller_transaction(service_database) -> None:
    user = await create_user(service_database, 'user-1')

    async with service_database() as session, session.begin():
        assert await get_balance(session, user) == 0


@pytest.mark.asyncio
async def test_get_balance_creates_zero_balance_account_on_first_view(service_database) -> None:
    user = await create_user(service_database, 'user-1')

    async with service_database() as session:
        assert await get_balance(session, user) == 0
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))

    assert account is not None
    assert account.balance == 0
    assert account.user_name_snapshot == user.name
    assert account.user_email_snapshot == user.email


@pytest.mark.asyncio
async def test_get_or_create_account_raises_when_upsert_does_not_persist(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'user-1')

    async with service_database() as session, session.begin():
        original_scalar = session.scalar

        async def missing_account(statement, *args, **kwargs):
            if 'ext_credit_account' in str(statement):
                return None
            return await original_scalar(statement, *args, **kwargs)

        monkeypatch.setattr(session, 'scalar', missing_account)
        with pytest.raises(RuntimeError, match='credit account was not persisted'):
            await get_or_create_account(session, user)


@pytest.mark.asyncio
async def test_concurrent_first_balance_views_create_one_account(service_database) -> None:
    user = await create_user(service_database, 'user-1')

    async def view_balance() -> int:
        async with service_database() as session:
            return await get_balance(session, user)

    assert await asyncio.gather(view_balance(), view_balance()) == [0, 0]
    async with service_database() as session:
        count = await session.scalar(
            select(func.count()).select_from(CreditAccount).where(CreditAccount.user_id == user.id)
        )
    assert count == 1


@pytest.mark.asyncio
async def test_existing_account_refreshes_current_identity_snapshot(service_database) -> None:
    target = await create_user(service_database, 'user-1', name='Initial Name', email='initial@example.test')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')

    async with service_database() as session:
        await adjust_balance(session, target, operator, adjustment('increase', 1), audit('initial'))
    async with service_database() as session, session.begin():
        await session.execute(
            User.__table__.update()
            .where(User.id == target.id)
            .values(name='Current Name', email='current@example.test')
        )
    async with service_database() as session:
        await adjust_balance(session, target, operator, adjustment('increase', 1), audit('refresh'))
    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == target.id))

    assert account is not None
    assert account.user_name_snapshot == 'Current Name'
    assert account.user_email_snapshot == 'current@example.test'


@pytest.mark.asyncio
async def test_increase_cannot_exceed_credit_balance_ceiling(service_database) -> None:
    target = await create_user(service_database, 'user-1')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')
    async with service_database() as session, session.begin():
        account = await get_or_create_account(session, target)
        await session.execute(
            CreditAccount.__table__.update().where(CreditAccount.id == account.id).values(balance=MAX_CREDIT_VALUE)
        )
        # Keep ledger in sync with the balance so the consistency guard
        # (_lock_and_verify_account_matches_ledger) doesn't reject the call
        # before the ceiling check can fire.
        session.add(
            CreditLedger(
                id='ledger-ceiling-seed',
                account_id=account.id,
                user_id=target.id,
                amount=MAX_CREDIT_VALUE,
                balance_before=0,
                balance_after=MAX_CREDIT_VALUE,
                entry_type='system_adjustment',
                reason_code='offline_recharge',
                request_source='internal_admin',
                request_id='ceiling-seed',
                service_type='credits',
                resource_id=None,
                action='adjust',
                created_at=int(time.time()),
            )
        )

    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await adjust_balance(session, target, operator, adjustment('increase', 1), audit('overflow'))

    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == target.id))
        ledger_count = await session.scalar(select(func.count()).select_from(CreditLedger))
    assert raised.value.code == 'invalid_adjustment'
    assert raised.value.context == {'reason': 'balance_limit_exceeded'}
    assert account is not None
    assert account.balance == MAX_CREDIT_VALUE
    assert ledger_count == 1  # only the seed entry; the overflow increase was rejected


@pytest.mark.asyncio
async def test_concurrent_increases_produce_linear_balance_history(service_database) -> None:
    target = await create_user(service_database, 'user-1')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')

    async def increase(request_id: str) -> None:
        async with service_database() as session:
            await adjust_balance(session, target, operator, adjustment('increase', 1), audit(request_id))

    await asyncio.gather(increase('concurrent-1'), increase('concurrent-2'))

    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == target.id))
        ledgers = list(
            await session.scalars(
                select(CreditLedger).where(CreditLedger.user_id == target.id).order_by(CreditLedger.balance_after)
            )
        )

    assert account is not None
    assert account.balance == 2
    assert [(ledger.balance_before, ledger.balance_after) for ledger in ledgers] == [(0, 1), (1, 2)]


@pytest.mark.asyncio
async def test_adjustment_atomically_records_signed_amount_audit_and_current_user_snapshot(service_database) -> None:
    target = await create_user(service_database, 'user-1', name='Current Name', email='current@example.test')
    stale_target = UserSnapshot(id=target.id, name='Stale Name', email='stale@example.test')
    operator = UserSnapshot(id='admin-1', name='Admin Name', email='admin@example.test')

    async with service_database() as session:
        increased = await adjust_balance(
            session,
            stale_target,
            operator,
            adjustment('increase', 50, 'offline_recharge'),
            audit('increase-1'),
        )
        decreased = await adjust_balance(
            session,
            target,
            operator,
            adjustment('decrease', 20, 'violation_deduction'),
            audit('decrease-1'),
        )

    assert increased.id
    assert (increased.amount, increased.balance_before, increased.balance_after) == (50, 0, 50)
    assert increased.user_name_snapshot == 'Current Name'
    assert increased.user_email_snapshot == 'current@example.test'
    assert increased.operator_id == operator.id
    assert increased.operator_name_snapshot == operator.name
    assert increased.operator_email_snapshot == operator.email
    assert increased.request_source == 'internal_admin'
    assert increased.request_id == 'increase-1'
    assert increased.metadata_snapshot == {'remote_address_hash': 'a0' * 32}
    assert (decreased.amount, decreased.balance_before, decreased.balance_after) == (-20, 50, 30)

    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == target.id))
        ledger_count = await session.scalar(select(func.count()).select_from(CreditLedger))
    assert account is not None
    assert account.balance == 30
    assert ledger_count == 2


@pytest.mark.asyncio
async def test_insufficient_debit_leaves_account_and_ledger_unchanged(service_database) -> None:
    target = await create_user(service_database, 'user-1')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')
    async with service_database() as session:
        await adjust_balance(session, target, operator, adjustment('increase', 10), audit('seed'))
        with pytest.raises(CreditError, match='Insufficient credits') as raised:
            await adjust_balance(session, target, operator, adjustment('decrease', 11), audit('debit'))
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == target.id))
        ledgers = await session.scalars(select(CreditLedger).where(CreditLedger.user_id == target.id))

    assert raised.value.code == 'insufficient_credits'
    assert account is not None
    assert account.balance == 10
    assert len(list(ledgers)) == 1


@pytest.mark.asyncio
async def test_adjustment_metric_is_emitted_after_transaction_exit(service_database, monkeypatch) -> None:
    import open_webui.extensions.credits.service as service

    target = await create_user(service_database, 'metric-order-user')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')
    ordering: list[str] = []
    monkeypatch.setattr(
        service.credit_metrics,
        'admin_adjustment',
        lambda *, amount: ordering.append(f'metric:{amount}'),
    )

    async with service_database() as session:

        @event.listens_for(session.sync_session, 'after_commit')
        def record_commit(_session) -> None:
            ordering.append('committed')

        await service.adjust_balance(session, target, operator, adjustment('increase', 10), audit())

    assert ordering == ['committed', 'metric:10']


@pytest.mark.asyncio
async def test_ledger_insert_failure_rolls_back_balance_update(service_database, monkeypatch) -> None:
    target = await create_user(service_database, 'user-1')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')

    async def fail_insert(*_args, **_kwargs) -> None:
        raise RuntimeError('ledger storage failed')

    monkeypatch.setattr('open_webui.extensions.credits.service.insert_ledger', fail_insert)
    async with service_database() as session:
        with pytest.raises(RuntimeError, match='ledger storage failed'):
            await adjust_balance(session, target, operator, adjustment('increase', 10), audit())

    async with service_database() as session:
        assert await session.scalar(select(func.count()).select_from(CreditAccount)) == 0
        assert await session.scalar(select(func.count()).select_from(CreditLedger)) == 0


@pytest.mark.parametrize(
    'reason_code',
    [
        'offline_recharge',
        'promotion_gift',
        'manual_refund',
        'accounting_correction',
        'violation_deduction',
    ],
)
def test_fixed_adjustment_reasons_do_not_override_explicit_direction(reason_code: str) -> None:
    assert adjustment('increase', 1, reason_code).direction == 'increase'
    assert adjustment('decrease', 1, reason_code).direction == 'decrease'


def test_other_requires_note_and_allows_both_directions() -> None:
    assert adjustment('increase', 1, 'other', note='manual reason').direction == 'increase'
    assert adjustment('decrease', 1, 'other', note='manual reason').direction == 'decrease'
    with pytest.raises(ValidationError):
        adjustment('decrease', 1, 'other')


@pytest.mark.asyncio
async def test_user_ledger_is_clamped_to_one_year_own_records_and_requested_page_size(service_database) -> None:
    target = await create_user(service_database, 'user-1')
    await create_user(service_database, 'user-2')
    now = int(time.time())
    await add_ledger(service_database, user_id=target.id, entry_id='old', created_at=now - (366 * 24 * 60 * 60))
    await add_ledger(service_database, user_id=target.id, entry_id='recent-1', created_at=now - 3)
    await add_ledger(
        service_database,
        user_id=target.id,
        entry_id='recent-2',
        created_at=now - 2,
        metadata_snapshot={'remote_address_hash': 'a0' * 32},
    )
    await add_ledger(service_database, user_id='user-2', entry_id='other-user', created_at=now - 1)

    async with service_database() as session:
        first_page = await list_user_ledger(session, target.id, UserLedgerQuery(since=0, limit=1))
        second_page = await list_user_ledger(
            session,
            target.id,
            UserLedgerQuery(
                since=0,
                limit=1,
                cursor_created_at=first_page.next_cursor.created_at,
                cursor_id=first_page.next_cursor.id,
            ),
        )

    assert [item.id for item in first_page.items] == ['recent-2']
    encoded_page = jsonable_encoder(first_page)
    assert encoded_page['items'][0]['id'] == 'recent-2'
    assert encoded_page['items'][0]['usage_status'] is None
    assert encoded_page['items'][0]['pricing_snapshot'] is None
    assert encoded_page['items'][0]['metadata_snapshot'] == {'remote_address_hash': 'a0' * 32}
    with pytest.raises(TypeError):
        first_page.items[0].metadata_snapshot['remote_address_hash'] = 'replacement'
    assert first_page.next_cursor is not None
    assert [item.id for item in second_page.items] == ['recent-1']
    assert second_page.next_cursor is None


@pytest.mark.asyncio
async def test_admin_ledger_query_supports_permanent_filters_and_date_range(service_database) -> None:
    await create_user(service_database, 'user-1')
    await create_user(service_database, 'user-2')
    now = int(time.time())
    await add_ledger(
        service_database,
        user_id='user-1',
        entry_id='matched',
        created_at=now - 10,
        reason_code='promotion_gift',
        service_type='image',
        resource_id='model-a',
        action='generate',
    )
    await add_ledger(
        service_database,
        user_id='user-1',
        entry_id='wrong-reason',
        created_at=now - 9,
        reason_code='other',
        service_type='image',
        resource_id='model-a',
        action='generate',
    )
    await add_ledger(
        service_database,
        user_id='user-2',
        entry_id='wrong-user',
        created_at=now - 8,
        reason_code='promotion_gift',
        service_type='image',
        resource_id='model-a',
        action='generate',
    )

    async with service_database() as session:
        page = await list_admin_ledger(
            session,
            AdminLedgerQuery(
                user_query='user-1',
                entry_type='admin_adjustment',
                reason_code='promotion_gift',
                service_type='image',
                resource_id='model-a',
                action='generate',
                since=now - 11,
                until=now - 9,
            ),
        )

    assert [item.id for item in page.items] == ['matched']
    assert page.total == 1


@pytest.mark.asyncio
async def test_admin_ledger_user_query_matches_name_email_and_snapshot(service_database) -> None:
    """管理员按用户名/邮箱模糊检索：命中用户表（改名前流水也可查）或流水快照（已删用户）。"""
    await create_user(service_database, 'user-1', name='Alice Zhang', email='alice@example.test')
    await create_user(service_database, 'user-2', name='Bob', email='bob@example.test')
    now = int(time.time())
    await add_ledger(service_database, user_id='user-1', entry_id='by-name', created_at=now - 3)
    await add_ledger(service_database, user_id='user-2', entry_id='by-email', created_at=now - 2)
    # ghost 用户已不在用户表，仅流水快照留有身份信息。
    await add_ledger(
        service_database,
        user_id='ghost',
        entry_id='by-snapshot',
        created_at=now - 1,
        user_name_snapshot='Ghost User',
        user_email_snapshot='ghost@example.test',
    )

    async with service_database() as session:
        by_name = await list_admin_ledger(session, AdminLedgerQuery(user_query='lice Zh'))
        by_email = await list_admin_ledger(session, AdminLedgerQuery(user_query='bob@example'))
        by_snapshot = await list_admin_ledger(session, AdminLedgerQuery(user_query='Ghost'))
        no_match = await list_admin_ledger(session, AdminLedgerQuery(user_query='carol'))

    assert [item.id for item in by_name.items] == ['by-name']
    assert [item.id for item in by_email.items] == ['by-email']
    assert [item.id for item in by_snapshot.items] == ['by-snapshot']
    assert no_match.items == ()
    assert no_match.total == 0


@pytest.mark.asyncio
async def test_admin_ledger_resource_id_fuzzy_match_escapes_like_wildcards(service_database) -> None:
    """模型/资源按子串模糊匹配，且 % _ \ 按字面匹配而非通配符。"""
    await create_user(service_database, 'user-1')
    now = int(time.time())
    await add_ledger(
        service_database,
        user_id='user-1',
        entry_id='flux-entry',
        created_at=now - 3,
        resource_id='fal-ai/flux-1/dev',
    )
    await add_ledger(
        service_database,
        user_id='user-1',
        entry_id='literal-entry',
        created_at=now - 2,
        resource_id='model-100%',
    )
    await add_ledger(
        service_database,
        user_id='user-1',
        entry_id='wildcard-entry',
        created_at=now - 1,
        resource_id='model-100x',
    )

    async with service_database() as session:
        partial = await list_admin_ledger(session, AdminLedgerQuery(resource_id='flux-1'))
        literal = await list_admin_ledger(session, AdminLedgerQuery(resource_id='100%'))

    assert [item.id for item in partial.items] == ['flux-entry']
    # '100%' 中的 % 是字面字符：不应把 'model-100x' 一并匹配进来。
    assert [item.id for item in literal.items] == ['literal-entry']


def test_admin_ledger_query_rejects_blank_user_query() -> None:
    """前端清空筛选后不应再传空串；即便传了也必须被 422 拒绝而非落库查询。"""
    with pytest.raises(ValidationError):
        AdminLedgerQuery(user_query='')
    with pytest.raises(ValidationError):
        AdminLedgerQuery(resource_id='')
    with pytest.raises(ValidationError):
        ReconciliationQuery(user_query='')
    with pytest.raises(ValidationError):
        CreditPriceQuery(resource_id='')


@pytest.mark.asyncio
async def test_credit_price_resource_id_fuzzy_match(service_database) -> None:
    """积分价格列表的模型/资源筛选按子串模糊匹配。"""
    await add_price(service_database, resource_id='fal-ai/flux-1/dev')
    await add_price(service_database, resource_id='openai/gpt-image-1')

    async with service_database() as session:
        items, total = await credit_repository.list_credit_prices(
            session, CreditPriceQuery(resource_id='flux')
        )
        exact_items, exact_total = await credit_repository.list_credit_prices(
            session, CreditPriceQuery(resource_id='openai/gpt-image-1')
        )
        no_match = await credit_repository.list_credit_prices(
            session, CreditPriceQuery(resource_id='midjourney')
        )

    assert [price.id for price in items] == ['price-fal-ai/flux-1/dev']
    assert total == 1
    assert [price.id for price in exact_items] == ['price-openai/gpt-image-1']
    assert exact_total == 1
    assert no_match[0] == []
    assert no_match[1] == 0


@pytest.mark.asyncio
async def test_admin_ledger_query_without_optional_filters_returns_all_entries(service_database) -> None:
    await create_user(service_database, 'user-1')
    now = int(time.time())
    await add_ledger(service_database, user_id='user-1', entry_id='entry-1', created_at=now - 2)
    await add_ledger(service_database, user_id='user-1', entry_id='entry-2', created_at=now - 1)

    async with service_database() as session:
        page = await list_admin_ledger(session, AdminLedgerQuery())

    assert [item.id for item in page.items] == ['entry-2', 'entry-1']
    # 页码分页必须给出命中总数，前端分页器据此渲染页码；旧游标分页没有 total。
    assert page.total == 2


@pytest.mark.asyncio
async def test_admin_ledger_paginates_with_skip_and_reports_total(service_database) -> None:
    """管理员流水用页码分页：skip 跳过已看页、total 给出命中总数用于渲染分页器。"""
    await create_user(service_database, 'user-1')
    now = int(time.time())
    await add_ledger(service_database, user_id='user-1', entry_id='entry-1', created_at=now - 5)
    await add_ledger(service_database, user_id='user-1', entry_id='entry-2', created_at=now - 4)
    await add_ledger(service_database, user_id='user-1', entry_id='entry-3', created_at=now - 3)

    async with service_database() as session:
        first_page = await list_admin_ledger(session, AdminLedgerQuery(limit=2, skip=0))
        second_page = await list_admin_ledger(session, AdminLedgerQuery(limit=2, skip=2))

    assert [item.id for item in first_page.items] == ['entry-3', 'entry-2']
    assert first_page.total == 3
    assert [item.id for item in second_page.items] == ['entry-1']
    assert second_page.total == 3


@pytest.mark.asyncio
async def test_deleted_users_keep_history_but_cannot_be_adjusted(service_database) -> None:
    target = await create_user(service_database, 'user-1')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')
    async with service_database() as session:
        await adjust_balance(session, target, operator, adjustment('increase', 10), audit('seed'))
    async with service_database() as session, session.begin():
        await session.execute(User.__table__.delete().where(User.id == target.id))

    async with service_database() as session:
        history = await list_user_ledger(session, target.id, UserLedgerQuery())
    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await adjust_balance(session, target, operator, adjustment('increase', 1), audit('after-delete'))

    assert [item.id for item in history.items]
    assert raised.value.code == 'invalid_adjustment'


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv('TEST_POSTGRES_DATABASE_URL'),
    reason='TEST_POSTGRES_DATABASE_URL is not set; PostgreSQL transaction tests skipped',
)
async def test_postgresql_adjustment_transaction_when_configured() -> None:
    engine = create_async_engine(_make_async_url(os.environ['TEST_POSTGRES_DATABASE_URL']))
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    user_id = f'pg-user-{uuid4().hex}'
    target = UserSnapshot(id=user_id, name='PostgreSQL User', email=f'{user_id}@example.test')
    operator = UserSnapshot(id='pg-admin', name='PostgreSQL Admin', email='pg-admin@example.test')
    try:
        async with engine.begin() as connection:
            await connection.run_sync(CreditBase.metadata.create_all)
            await connection.run_sync(User.__table__.create, checkfirst=True)
            await connection.execute(
                postgresql_insert(User)
                .values(id=target.id, name=target.name, email=target.email)
                .on_conflict_do_nothing()
            )
        async with sessions() as session:
            ledger = await adjust_balance(session, target, operator, adjustment('increase', 9), audit('pg-adjustment'))
            assert ledger.balance_after == 9
    finally:
        async with engine.begin() as connection:
            await connection.execute(CreditLedger.__table__.delete().where(CreditLedger.user_id == target.id))
            await connection.execute(CreditAccount.__table__.delete().where(CreditAccount.user_id == target.id))
            await connection.execute(User.__table__.delete().where(User.id == target.id))
        await engine.dispose()


@pytest.mark.asyncio
async def test_user_ledger_category_filters_income_consumption_and_adjustments(service_database) -> None:
    target = await create_user(service_database, 'category-user')
    now = int(time.time())
    async with service_database() as session, session.begin():
        account = CreditAccount(
            id='category-account',
            user_id=target.id,
            balance=10,
            created_at=now,
            updated_at=now,
        )
        session.add(account)
        await session.flush()
        for entry_id, amount, entry_type in (
            ('income', 5, 'admin_adjustment'),
            ('consumption', -2, 'consumption'),
            ('adjustment', -1, 'admin_adjustment'),
        ):
            session.add(
                CreditLedger(
                    id=entry_id,
                    account_id=account.id,
                    user_id=target.id,
                    amount=amount,
                    balance_before=10,
                    balance_after=10 + amount,
                    entry_type=entry_type,
                    request_source='internal_admin',
                    request_id=f'request-{entry_id}',
                    created_at=now,
                )
            )

    expected = {
        'income': {'income'},
        'consumption': {'consumption'},
        'adjustment': {'income', 'adjustment'},
    }
    for category, identifiers in expected.items():
        async with service_database() as session:
            page = await list_user_ledger(session, target.id, UserLedgerQuery(category=category))
        assert {item.id for item in page.items} == identifiers


@pytest.mark.asyncio
async def test_adjustment_does_not_mutate_input_snapshots_or_request(service_database) -> None:
    target = await create_user(service_database, 'user-1')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')
    request = adjustment('increase', 10, 'other', note='manual reason')
    target_before = asdict(target)
    operator_before = asdict(operator)
    request_before = request.model_dump()

    async with service_database() as session:
        await adjust_balance(session, target, operator, request, audit())

    assert asdict(target) == target_before
    assert asdict(operator) == operator_before
    assert request.model_dump() == request_before
