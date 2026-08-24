from __future__ import annotations

import asyncio
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import open_webui.extensions.credits.service as credit_service
import pytest
import pytest_asyncio
from open_webui.extensions.credits.compat import ImageBillingContext
from open_webui.extensions.credits.constants import MAX_USAGE_RESULT_URLS
from open_webui.extensions.credits.db import CreditBase
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.models import CreditAccount, CreditLedger, CreditPrice, CreditUsage
from open_webui.extensions.credits.schemas import AdjustmentRequest, RequestAuditContext, UserSnapshot
from open_webui.extensions.credits.service import (
    SafeProviderError,
    begin_image_usage,
    mark_stale_usage_unknown,
    mark_usage_failed,
    mark_usage_invoking,
    mark_usage_succeeded,
)
from open_webui.internal.db import _make_async_url
from open_webui.models.users import User
from sqlalchemy import event, func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def service_database(tmp_path: Path):
    database_path = tmp_path / 'usage-service.sqlite'
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


def adjustment(direction: str, amount: int) -> AdjustmentRequest:
    return AdjustmentRequest(direction=direction, amount=amount, reason_code='accounting_correction')


@asynccontextmanager
async def credit_session_for_test(sessions):
    async with sessions() as session:
        yield session


from .service_test_support import add_price, create_user, credit_user, image_context


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv('TEST_POSTGRES_DATABASE_URL'),
    reason='TEST_POSTGRES_DATABASE_URL is not set; PostgreSQL usage concurrency tests skipped',
)
async def test_postgresql_concurrent_usage_claims_when_configured() -> None:
    engine = create_async_engine(_make_async_url(os.environ['TEST_POSTGRES_DATABASE_URL']))
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    user_id = f'pg-usage-{uuid4().hex}'
    resource_id = f'pg-model-{uuid4().hex}'
    user = UserSnapshot(id=user_id, name='PostgreSQL User', email=f'{user_id}@example.test')
    try:
        async with engine.begin() as connection:
            await connection.run_sync(CreditBase.metadata.create_all)
            await connection.run_sync(User.__table__.create, checkfirst=True)
            await connection.execute(
                postgresql_insert(User).values(id=user.id, name=user.name, email=user.email).on_conflict_do_nothing()
            )
        await credit_user(sessions, user, amount=3)
        await add_price(sessions, resource_id=resource_id)

        async def begin_once(key: str):
            async with sessions() as session:
                return await begin_image_usage(session, user, image_context(resource_id=resource_id), key)

        first, second = await asyncio.gather(begin_once('same-key'), begin_once('same-key'))
        assert {first.outcome, second.outcome} == {'new', 'processing'}
        assert first.usage.id == second.usage.id

        await credit_user(sessions, user, amount=3)
        outcomes = await asyncio.gather(begin_once('distinct-1'), begin_once('distinct-2'), return_exceptions=True)
        assert sum(getattr(outcome, 'outcome', None) == 'new' for outcome in outcomes) == 1
        assert (
            sum(isinstance(outcome, CreditError) and outcome.code == 'insufficient_credits' for outcome in outcomes)
            == 1
        )

        async with sessions() as session:
            account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
            usage_count = await session.scalar(
                select(func.count()).select_from(CreditUsage).where(CreditUsage.user_id == user.id)
            )
            consumption_count = await session.scalar(
                select(func.count())
                .select_from(CreditLedger)
                .where(CreditLedger.user_id == user.id, CreditLedger.entry_type == 'consumption')
            )

        assert account is not None
        assert account.balance == 0
        assert usage_count == 2
        assert consumption_count == 2
    finally:
        async with engine.begin() as connection:
            await connection.execute(CreditLedger.__table__.delete().where(CreditLedger.user_id == user.id))
            await connection.execute(CreditUsage.__table__.delete().where(CreditUsage.user_id == user.id))
            await connection.execute(CreditPrice.__table__.delete().where(CreditPrice.resource_id == resource_id))
            await connection.execute(CreditAccount.__table__.delete().where(CreditAccount.user_id == user.id))
            await connection.execute(User.__table__.delete().where(User.id == user.id))
        await engine.dispose()


@pytest.mark.asyncio
async def test_begin_image_usage_charges_once_and_replays_same_request(service_database) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)

    async with service_database() as session:
        initial = await begin_image_usage(session, user, image_context(), 'usage-key-1')
    async with service_database() as session:
        replay = await begin_image_usage(session, user, image_context(), 'usage-key-1')

    assert initial.outcome == 'new'
    assert replay.outcome == 'processing'
    assert replay.usage.id == initial.usage.id
    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        usages = list(await session.scalars(select(CreditUsage).where(CreditUsage.user_id == user.id)))
        ledgers = list(await session.scalars(select(CreditLedger).where(CreditLedger.user_id == user.id)))
    assert account is not None
    assert account.balance == 7
    assert len(usages) == 1
    assert len(ledgers) == 2
    consumption = next(ledger for ledger in ledgers if ledger.entry_type == 'consumption')
    assert consumption.amount == -3
    assert consumption.usage_id == initial.usage.id
    assert initial.usage.ledger_id == consumption.id
    assert initial.usage.request_snapshot == {
        'request_hash': image_context().request_hash,
        'dimensions': {'size': '512x512', 'image_count': 1},
    }
    assert initial.usage.pricing_snapshot == {
        'service_type': 'image',
        'resource_id': 'model-a',
        'action': 'text-to-image',
        'base_price': '3',
        'factors': [],
        'raw_price': '3',
        'charged_credits': 3,
        'rounding': 'ceiling',
    }


@pytest.mark.asyncio
async def test_concurrent_same_idempotency_key_creates_one_usage_and_debit(service_database) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)

    async def begin_once():
        async with service_database() as session:
            return await begin_image_usage(session, user, image_context(), 'same-key')

    first, second = await asyncio.gather(begin_once(), begin_once())
    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        usage_count = await session.scalar(select(func.count()).select_from(CreditUsage))
        ledger_count = await session.scalar(
            select(func.count()).select_from(CreditLedger).where(CreditLedger.entry_type == 'consumption')
        )

    assert {first.outcome, second.outcome} == {'new', 'processing'}
    assert first.usage.id == second.usage.id
    assert account is not None
    assert account.balance == 7
    assert usage_count == 1
    assert ledger_count == 1


@pytest.mark.asyncio
async def test_concurrent_distinct_idempotency_keys_cannot_overdraft(service_database) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user, amount=3)
    await add_price(service_database)

    async def begin_once(key: str):
        async with service_database() as session:
            return await begin_image_usage(session, user, image_context(), key)

    outcomes = await asyncio.gather(begin_once('key-1'), begin_once('key-2'), return_exceptions=True)
    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        usage_count = await session.scalar(select(func.count()).select_from(CreditUsage))

    assert sum(isinstance(outcome, CreditError) and outcome.code == 'insufficient_credits' for outcome in outcomes) == 1
    assert sum(getattr(outcome, 'outcome', None) == 'new' for outcome in outcomes) == 1
    assert account is not None
    assert account.balance == 0
    assert usage_count == 1


@pytest.mark.asyncio
async def test_begin_image_usage_replays_existing_request_without_repricing(service_database) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)

    async with service_database() as session:
        initial = await begin_image_usage(session, user, image_context(), 'usage-key-1')
    async with service_database() as session, session.begin():
        await session.execute(CreditPrice.__table__.delete())
    async with service_database() as session:
        replay = await begin_image_usage(session, user, image_context(), 'usage-key-1')

    assert replay.outcome == 'processing'
    assert replay.usage.id == initial.usage.id


@pytest.mark.asyncio
async def test_begin_image_usage_rejects_conflicting_idempotency_request(service_database) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)

    async with service_database() as session:
        await begin_image_usage(session, user, image_context(), 'usage-key-1')
    conflicting_context = ImageBillingContext(
        service_type='image',
        resource_id='model-a',
        action='text-to-image',
        channel='web',
        dimensions={'size': '1024x1024', 'image_count': 1},
        prompt_hash='c' * 64,
        reference_hashes=(),
        request_hash='d' * 64,
    )
    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await begin_image_usage(session, user, conflicting_context, 'usage-key-1')

    assert raised.value.code == 'idempotency_key_conflict'


@pytest.mark.asyncio
async def test_begin_image_usage_rolls_back_failed_precharge_for_retry(service_database) -> None:
    user = await create_user(service_database, 'user-1')
    await add_price(service_database)

    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await begin_image_usage(session, user, image_context(), 'usage-key-1')
    assert raised.value.code == 'insufficient_credits'
    async with service_database() as session:
        assert await session.scalar(select(func.count()).select_from(CreditUsage)) == 0

    await credit_user(service_database, user)
    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'usage-key-1')
    assert result.outcome == 'new'


@pytest.mark.asyncio
async def test_begin_image_usage_admin_requires_price(service_database) -> None:
    user = await create_user(service_database, 'admin-1')
    async with service_database() as session, session.begin():
        await session.execute(User.__table__.update().where(User.id == user.id).values(role='admin'))

    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await begin_image_usage(session, user, image_context(), 'admin-key-1')

    assert raised.value.code == 'price_not_configured'
    async with service_database() as session:
        assert await session.scalar(select(func.count()).select_from(CreditAccount)) == 0
        assert await session.scalar(select(func.count()).select_from(CreditLedger)) == 0


@pytest.mark.asyncio
async def test_usage_state_transitions_are_conditional_and_sanitize_results(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'usage-key-1')

    assert await mark_usage_invoking(result.usage.id) == 1
    assert await mark_usage_succeeded(result.usage.id, ['/api/v1/files/file-1/content']) == 1
    assert (
        await mark_usage_failed(result.usage.id, SafeProviderError(code='provider_error', summary='secret\nmessage'))
        == 0
    )
    async with service_database() as session:
        usage = await session.get(CreditUsage, result.usage.id)

    assert usage is not None
    assert usage.status == 'succeeded'
    assert usage.result_snapshot == {'urls': ['/api/v1/files/file-1/content']}
    assert usage.error_snapshot is None


@pytest.mark.asyncio
async def test_known_pre_provider_failure_atomically_restores_prepaid_credits(
    service_database, monkeypatch
) -> None:
    user = await create_user(service_database, 'user-cancel')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'cancel-key')

    assert await mark_usage_invoking(result.usage.id) == 1
    pre_provider_failure = SafeProviderError(
        code='video_fal_not_configured',
        summary='Image provider request failed',
    )
    assert await mark_usage_failed(result.usage.id, pre_provider_failure, restore_prepaid=True) == 1
    # A repeated restoration cannot create another compensating ledger row.
    assert await mark_usage_failed(result.usage.id, pre_provider_failure, restore_prepaid=True) == 0

    async with service_database() as session:
        usage = await session.get(CreditUsage, result.usage.id)
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        ledgers = list(
            (
                await session.scalars(
                    select(CreditLedger)
                    .where(CreditLedger.usage_id == result.usage.id)
                    .order_by(CreditLedger.created_at, CreditLedger.id)
                )
            ).all()
        )

    assert usage is not None and usage.status == 'failed'
    assert usage.error_snapshot['code'] == 'video_fal_not_configured'
    assert account is not None and account.balance == 10
    assert sorted(ledger.amount for ledger in ledgers) == [-3, 3]
    refund = next(ledger for ledger in ledgers if ledger.amount > 0)
    assert refund.entry_type == 'system_adjustment'
    assert refund.related_ledger_id == result.usage.ledger_id
    assert refund.idempotency_key == f'restore:{result.usage.id}'
    assert refund.metadata_snapshot == {'reason': 'prepaid_restored'}


@pytest.mark.asyncio
async def test_usage_state_updates_reject_external_urls_and_mark_stale_without_refund(
    service_database, monkeypatch
) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'usage-key-1')

    await mark_usage_invoking(result.usage.id)
    with pytest.raises(CreditError) as raised:
        await mark_usage_succeeded(result.usage.id, ['https://provider.example/image.png'])
    marked = await mark_stale_usage_unknown(int(time.time()) + 1)
    async with service_database() as session:
        usage = await session.get(CreditUsage, result.usage.id)
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))

    assert raised.value.code == 'provider_failed'
    assert marked == 1
    assert usage is not None
    assert usage.status == 'unknown'
    assert account is not None
    assert account.balance == 7


@pytest.mark.parametrize('key', ['', 'k' * 129, 'line\nbreak', 'café'])
@pytest.mark.asyncio
async def test_begin_image_usage_rejects_invalid_idempotency_keys_without_claim(service_database, key) -> None:
    user = await create_user(service_database, 'user-1')

    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await begin_image_usage(session, user, image_context(), key)
    async with service_database() as session:
        usage_count = await session.scalar(select(func.count()).select_from(CreditUsage))

    assert raised.value.code == 'invalid_adjustment'
    assert raised.value.context == {'reason': 'invalid_idempotency_key'}
    assert usage_count == 0


@pytest.mark.asyncio
async def test_begin_image_usage_rejects_deleted_user_without_claim(service_database) -> None:
    user = await create_user(service_database, 'user-1')
    async with service_database() as session, session.begin():
        await session.execute(User.__table__.delete().where(User.id == user.id))

    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await begin_image_usage(session, user, image_context(), 'deleted-user-key')
    async with service_database() as session:
        usage_count = await session.scalar(select(func.count()).select_from(CreditUsage))

    assert raised.value.code == 'invalid_adjustment'
    assert raised.value.context == {'reason': 'target_user_not_found'}
    assert usage_count == 0


@pytest.mark.parametrize(
    ('price_state', 'expected_code'),
    [
        ('missing', 'price_not_configured'),
        ('disabled', 'price_not_configured'),
        ('incomplete', 'price_rule_incomplete'),
    ],
)
@pytest.mark.asyncio
async def test_precharge_price_rejections_leave_balance_and_idempotency_key_reusable(
    service_database, price_state, expected_code
) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    if price_state == 'disabled':
        await add_price(service_database, enabled=False)
    elif price_state == 'incomplete':
        await add_price(service_database, base_price='NaN')

    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await begin_image_usage(session, user, image_context(), 'price-retry-key')
    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        usage_count = await session.scalar(select(func.count()).select_from(CreditUsage))

    assert raised.value.code == expected_code
    assert account is not None
    assert account.balance == 10
    assert usage_count == 0

    async with service_database() as session, session.begin():
        if price_state == 'missing':
            now = int(time.time())
            session.add(
                CreditPrice(
                    id='price-model-a',
                    service_type='image',
                    resource_id='model-a',
                    action='text-to-image',
                    base_price='3',
                    rules={'schema_version': 1, 'dimensions': []},
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            await session.execute(
                CreditPrice.__table__.update()
                .where(CreditPrice.resource_id == 'model-a')
                .values(base_price='3', enabled=True)
            )
    async with service_database() as session:
        retry = await begin_image_usage(session, user, image_context(), 'price-retry-key')

    assert retry.outcome == 'new'


@pytest.mark.asyncio
async def test_terminal_usage_outcomes_replay_snapshots_without_recharging(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))

    async with service_database() as session:
        succeeded = await begin_image_usage(session, user, image_context(), 'succeeded-key')
    await mark_usage_invoking(succeeded.usage.id)
    await mark_usage_succeeded(succeeded.usage.id, ['/api/v1/files/result-1/content'])

    async with service_database() as session:
        failed = await begin_image_usage(session, user, image_context(), 'failed-key')
    await mark_usage_invoking(failed.usage.id)
    safe_error = SafeProviderError(code='provider_error', summary='safe\nsummary' + ('x' * 600))
    await mark_usage_failed(failed.usage.id, safe_error)

    async with service_database() as session:
        unknown = await begin_image_usage(session, user, image_context(), 'unknown-key')
    await mark_usage_invoking(unknown.usage.id)
    assert await mark_stale_usage_unknown(int(time.time()) + 1) == 1

    async with service_database() as session, session.begin():
        await session.execute(CreditPrice.__table__.delete())
    async with service_database() as session:
        succeeded_replay = await begin_image_usage(session, user, image_context(), 'succeeded-key')
        failed_replay = await begin_image_usage(session, user, image_context(), 'failed-key')
        unknown_replay = await begin_image_usage(session, user, image_context(), 'unknown-key')
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))

    assert succeeded_replay.outcome == 'succeeded'
    assert succeeded_replay.usage.result_snapshot == {'urls': ['/api/v1/files/result-1/content']}
    assert failed_replay.outcome == 'failed'
    assert failed_replay.usage.error_snapshot['code'] == 'provider_error'
    assert '\n' not in failed_replay.usage.error_snapshot['summary']
    assert len(failed_replay.usage.error_snapshot['summary']) <= 512
    assert unknown_replay.outcome == 'unknown'
    assert account is not None
    assert account.balance == 1


@pytest.mark.parametrize('code', ['bad code', 'line\nbreak', 'café', '-starts-with-symbol'])
def test_safe_provider_error_rejects_noncanonical_codes(code: str) -> None:
    with pytest.raises(ValueError):
        SafeProviderError(code=code, summary='safe summary')


@pytest.mark.asyncio
async def test_usage_result_rejects_noncanonical_internal_file_id(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'unsafe-result-key')
    await mark_usage_invoking(result.usage.id)

    with pytest.raises(CreditError) as raised:
        await mark_usage_succeeded(result.usage.id, ['/api/v1/files/bad id/content'])
    async with service_database() as session:
        usage = await session.get(CreditUsage, result.usage.id)

    assert raised.value.code == 'provider_failed'
    assert usage is not None
    assert usage.status == 'invoking'
    assert usage.result_snapshot is None


def test_safe_provider_error_bounds_and_sanitizes_summary() -> None:
    error = SafeProviderError(code='provider_error', summary='first\nsecond\t' + ('x' * 600))

    assert '\n' not in error.summary
    assert '\t' not in error.summary
    assert len(error.summary) <= 512


@pytest.mark.parametrize(
    'urls',
    [
        [],
        ['/api/v1/files/file-1/content'] * (MAX_USAGE_RESULT_URLS + 1),
        ['/api/v1/files/file-1/content?token=secret'],
        ['/api/v1/files/file-1/content#fragment'],
        ['/api/v1/files/../content'],
        ['/api/v1/files/file-1\\content'],
    ],
)
@pytest.mark.asyncio
async def test_usage_result_enforces_url_count_and_path_boundaries(service_database, monkeypatch, urls) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'bounded-result-key')
    await mark_usage_invoking(result.usage.id)

    with pytest.raises(CreditError) as raised:
        await mark_usage_succeeded(result.usage.id, urls)
    async with service_database() as session:
        usage = await session.get(CreditUsage, result.usage.id)

    assert raised.value.code == 'provider_failed'
    assert usage is not None
    assert usage.status == 'invoking'
    assert usage.result_snapshot is None


@pytest.mark.asyncio
async def test_begin_image_usage_rolls_back_claim_and_debit_when_ledger_insert_fails(
    service_database, monkeypatch
) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)

    async def fail_insert(*_args, **_kwargs):
        raise RuntimeError('usage ledger storage failed')

    monkeypatch.setattr(credit_service, 'insert_ledger', fail_insert)
    async with service_database() as session:
        with pytest.raises(RuntimeError, match='usage ledger storage failed'):
            await begin_image_usage(session, user, image_context(), 'storage-failure-key')

    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        usage_count = await session.scalar(select(func.count()).select_from(CreditUsage))
        consumption_count = await session.scalar(
            select(func.count()).select_from(CreditLedger).where(CreditLedger.entry_type == 'consumption')
        )

    assert account is not None
    assert account.balance == 10
    assert usage_count == 0
    assert consumption_count == 0


@pytest.mark.asyncio
async def test_begin_image_usage_commits_before_caller_can_invoke_provider(service_database) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)
    ordering: list[str] = []

    async with service_database() as session:

        @event.listens_for(session.sync_session, 'after_commit')
        def record_commit(_session) -> None:
            ordering.append('committed')

        result = await begin_image_usage(session, user, image_context(), 'commit-order-key')
        ordering.append('provider')

    async with service_database() as session:
        persisted = await session.get(CreditUsage, result.usage.id)

    assert ordering == ['committed', 'provider']
    assert persisted is not None
    assert persisted.status == 'debited'
