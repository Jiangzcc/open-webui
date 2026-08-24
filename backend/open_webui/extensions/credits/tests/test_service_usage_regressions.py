from __future__ import annotations

import asyncio
import time

import open_webui.extensions.credits.service as credit_service
import pytest
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.models import CreditAccount, CreditLedger, CreditPrice, CreditUsage
from open_webui.extensions.credits.schemas import ReconciliationQuery, UserLedgerQuery
from open_webui.extensions.credits.service import (
    SafeProviderError,
    begin_image_usage,
    list_reconciliation_cases,
    mark_stale_usage_unknown,
    mark_usage_failed,
    mark_usage_invoking,
    mark_usage_succeeded,
)
from open_webui.internal.db import JSONField
from open_webui.models.users import User
from sqlalchemy import event, func, select, update

from .service_test_support import (
    add_price,
    create_user,
    credit_user,
    image_context,
)
from .test_service import (
    credit_session_for_test,
)
from .test_service import (
    service_database as _service_database,
)

service_database = _service_database


@pytest.mark.asyncio
async def test_image_usage_charges_once_and_replays_without_new_ledger(service_database) -> None:
    user = await create_user(service_database, 'usage-user')
    await credit_user(service_database, user)
    await add_price(service_database)

    async with service_database() as session:
        initial = await begin_image_usage(session, user, image_context(), 'usage-key')
    async with service_database() as session:
        replay = await begin_image_usage(session, user, image_context(), 'usage-key')

    assert initial.outcome == 'new'
    assert replay.outcome == 'processing'
    assert replay.usage.id == initial.usage.id
    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        usages = await session.scalar(select(func.count()).select_from(CreditUsage))
        consumptions = await session.scalar(
            select(func.count()).select_from(CreditLedger).where(CreditLedger.entry_type == 'consumption')
        )
    assert account is not None
    assert account.balance == 7
    assert usages == 1
    assert consumptions == 1


@pytest.mark.asyncio
async def test_admin_image_usage_requires_price_and_does_not_create_a_placeholder(service_database) -> None:
    user = await create_user(service_database, 'admin-user')
    async with service_database() as session, session.begin():
        await session.execute(User.__table__.update().where(User.id == user.id).values(role='admin'))

    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await begin_image_usage(session, user, image_context(), 'admin-key')

    assert raised.value.code == 'price_not_configured'
    async with service_database() as session:
        assert await session.scalar(select(func.count()).select_from(CreditAccount)) == 0
        assert await session.scalar(select(func.count()).select_from(CreditLedger)) == 0


@pytest.mark.asyncio
async def test_insufficient_precharge_rolls_back_claim_and_allows_same_key_retry(service_database) -> None:
    user = await create_user(service_database, 'retry-user')
    await add_price(service_database)

    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await begin_image_usage(session, user, image_context(), 'retry-key')
    assert raised.value.code == 'insufficient_credits'
    async with service_database() as session:
        assert await session.scalar(select(func.count()).select_from(CreditUsage)) == 0

    await credit_user(service_database, user)
    async with service_database() as session:
        retry = await begin_image_usage(session, user, image_context(), 'retry-key')
    assert retry.outcome == 'new'


@pytest.mark.asyncio
async def test_conflicting_idempotency_key_is_rejected_and_replay_skips_repricing(service_database) -> None:
    user = await create_user(service_database, 'idempotency-user')
    await credit_user(service_database, user)
    await add_price(service_database)
    async with service_database() as session:
        initial = await begin_image_usage(session, user, image_context(), 'shared-key')

    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await begin_image_usage(session, user, image_context(request_hash='c' * 64), 'shared-key')
    assert raised.value.code == 'idempotency_key_conflict'

    async with service_database() as session, session.begin():
        await session.execute(CreditPrice.__table__.delete())
    async with service_database() as session:
        replay = await begin_image_usage(session, user, image_context(), 'shared-key')
    assert replay.outcome == 'processing'
    assert replay.usage.id == initial.usage.id


@pytest.mark.asyncio
async def test_same_key_concurrency_creates_one_usage_and_single_debit(service_database) -> None:
    user = await create_user(service_database, 'same-key-user')
    await credit_user(service_database, user)
    await add_price(service_database)

    async def claim_once():
        async with service_database() as session:
            return await begin_image_usage(session, user, image_context(), 'same-key')

    first, second = await asyncio.gather(claim_once(), claim_once())
    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        usages = await session.scalar(select(func.count()).select_from(CreditUsage))
        consumptions = await session.scalar(
            select(func.count()).select_from(CreditLedger).where(CreditLedger.entry_type == 'consumption')
        )
    assert {first.outcome, second.outcome} == {'new', 'processing'}
    assert first.usage.id == second.usage.id
    assert account is not None
    assert account.balance == 7
    assert usages == 1
    assert consumptions == 1


@pytest.mark.asyncio
async def test_distinct_key_concurrency_cannot_overdraft(service_database) -> None:
    user = await create_user(service_database, 'distinct-key-user')
    await credit_user(service_database, user, amount=3)
    await add_price(service_database)

    async def claim_once(key: str):
        async with service_database() as session:
            return await begin_image_usage(session, user, image_context(), key)

    outcomes = await asyncio.gather(claim_once('key-1'), claim_once('key-2'), return_exceptions=True)
    assert sum(getattr(outcome, 'outcome', None) == 'new' for outcome in outcomes) == 1
    assert sum(isinstance(outcome, CreditError) and outcome.code == 'insufficient_credits' for outcome in outcomes) == 1
    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        usages = await session.scalar(select(func.count()).select_from(CreditUsage))
    assert account is not None
    assert account.balance == 0
    assert usages == 1


@pytest.mark.asyncio
async def test_state_machine_prevents_terminal_regression_and_marks_stale_without_refund(
    service_database, monkeypatch
) -> None:
    user = await create_user(service_database, 'state-user')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'state-key')

    assert await mark_usage_invoking(result.usage.id) == 1
    assert await mark_usage_succeeded(result.usage.id, ['/api/v1/files/file-1/content']) == 1
    error = SafeProviderError(code='provider_error', summary='secret\nmessage')
    assert await mark_usage_failed(result.usage.id, error) == 0
    assert await mark_stale_usage_unknown(int(time.time()) + 1) == 0
    async with service_database() as session:
        usage = await session.get(CreditUsage, result.usage.id)
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
    assert usage is not None
    assert usage.status == 'succeeded'
    assert usage.result_snapshot == {'urls': ['/api/v1/files/file-1/content']}
    assert usage.error_snapshot is None
    assert account is not None
    assert account.balance == 7


@pytest.mark.asyncio
async def test_reconciliation_recognizes_automatic_refund_and_mock_mode(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'mock-refund-user')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'mock-refund-key')
    async with service_database() as session, session.begin():
        usage = await session.get(CreditUsage, result.usage.id)
        usage.request_snapshot = {**usage.request_snapshot, 'execution_mode': 'mock'}

    assert await mark_usage_invoking(result.usage.id) == 1
    assert (
        await mark_usage_failed(
            result.usage.id,
            SafeProviderError(code='mock_failed', summary='Mock generation failed'),
            restore_prepaid=True,
        )
        == 1
    )

    async with service_database() as session:
        page = await list_reconciliation_cases(session, ReconciliationQuery())

    assert page.total == 1
    assert page.items[0].execution_mode == 'mock'
    assert page.items[0].compensation_ledger_id is not None


@pytest.mark.asyncio
async def test_success_snapshot_update_does_not_mutate_shared_column_type(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'snapshot-column-user')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))

    async with service_database() as session:
        first = await begin_image_usage(session, user, image_context(), 'snapshot-first')
        second = await begin_image_usage(session, user, image_context(), 'snapshot-second')

    assert await mark_usage_invoking(first.usage.id) == 1
    assert await mark_usage_invoking(second.usage.id) == 1
    assert await mark_usage_succeeded(first.usage.id, ['/api/v1/files/file-1/content']) == 1
    assert isinstance(CreditUsage.__table__.c.result_snapshot.type, JSONField)

    async with service_database() as session, session.begin():
        await session.execute(
            update(CreditUsage)
            .where(CreditUsage.id == second.usage.id)
            .values(result_snapshot={'urls': ['/api/v1/files/file-2/content']})
        )

    async with service_database() as session:
        usage = await session.get(CreditUsage, second.usage.id)
    assert usage is not None
    assert usage.result_snapshot == {'urls': ['/api/v1/files/file-2/content']}


@pytest.mark.asyncio
async def test_terminal_failed_and_unknown_usages_replay_without_repricing(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'terminal-user')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        failed = await begin_image_usage(session, user, image_context(), 'failed-key')
    assert await mark_usage_invoking(failed.usage.id) == 1
    error = SafeProviderError(code='provider_error', summary='safe\nsummary')
    assert await mark_usage_failed(failed.usage.id, error) == 1

    async with service_database() as session:
        await begin_image_usage(session, user, image_context(), 'unknown-key')
    assert await mark_stale_usage_unknown(int(time.time()) + 1) == 1

    async with service_database() as session, session.begin():
        await session.execute(CreditPrice.__table__.delete())
    async with service_database() as session:
        failed_replay = await begin_image_usage(session, user, image_context(), 'failed-key')
        unknown_replay = await begin_image_usage(session, user, image_context(), 'unknown-key')
    assert failed_replay.outcome == 'failed'
    assert failed_replay.usage.error_snapshot == {'code': 'provider_error', 'summary': 'safesummary'}
    assert unknown_replay.outcome == 'unknown'


@pytest.mark.asyncio
async def test_usage_results_reject_external_urls_and_sanitize_provider_errors(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'result-user')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'result-key')
    assert await mark_usage_invoking(result.usage.id) == 1

    with pytest.raises(CreditError) as raised:
        await mark_usage_succeeded(result.usage.id, ['https://provider.example/image.png'])
    assert raised.value.code == 'provider_failed'
    oversized = SafeProviderError(code='provider_error', summary='first\nsecond\t' + ('x' * 600))
    assert await mark_usage_failed(result.usage.id, oversized) == 1
    async with service_database() as session:
        usage = await session.get(CreditUsage, result.usage.id)
    assert usage is not None
    assert usage.error_snapshot is not None
    assert '\n' not in usage.error_snapshot['summary']
    assert '\t' not in usage.error_snapshot['summary']
    assert len(usage.error_snapshot['summary']) <= 512


@pytest.mark.parametrize(
    ('price_state', 'expected_code'),
    [
        ('missing', 'price_not_configured'),
        ('disabled', 'price_not_configured'),
        ('incomplete', 'price_rule_incomplete'),
    ],
)
@pytest.mark.asyncio
async def test_price_rejection_does_not_reserve_idempotency_key(service_database, price_state, expected_code) -> None:
    user = await create_user(service_database, f'price-{price_state}-user')
    await credit_user(service_database, user)
    if price_state == 'disabled':
        await add_price(service_database, enabled=False)
    elif price_state == 'incomplete':
        await add_price(service_database, base_price='NaN')

    async with service_database() as session:
        with pytest.raises(CreditError) as raised:
            await begin_image_usage(session, user, image_context(), 'price-retry-key')
    assert raised.value.code == expected_code
    async with service_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user.id))
        usage_count = await session.scalar(select(func.count()).select_from(CreditUsage))
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
async def test_usage_ledger_insert_failure_rolls_back_claim_and_debit(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'ledger-failure-user')
    await credit_user(service_database, user)
    await add_price(service_database)

    async def fail_insert(*_args, **_kwargs):
        raise RuntimeError('usage ledger storage failed')

    monkeypatch.setattr(credit_service, 'insert_ledger', fail_insert)
    async with service_database() as session:
        with pytest.raises(RuntimeError, match='usage ledger storage failed'):
            await begin_image_usage(session, user, image_context(), 'ledger-failure-key')
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
async def test_precharge_metrics_emit_only_after_the_commit_boundary(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'metric-commit-user')
    await credit_user(service_database, user)
    await add_price(service_database)
    ordering: list[str] = []
    monkeypatch.setattr(
        credit_service.credit_metrics,
        'debit_succeeded',
        lambda **_kwargs: ordering.append('debit-metric'),
    )
    monkeypatch.setattr(
        credit_service.credit_metrics,
        'usage_status',
        lambda **_kwargs: ordering.append('status-metric'),
    )

    async with service_database() as session:

        @event.listens_for(session.sync_session, 'after_commit')
        def record_commit(_session) -> None:
            ordering.append('committed')

        await begin_image_usage(session, user, image_context(), 'metric-commit-key')

    assert ordering == ['committed', 'debit-metric', 'status-metric']


@pytest.mark.asyncio
async def test_precharge_commits_before_the_provider_boundary(service_database) -> None:
    user = await create_user(service_database, 'commit-user')
    await credit_user(service_database, user)
    await add_price(service_database)
    ordering: list[str] = []

    async with service_database() as session:

        @event.listens_for(session.sync_session, 'after_commit')
        def record_commit(_session) -> None:
            ordering.append('committed')

        result = await begin_image_usage(session, user, image_context(), 'commit-key')
        ordering.append('provider')

    async with service_database() as session:
        persisted = await session.get(CreditUsage, result.usage.id)
    assert ordering == ['committed', 'provider']
    assert persisted is not None
    assert persisted.status == 'debited'


@pytest.mark.asyncio
async def test_user_ledger_exposes_bounded_usage_status_and_pricing_snapshot(service_database) -> None:
    user = await create_user(service_database, 'ledger-ui-user')
    await credit_user(service_database, user)
    await add_price(service_database)
    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'ledger-ui-key')
    async with service_database() as session, session.begin():
        await session.execute(
            CreditUsage.__table__.update()
            .where(CreditUsage.id == result.usage.id)
            .values(status='failed', error_snapshot={'code': 'provider_error', 'summary': 'safe summary'})
        )
    async with service_database() as session:
        page = await credit_service.list_user_ledger(session, user.id, UserLedgerQuery(limit=10))

    item = next(item for item in page.items if item.entry_type == 'consumption')
    assert item.usage_status == 'failed'
    assert item.pricing_snapshot is not None
    assert item.pricing_snapshot['charged_credits'] == 3
    assert 'error_snapshot' not in item.pricing_snapshot


@pytest.mark.asyncio
async def test_empty_provider_result_does_not_mark_usage_succeeded(service_database, monkeypatch) -> None:
    user = await create_user(service_database, 'empty-result-user')
    await credit_user(service_database, user)
    await add_price(service_database)
    monkeypatch.setattr(credit_service, 'credit_session', lambda: credit_session_for_test(service_database))
    async with service_database() as session:
        result = await begin_image_usage(session, user, image_context(), 'empty-result-key')
    assert await mark_usage_invoking(result.usage.id) == 1

    with pytest.raises(CreditError) as raised:
        await mark_usage_succeeded(result.usage.id, [])
    assert raised.value.code == 'provider_failed'
    async with service_database() as session:
        usage = await session.get(CreditUsage, result.usage.id)
    assert usage is not None
    assert usage.status == 'invoking'
    assert usage.result_snapshot is None
