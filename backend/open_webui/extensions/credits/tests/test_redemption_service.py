from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
import pytest_asyncio
from open_webui.extensions.credits import redemption
from open_webui.extensions.credits.db import CreditBase
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.models import (
    CreditAccount,
    CreditLedger,
    CreditRedeemAudit,
    CreditRedeemCode,
)
from open_webui.extensions.credits.schemas import (
    RedeemBatchCreate,
    RequestAuditContext,
    UserSnapshot,
)
from open_webui.models.users import User
from sqlalchemy import event, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def redemption_database(tmp_path: Path):
    engine = create_async_engine(
        f'sqlite+aiosqlite:///{tmp_path / "redemption.sqlite"}',
        connect_args={'timeout': 10},
    )

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


def snapshot(user_id: str, *, name: str | None = None) -> UserSnapshot:
    return UserSnapshot(
        id=user_id,
        name=name or f'Name {user_id}',
        email=f'{user_id}@example.test',
    )


def audit(request_id: str, *, source: str = 'web') -> RequestAuditContext:
    return RequestAuditContext(
        source=source,
        request_id=request_id,
        remote_address_hash='a0' * 32,
    )


async def create_user(sessions, user_id: str) -> UserSnapshot:
    user = snapshot(user_id)
    async with sessions() as session, session.begin():
        await session.execute(insert(User).values(id=user.id, name=user.name, email=user.email))
    return user


async def create_batch(
    sessions,
    *,
    quantity: int = 1,
    face_value: int = 25,
    per_user_limit: int | None = None,
    expires_at: int | None = None,
):
    operator = snapshot('admin-1', name='Administrator')
    async with sessions() as session:
        return await redemption.create_redeem_batch(
            session,
            RedeemBatchCreate(
                name='Launch batch',
                face_value=face_value,
                quantity=quantity,
                per_user_limit=per_user_limit,
                expires_at=expires_at,
            ),
            operator,
            audit('generate-1', source='internal_admin'),
        )


@pytest.mark.asyncio
async def test_generation_returns_strong_unique_codes_and_persists_plaintext_for_admins(
    redemption_database,
) -> None:
    created = await create_batch(redemption_database, quantity=4)

    assert len(created.codes) == 4
    assert len(set(created.codes)) == 4
    assert all(code.startswith('OWC-') and len(redemption._canonical_code(code) or '') == 29 for code in created.codes)

    async with redemption_database() as session:
        rows = (await session.scalars(select(CreditRedeemCode).order_by(CreditRedeemCode.id))).all()
        audits = (await session.scalars(select(CreditRedeemAudit))).all()

    assert len(rows) == 4
    assert all(len(row.code_hash) == 64 for row in rows)
    # Administrators must be able to view codes at any time, so the display
    # plaintext is persisted alongside the redemption hash.
    assert sorted(row.code for row in rows) == sorted(created.codes)
    assert [(item.action, item.metadata_snapshot) for item in audits] == [
        ('generate', {'quantity': 4, 'face_value': 25})
    ]


@pytest.mark.asyncio
async def test_admin_code_listing_returns_persisted_plaintext(redemption_database) -> None:
    created = await create_batch(redemption_database, quantity=3)

    async with redemption_database() as session:
        page = await redemption.list_redeem_codes(session, created.id, skip=0, limit=50)

    assert page.total == 3
    assert sorted(item.code for item in page.items) == sorted(created.codes)


def test_code_normalization_accepts_only_documented_ascii_separators() -> None:
    display, _digest, _hint = redemption._new_code()
    assert redemption._canonical_code(display) is not None
    assert redemption._canonical_code(display.replace('-', ' ', 1)) is not None
    assert redemption._canonical_code(display.replace('-', '!', 1)) is None
    assert redemption._canonical_code(display.replace('-', '/', 1)) is None


@pytest.mark.asyncio
async def test_redeem_atomically_updates_code_balance_ledger_and_audit(redemption_database) -> None:
    user = await create_user(redemption_database, 'user-1')
    created = await create_batch(redemption_database, face_value=25)

    async with redemption_database() as session:
        result = await redemption.redeem_code(session, created.codes[0], user, audit('redeem-1'))

    assert result.credited == 25
    assert result.balance == 25

    async with redemption_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        ledger = await session.get(CreditLedger, result.ledger_id)
        code = await session.scalar(select(CreditRedeemCode))
        actions = list(
            await session.scalars(
                select(CreditRedeemAudit.action).order_by(CreditRedeemAudit.created_at, CreditRedeemAudit.id)
            )
        )

    assert account is not None and account.balance == 25
    assert ledger is not None
    assert (ledger.amount, ledger.balance_before, ledger.balance_after) == (25, 0, 25)
    assert (ledger.entry_type, ledger.reason_code, ledger.service_type, ledger.action) == (
        'system_adjustment',
        'redeem',
        'credits',
        'redeem',
    )
    assert code is not None
    assert (code.redeemed_by_user_id, code.redeemed_ledger_id) == (user.id, ledger.id)
    assert actions == ['generate', 'redeem'] or actions == ['redeem', 'generate']

    async with redemption_database() as session:
        with pytest.raises(CreditError) as repeated:
            await redemption.redeem_code(session, created.codes[0], user, audit('redeem-2'))
    assert repeated.value.code == 'redeem_code_used'

    async with redemption_database() as session:
        assert await session.scalar(select(CreditAccount.balance)) == 25
        assert await session.scalar(select(func.count(CreditLedger.id))) == 1


@pytest.mark.asyncio
async def test_ledger_failure_rolls_back_account_code_and_redeem_audit(
    redemption_database,
    monkeypatch,
) -> None:
    user = await create_user(redemption_database, 'rollback-user')
    created = await create_batch(redemption_database)

    async def fail_ledger(*_args, **_kwargs):
        raise RuntimeError('ledger insert failed')

    monkeypatch.setattr(redemption, 'insert_ledger', fail_ledger)
    async with redemption_database() as session:
        with pytest.raises(RuntimeError, match='ledger insert failed'):
            await redemption.redeem_code(session, created.codes[0], user, audit('rollback-redeem'))

    async with redemption_database() as session:
        code = await session.scalar(select(CreditRedeemCode))
        assert await session.scalar(select(func.count(CreditAccount.id))) == 0
        assert await session.scalar(select(func.count(CreditLedger.id))) == 0
        assert await session.scalar(
            select(func.count(CreditRedeemAudit.id)).where(CreditRedeemAudit.action == 'redeem')
        ) == 0
    assert code is not None and code.redeemed_at is None and code.redeemed_ledger_id is None


@pytest.mark.asyncio
async def test_redeem_refuses_to_build_on_an_account_ledger_mismatch(redemption_database) -> None:
    user = await create_user(redemption_database, 'mismatch-user')
    created = await create_batch(redemption_database, face_value=10)
    async with redemption_database() as session, session.begin():
        session.add(
            CreditAccount(
                id='mismatched-account',
                user_id=user.id,
                balance=7,
                user_name_snapshot=user.name,
                user_email_snapshot=user.email,
                created_at=1,
                updated_at=1,
            )
        )

    async with redemption_database() as session:
        with pytest.raises(CreditError) as mismatch:
            await redemption.redeem_code(session, created.codes[0], user, audit('mismatch-redeem'))
    assert mismatch.value.code == 'credit_service_unavailable'

    async with redemption_database() as session:
        code = await session.scalar(select(CreditRedeemCode))
        assert await session.scalar(select(CreditAccount.balance)) == 7
        assert await session.scalar(select(func.count(CreditLedger.id))) == 0
    assert code is not None and code.redeemed_at is None


@pytest.mark.asyncio
async def test_concurrent_same_code_credits_exactly_once_with_a_domain_error_for_the_loser(
    redemption_database,
) -> None:
    user = await create_user(redemption_database, 'same-code-user')
    created = await create_batch(redemption_database, face_value=9)

    async def redeem_once(request_id: str):
        try:
            async with redemption_database() as session:
                return await redemption.redeem_code(session, created.codes[0], user, audit(request_id))
        except Exception as error:
            return error

    outcomes = await asyncio.gather(redeem_once('same-1'), redeem_once('same-2'))
    successes = [outcome for outcome in outcomes if not isinstance(outcome, Exception)]
    failures = [outcome for outcome in outcomes if isinstance(outcome, Exception)]

    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], CreditError)
    assert failures[0].code == 'redeem_code_used'
    async with redemption_database() as session:
        assert await session.scalar(select(CreditAccount.balance)) == 9
        assert await session.scalar(select(func.count(CreditLedger.id))) == 1


@pytest.mark.asyncio
async def test_concurrent_distinct_codes_cannot_bypass_per_user_limit(redemption_database) -> None:
    user = await create_user(redemption_database, 'limited-user')
    created = await create_batch(redemption_database, quantity=2, face_value=11, per_user_limit=1)

    async def redeem_once(code: str, request_id: str):
        try:
            async with redemption_database() as session:
                return await redemption.redeem_code(session, code, user, audit(request_id))
        except Exception as error:
            return error

    outcomes = await asyncio.gather(
        redeem_once(created.codes[0], 'limit-1'),
        redeem_once(created.codes[1], 'limit-2'),
    )
    successes = [outcome for outcome in outcomes if not isinstance(outcome, Exception)]
    failures = [outcome for outcome in outcomes if isinstance(outcome, Exception)]

    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], CreditError)
    assert failures[0].code == 'redeem_code_limit_reached'
    async with redemption_database() as session:
        assert await session.scalar(select(CreditAccount.balance)) == 11
        assert await session.scalar(select(func.count(CreditLedger.id))) == 1
        assert await session.scalar(
            select(func.count(CreditRedeemCode.id)).where(CreditRedeemCode.redeemed_at.is_not(None))
        ) == 1


@pytest.mark.asyncio
async def test_void_and_expiry_fail_without_creating_credit(redemption_database, monkeypatch) -> None:
    user = await create_user(redemption_database, 'terminal-user')
    created = await create_batch(redemption_database, quantity=2)
    operator = snapshot('admin-1')
    canonical = redemption._canonical_code(created.codes[0])
    assert canonical is not None
    code_hash = redemption._hash_code(canonical)

    async with redemption_database() as session:
        code_id = await session.scalar(
            select(CreditRedeemCode.id).where(
                CreditRedeemCode.batch_id == created.id,
                CreditRedeemCode.code_hash == code_hash,
            )
        )
    assert code_id is not None
    async with redemption_database() as session:
        assert await redemption.void_redeem_code(
            session,
            created.id,
            code_id,
            operator,
            audit('void-1', source='internal_admin'),
        )

    async with redemption_database() as session:
        with pytest.raises(CreditError) as voided:
            await redemption.redeem_code(session, created.codes[0], user, audit('voided-redeem'))
    assert voided.value.code == 'redeem_code_voided'

    future = 2_000_000_000
    monkeypatch.setattr(redemption, '_now', lambda: future)
    expiring = await create_batch(redemption_database, expires_at=future + 1)
    monkeypatch.setattr(redemption, '_now', lambda: future + 1)
    async with redemption_database() as session:
        with pytest.raises(CreditError) as expired:
            await redemption.redeem_code(session, expiring.codes[0], user, audit('expired-redeem'))
    assert expired.value.code == 'redeem_code_expired'

    async with redemption_database() as session:
        assert await session.scalar(select(func.count(CreditLedger.id))) == 0
