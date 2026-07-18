from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path

import open_webui.extensions.credits.service as credit_service
import pytest
import pytest_asyncio
from open_webui.extensions.credits.compat import ImageBillingContext
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
from open_webui.models.users import User
from sqlalchemy import event, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


async def create_user(sessions, user_id: str, *, name: str | None = None, email: str | None = None) -> UserSnapshot:
    snapshot = UserSnapshot(
        id=user_id,
        name=name or f'Name {user_id}',
        email=email or f'{user_id}@example.test',
    )
    async with sessions() as session, session.begin():
        await session.execute(insert(User).values(id=snapshot.id, name=snapshot.name, email=snapshot.email))
    return snapshot


def audit(request_id: str = 'request-1') -> RequestAuditContext:
    return RequestAuditContext(source='internal_admin', request_id=request_id, remote_address_hash='a0' * 32)


def adjustment(direction: str, amount: int) -> AdjustmentRequest:
    return AdjustmentRequest(direction=direction, amount=amount, reason_code='accounting_correction')


def image_context(*, resource_id: str = 'model-a') -> ImageBillingContext:
    return ImageBillingContext(
        service_type='image',
        resource_id=resource_id,
        action='text-to-image',
        channel='web',
        dimensions={'size': '512x512', 'image_count': 1},
        prompt_hash='a' * 64,
        reference_hashes=(),
        request_hash='b' * 64,
    )


async def add_price(sessions, *, resource_id: str = 'model-a', enabled: bool = True, base_price: str = '3') -> None:
    now = int(time.time())
    async with sessions() as session, session.begin():
        session.add(
            CreditPrice(
                id=f'price-{resource_id}',
                service_type='image',
                resource_id=resource_id,
                action='text-to-image',
                base_price=base_price,
                rules={'schema_version': 1, 'dimensions': []},
                enabled=enabled,
                created_at=now,
                updated_at=now,
            )
        )


async def credit_user(sessions, user: UserSnapshot, amount: int = 10) -> None:
    async with sessions() as session:
        await credit_service.adjust_balance(
            session,
            user,
            UserSnapshot(id='admin-1', name='Admin', email='admin@example.test'),
            adjustment('increase', amount),
            audit('seed'),
        )


@pytest_asyncio.fixture
async def service_database(tmp_path: Path):
    database_path = tmp_path / 'task6.sqlite'
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


@asynccontextmanager
async def credit_session_for_test(sessions):
    async with sessions() as session:
        yield session


@pytest.mark.asyncio
async def test_begin_image_usage_rejects_invalid_idempotency_key_without_usage(service_database) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)

    async with service_database() as session:
        for key in ('', 'a' * 129, 'bad\nkey', 7):
            with pytest.raises(CreditError) as raised:
                await begin_image_usage(session, user, image_context(), key)
            assert raised.value.code == 'invalid_adjustment'

    async with service_database() as session:
        assert await session.scalar(select(func.count()).select_from(CreditUsage)) == 0


@pytest.mark.asyncio
async def test_begin_image_usage_uses_current_role_and_rejects_deleted_user(service_database) -> None:
    user = await create_user(service_database, 'admin-1')
    await credit_user(service_database, user)
    await add_price(service_database)
    stale_admin = UserSnapshot(id=user.id, name=user.name, email=user.email)
    async with service_database() as session, session.begin():
        await session.execute(User.__table__.update().where(User.id == user.id).values(role='admin'))

    async with service_database() as session:
        exempt = await begin_image_usage(session, stale_admin, image_context(), 'admin-current-role')
    assert exempt.usage.exempt is True
    assert exempt.usage.ledger_id is None
    assert exempt.usage.charged_credits == 0

    async with service_database() as session, session.begin():
        await session.execute(User.__table__.delete().where(User.id == user.id))
    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await begin_image_usage(session, stale_admin, image_context(), 'deleted-user')
    assert raised.value.code == 'invalid_adjustment'


@pytest.mark.asyncio
async def test_begin_image_usage_retries_same_key_after_missing_disabled_or_incomplete_price(service_database) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)

    async with service_database() as session:
        with pytest.raises(CreditError) as missing:
            await begin_image_usage(session, user, image_context(), 'price-retry-key')
    assert missing.value.code == 'price_not_configured'

    await add_price(service_database, enabled=False)
    async with service_database() as session:
        with pytest.raises(CreditError) as disabled:
            await begin_image_usage(session, user, image_context(), 'price-retry-key')
    assert disabled.value.code == 'price_not_configured'

    async with service_database() as session, session.begin():
        await session.execute(CreditPrice.__table__.update().values(enabled=True, rules={'invalid': True}))
    async with service_database() as session:
        with pytest.raises(CreditError) as incomplete:
            await begin_image_usage(session, user, image_context(), 'price-retry-key')
    assert incomplete.value.code == 'price_rule_incomplete'

    async with service_database() as session:
        assert await session.scalar(select(func.count()).select_from(CreditUsage)) == 0
        assert (
            await session.scalar(
                select(func.count()).select_from(CreditLedger).where(CreditLedger.entry_type == 'consumption')
            )
            == 0
        )

    async with service_database() as session, session.begin():
        await session.execute(CreditPrice.__table__.update().values(rules={'schema_version': 1, 'dimensions': []}))
    async with service_database() as session:
        retry = await begin_image_usage(session, user, image_context(), 'price-retry-key')
    assert retry.outcome == 'new'


@pytest.mark.asyncio
async def test_begin_image_usage_replays_each_committed_usage_outcome_without_debiting_again(
    service_database, monkeypatch
) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user, amount=30)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))

    async with service_database() as session:
        usage = await begin_image_usage(session, user, image_context(), 'outcome-replay')
    assert await mark_usage_invoking(usage.usage.id) == 1
    assert await mark_usage_failed(usage.usage.id, SafeProviderError(code='provider_error', summary='safe')) == 1

    async with service_database() as session:
        replay_failed = await begin_image_usage(session, user, image_context(), 'outcome-replay')
    assert replay_failed.outcome == 'failed'
    assert replay_failed.usage.error_snapshot == {'code': 'provider_error', 'summary': 'safe'}

    async with service_database() as session:
        processing = await begin_image_usage(session, user, image_context(), 'unknown-replay')
    marked = await mark_stale_usage_unknown(int(time.time()) + 1)
    assert marked == 1
    async with service_database() as session:
        replay_unknown = await begin_image_usage(session, user, image_context(), 'unknown-replay')
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        consumption_count = await session.scalar(
            select(func.count()).select_from(CreditLedger).where(CreditLedger.entry_type == 'consumption')
        )

    assert processing.outcome == 'new'
    assert replay_unknown.outcome == 'unknown'
    assert account is not None
    assert account.balance == 24
    assert consumption_count == 2


@pytest.mark.asyncio
async def test_usage_snapshots_filter_unsafe_data_and_keep_state_transitions_conditional(
    service_database, monkeypatch
) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))

    async with service_database() as session:
        started = await begin_image_usage(session, user, image_context(), 'snapshot-key')
    assert started.usage.request_snapshot == {
        'request_hash': 'b' * 64,
        'dimensions': {'size': '512x512', 'image_count': 1},
    }
    assert started.usage.pricing_snapshot is not None
    assert started.usage.pricing_snapshot['rounding'] == 'ceiling'
    assert 'prompt' not in started.usage.request_snapshot
    assert await mark_usage_invoking(started.usage.id) == 1
    assert await mark_usage_succeeded(started.usage.id, ['/api/v1/files/safe-file/content']) == 1
    assert await mark_usage_succeeded(started.usage.id, ['/api/v1/files/late/content']) == 0
    assert (
        await mark_usage_failed(
            started.usage.id,
            SafeProviderError(code='provider_error', summary='token=secret\n127.0.0.1'),
        )
        == 0
    )

    async with service_database() as session:
        usage = await session.get(CreditUsage, started.usage.id)
    assert usage is not None
    assert usage.status == 'succeeded'
    assert usage.result_snapshot == {'urls': ['/api/v1/files/safe-file/content']}
    assert usage.error_snapshot is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'url',
    [
        '//cdn.example/image.png',
        'https://provider.example/image.png',
        '/api/v1/files/safe/content?token=secret',
        '/api/v1/files/safe/content#fragment',
        '/api/v1/files/safe\\content',
        '/api/v1/files/safe/content\n',
        '/images/safe/content',
    ],
)
async def test_usage_succeeded_rejects_unsafe_provider_result_urls(service_database, monkeypatch, url: str) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        started = await begin_image_usage(session, user, image_context(), f'unsafe-{url!r}')
    await mark_usage_invoking(started.usage.id)

    with pytest.raises(CreditError) as raised:
        await mark_usage_succeeded(started.usage.id, [url])
    assert raised.value.code == 'provider_failed'


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'url',
    [
        '/api/v1/files//content',
        '/api/v1/files/../content',
        '/api/v1/files/file%2fother/content',
    ],
)
async def test_usage_succeeded_rejects_non_safe_file_identifier(service_database, monkeypatch, url: str) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        started = await begin_image_usage(session, user, image_context(), f'unsafe-path-{url!r}')
    assert await mark_usage_invoking(started.usage.id) == 1
    with pytest.raises(CreditError) as raised:
        await mark_usage_succeeded(started.usage.id, [url])
    assert raised.value.code == 'provider_failed'


@pytest.mark.asyncio
async def test_begin_image_usage_commits_before_return(service_database) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)

    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'committed-before-return')
        assert not session.in_transaction()

    async with service_database() as separate_session:
        persisted = await separate_session.get(CreditUsage, result.usage.id)
    assert persisted is not None
    assert persisted.status == 'debited'


@pytest.mark.asyncio
async def test_safe_provider_error_summary_is_bounded_without_control_characters(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'user-1')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        started = await begin_image_usage(session, user, image_context(), 'safe-error')
    assert await mark_usage_invoking(started.usage.id) == 1
    assert (
        await mark_usage_failed(
            started.usage.id,
            SafeProviderError(code='stable_provider_error', summary='secret\x00\n' + ('x' * 600)),
        )
        == 1
    )

    async with service_database() as session:
        usage = await session.get(CreditUsage, started.usage.id)
    assert usage is not None
    assert usage.error_snapshot == {'code': 'stable_provider_error', 'summary': 'secret' + ('x' * 506)}


@pytest.mark.parametrize('code', ['', 'provider error', 'provider\x00error', 'x' * 65])
def test_safe_provider_error_rejects_non_stable_codes(code: str) -> None:
    with pytest.raises(ValueError):
        SafeProviderError(code=code, summary='safe summary')
