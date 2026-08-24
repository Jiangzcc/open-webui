from __future__ import annotations

import os
from pathlib import Path

import pytest
import pytest_asyncio
from open_webui.extensions.credits.compat import ImageBillingContext
from open_webui.extensions.credits.db import CreditBase
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.models import CreditAccount, CreditLedger, CreditPrice
from open_webui.extensions.credits.schemas import AdjustmentRequest, RequestAuditContext, UserSnapshot
from open_webui.extensions.credits.service import adjust_balance, begin_image_usage
from open_webui.models.users import User
from sqlalchemy import func, insert, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def repair_database(tmp_path: Path):
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "repair.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(User.__table__.create)
        await connection.run_sync(CreditBase.metadata.create_all)

    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield sessions
    finally:
        await engine.dispose()


async def create_user(sessions, user_id: str) -> UserSnapshot:
    user = UserSnapshot(id=user_id, name=f'User {user_id}', email=f'{user_id}@example.test')
    async with sessions() as session, session.begin():
        await session.execute(insert(User).values(id=user.id, name=user.name, email=user.email))
    return user


async def create_mismatched_account(sessions, user: UserSnapshot) -> None:
    async with sessions() as session, session.begin():
        account = CreditAccount(
            id=f'account-{user.id}',
            user_id=user.id,
            balance=8,
            user_name_snapshot=user.name,
            user_email_snapshot=user.email,
            created_at=1,
            updated_at=1,
        )
        session.add(account)
        session.add(
            CreditLedger(
                id=f'ledger-{user.id}',
                account_id=account.id,
                user_id=user.id,
                user_name_snapshot=user.name,
                user_email_snapshot=user.email,
                amount=5,
                balance_before=0,
                balance_after=5,
                entry_type='admin_adjustment',
                reason_code='accounting_correction',
                request_source='internal_admin',
                request_id='seed-mismatch',
                created_at=1,
            )
        )
        session.add(
            CreditPrice(
                id=f'price-{user.id}',
                service_type='image',
                resource_id='model-a',
                action='text-to-image',
                base_price='1',
                rules={'schema_version': 1, 'dimensions': []},
                enabled=True,
                created_at=1,
                updated_at=1,
            )
        )


async def account_and_ledger_total(sessions, user_id: str) -> tuple[int, int]:
    async with sessions() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user_id))
        assert account is not None
        total = await session.scalar(
            select(func.coalesce(func.sum(CreditLedger.amount), 0)).where(CreditLedger.account_id == account.id)
        )
        return account.balance, int(total)


def image_context() -> ImageBillingContext:
    return ImageBillingContext(
        service_type='image',
        resource_id='model-a',
        action='text-to-image',
        channel='web',
        dimensions={'image_count': 1},
        prompt_hash='a' * 64,
        reference_hashes=(),
        request_hash='b' * 64,
    )


@pytest.mark.asyncio
async def test_regular_adjustment_preserves_an_existing_account_ledger_difference(repair_database) -> None:
    """adjust_balance now rejects mismatched accounts (P0 #5 fix).

    Previously it would silently preserve the mismatch; the consistency
    guard added in the redemption work makes it refuse to write until the
    account is repaired. This test verifies the guard fires.
    """
    target = await create_user(repair_database, 'repair-user')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')
    await create_mismatched_account(repair_database, target)

    async with repair_database() as session:
        with pytest.raises(CreditError) as raised:
            await adjust_balance(
                session,
                target,
                operator,
                AdjustmentRequest(direction='increase', amount=2, reason_code='accounting_correction'),
                RequestAuditContext(
                    source='internal_admin',
                    request_id='ordinary-adjustment',
                    remote_address_hash=None,
                ),
            )
    assert raised.value.code == 'credit_service_unavailable'
    assert raised.value.context.get('reason') == 'account_ledger_mismatch'

    # The mismatch is preserved — no writes occurred.
    account_balance, ledger_total = await account_and_ledger_total(repair_database, target.id)
    assert (account_balance, ledger_total) == (8, 5)
    assert account_balance - ledger_total == 3


@pytest.mark.asyncio
async def test_controlled_repair_rejects_invalid_operator_identity_without_writes(repair_database) -> None:
    from open_webui.extensions.credits.repair import CreditRepairError, repair_account_from_ledger

    target = await create_user(repair_database, 'repair-user')
    await create_mismatched_account(repair_database, target)
    operator = object.__new__(UserSnapshot)
    object.__setattr__(operator, 'id', 'admin-1')
    object.__setattr__(operator, 'name', None)
    object.__setattr__(operator, 'email', 'admin@example.test\nsecret')

    async with repair_database() as session:
        with pytest.raises(CreditRepairError, match='operator'):
            await repair_account_from_ledger(
                session,
                target.id,
                operator,
                incident_id='INC-2026-INVALID-OPERATOR',
                expected_balance=5,
                note='Reconciled after verified database restore.',
                backup_confirmed=True,
            )

    assert await account_and_ledger_total(repair_database, target.id) == (8, 5)


@pytest.mark.asyncio
async def test_controlled_repair_calibrates_only_account_and_appends_zero_amount_evidence(repair_database) -> None:
    from open_webui.extensions.credits.repair import repair_account_from_ledger

    target = await create_user(repair_database, 'repair-user')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')
    await create_mismatched_account(repair_database, target)

    async with repair_database() as session:
        repair = await repair_account_from_ledger(
            session,
            target.id,
            operator,
            incident_id='INC-2026-0001',
            expected_balance=5,
            note='Reconciled after verified database restore.',
            backup_confirmed=True,
        )

    account_balance, ledger_total = await account_and_ledger_total(repair_database, target.id)
    assert (account_balance, ledger_total) == (5, 5)
    assert repair.amount == 0
    assert repair.balance_before == repair.balance_after == 5
    assert repair.entry_type == 'system_adjustment'
    assert repair.metadata_snapshot is not None
    assert repair.metadata_snapshot['incident_id'] == 'INC-2026-0001'
    assert repair.metadata_snapshot['observed_account_balance'] == 8
    assert repair.metadata_snapshot['difference'] == 3
    assert repair.metadata_snapshot['operator'] == {'id': 'admin-1', 'name': 'Admin', 'email': 'admin@example.test'}
    assert repair.metadata_snapshot['reason'] == 'ledger_reconciliation'
    assert isinstance(repair.metadata_snapshot['repaired_at'], int)


@pytest.mark.asyncio
async def test_repair_requires_backup_confirmation_correct_expected_sum_and_safe_target(repair_database) -> None:
    from open_webui.extensions.credits.repair import CreditRepairError, repair_account_from_ledger

    target = await create_user(repair_database, 'repair-user')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')
    await create_mismatched_account(repair_database, target)

    async with repair_database() as session:
        with pytest.raises(CreditRepairError, match='verified backup'):
            await repair_account_from_ledger(
                session,
                target.id,
                operator,
                incident_id='INC-2026-0002',
                expected_balance=4,
                note='Reconciled after verified database restore.',
                backup_confirmed=False,
            )

    assert await account_and_ledger_total(repair_database, target.id) == (8, 5)


@pytest.mark.asyncio
async def test_repair_rejects_a_stale_expected_ledger_sum_without_writing_evidence(repair_database) -> None:
    from open_webui.extensions.credits.repair import CreditRepairError, repair_account_from_ledger

    target = await create_user(repair_database, 'repair-user')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')
    await create_mismatched_account(repair_database, target)

    async with repair_database() as session:
        with pytest.raises(CreditRepairError, match='does not match'):
            await repair_account_from_ledger(
                session,
                target.id,
                operator,
                incident_id='INC-2026-0002',
                expected_balance=4,
                note='Reconciled after verified database restore.',
                backup_confirmed=True,
            )

    assert await account_and_ledger_total(repair_database, target.id) == (8, 5)
    async with repair_database() as session:
        evidence_count = await session.scalar(
            select(func.count()).where(CreditLedger.entry_type == 'system_adjustment')
        )
    assert evidence_count == 0


@pytest.mark.asyncio
async def test_repeated_repair_incident_returns_existing_zero_amount_evidence(repair_database) -> None:
    from open_webui.extensions.credits.repair import repair_account_from_ledger

    target = await create_user(repair_database, 'repair-user')
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')
    await create_mismatched_account(repair_database, target)

    async with repair_database() as session:
        first = await repair_account_from_ledger(
            session,
            target.id,
            operator,
            incident_id='INC-2026-0003',
            expected_balance=5,
            note='Reconciled after verified database restore.',
            backup_confirmed=True,
        )

    async with repair_database() as session:
        repeated = await repair_account_from_ledger(
            session,
            target.id,
            operator,
            incident_id='INC-2026-0003',
            expected_balance=5,
            note='Reconciled after verified database restore.',
            backup_confirmed=True,
        )

    async with repair_database() as session:
        evidence_count = await session.scalar(
            select(func.count()).where(
                CreditLedger.account_id == 'account-repair-user',
                CreditLedger.entry_type == 'system_adjustment',
                CreditLedger.request_id == 'repair:INC-2026-0003',
            )
        )

    assert repeated.id == first.id
    assert evidence_count == 1
    assert await account_and_ledger_total(repair_database, target.id) == (5, 5)


@pytest.mark.asyncio
async def test_usage_precharge_fails_closed_when_account_and_full_ledger_sum_differ(repair_database) -> None:
    target = await create_user(repair_database, 'repair-user')
    await create_mismatched_account(repair_database, target)

    async with repair_database() as session:
        with pytest.raises(Exception) as raised:
            await begin_image_usage(session, target, image_context(), 'mismatch-usage')

    assert getattr(raised.value, 'code', None) == 'credit_service_unavailable'
    async with repair_database() as session:
        ledger_count = await session.scalar(select(func.count()).select_from(CreditLedger))
    assert ledger_count == 1


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv('TEST_POSTGRES_DATABASE_URL'),
    reason='TEST_POSTGRES_DATABASE_URL is not set; PostgreSQL repair gate skipped',
)
async def test_postgresql_repair_when_configured() -> None:
    from open_webui.extensions.credits.repair import repair_account_from_ledger
    from open_webui.internal.db import _make_async_url

    database_url = os.environ['TEST_POSTGRES_DATABASE_URL']
    engine = create_async_engine(_make_async_url(database_url))
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    target = UserSnapshot(id='pg-repair-user', name='PostgreSQL User', email='pg-repair@example.test')
    operator = UserSnapshot(id='pg-repair-admin', name='Admin', email='pg-admin@example.test')
    try:
        async with engine.begin() as connection:
            await connection.run_sync(CreditBase.metadata.create_all)
            await connection.run_sync(User.__table__.create, checkfirst=True)
        async with sessions() as session, session.begin():
            await session.execute(
                postgresql_insert(User)
                .values(id=target.id, name=target.name, email=target.email)
                .on_conflict_do_nothing()
            )
            account = CreditAccount(
                id='pg-repair-account',
                user_id=target.id,
                balance=8,
                created_at=1,
                updated_at=1,
            )
            session.add(account)
            session.add(
                CreditLedger(
                    id='pg-repair-ledger',
                    account_id=account.id,
                    user_id=target.id,
                    amount=5,
                    balance_before=0,
                    balance_after=5,
                    entry_type='admin_adjustment',
                    reason_code='accounting_correction',
                    request_source='internal_admin',
                    request_id='pg-seed',
                    created_at=1,
                )
            )
        async with sessions() as session:
            repair = await repair_account_from_ledger(
                session,
                target.id,
                operator,
                incident_id='INC-PG-0001',
                expected_balance=5,
                note='Reconciled after verified database restore.',
                backup_confirmed=True,
            )
        assert repair.amount == 0
        async with sessions() as session:
            account = await session.scalar(select(CreditAccount).where(CreditAccount.id == 'pg-repair-account'))
            total = await session.scalar(
                select(func.coalesce(func.sum(CreditLedger.amount), 0)).where(
                    CreditLedger.account_id == 'pg-repair-account'
                )
            )
        assert account is not None
        assert (account.balance, total) == (5, 5)
    finally:
        async with engine.begin() as connection:
            await connection.execute(
                CreditLedger.__table__.delete().where(CreditLedger.account_id == 'pg-repair-account')
            )
            await connection.execute(CreditAccount.__table__.delete().where(CreditAccount.id == 'pg-repair-account'))
            await connection.execute(User.__table__.delete().where(User.id == target.id))
        await engine.dispose()
