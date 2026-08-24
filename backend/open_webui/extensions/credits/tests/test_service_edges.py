from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from open_webui.extensions.credits import service
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.schemas import ReconciliationQuery, UserSnapshot
from open_webui.extensions.tests.async_test_support import (
    AsyncContext,
)
from open_webui.extensions.tests.async_test_support import (
    TransactionalSession as _Session,
)


def test_safe_provider_error_and_request_snapshot_validation() -> None:
    with pytest.raises(ValueError, match='canonical'):
        service.SafeProviderError('bad code', 'summary')
    with pytest.raises(ValueError, match='summary'):
        service.SafeProviderError('valid', 1)
    error = service.SafeProviderError('valid', 'safe\x00summary')
    assert error.summary == 'safesummary'

    context = SimpleNamespace(request_hash='hash', dimensions={}, execution_mode='mock')
    assert service._request_snapshot(context)['execution_mode'] == 'mock'
    context.execution_mode = 'invalid'
    assert 'execution_mode' not in service._request_snapshot(context)


@pytest.mark.asyncio
async def test_user_and_account_consistency_guards(monkeypatch) -> None:
    missing = SimpleNamespace(one_or_none=lambda: None)
    session = SimpleNamespace(execute=AsyncMock(return_value=missing))
    for lookup in (service._current_user_snapshot, service._current_user_for_usage):
        with pytest.raises(CreditError):
            await lookup(session, 'missing')

    anomaly = Mock()
    monkeypatch.setattr(service.credit_metrics, 'consistency_anomaly', anomaly)
    session = SimpleNamespace(scalar=AsyncMock(return_value=None))
    with pytest.raises(CreditError, match='unavailable'):
        await service._lock_and_verify_account_matches_ledger(session, 'account')
    account = SimpleNamespace(id='account', balance=3)
    session.scalar = AsyncMock(side_effect=[account, 2])
    with pytest.raises(CreditError, match='unavailable'):
        await service._lock_and_verify_account_matches_ledger(session, 'account')
    assert anomaly.call_count == 2


@pytest.mark.asyncio
async def test_usage_claim_requires_a_persisted_conflict_winner(monkeypatch) -> None:
    session = _Session()
    user = UserSnapshot(id='user', name='User', email='user@example.test')
    context = SimpleNamespace(request_hash='hash')
    monkeypatch.setattr(
        service,
        '_current_user_for_usage',
        AsyncMock(return_value=(user, 'user')),
    )
    monkeypatch.setattr(service, 'claim_usage_placeholder', AsyncMock(return_value=None))
    monkeypatch.setattr(service, 'get_usage_by_idempotency_key', AsyncMock(return_value=None))
    monkeypatch.setattr(service, '_usage_placeholder_values', lambda *_args: {})
    with pytest.raises(RuntimeError, match='not persisted'):
        await service.begin_generation_usage(session, user, context, 'key')


def test_result_url_validation_rejects_ambiguous_or_external_values() -> None:
    invalid_values = (
        '/api/v1/files/file/content',
        [],
        [1],
        [''],
        ['//host/path'],
        ['/api/v1/files/file/content?secret=1'],
        ['/api/v1/files/file/extra/content'],
    )
    for value in invalid_values:
        with pytest.raises(CreditError):
            service._safe_result_urls(value)
    assert service._safe_result_urls(['/api/v1/files/file-1/content']) == [
        '/api/v1/files/file-1/content'
    ]


@pytest.mark.asyncio
async def test_usage_state_helpers_cover_noop_and_heartbeat(monkeypatch) -> None:
    monkeypatch.setattr(service, '_update_usage_status', AsyncMock(return_value=1))
    metric = Mock()
    monkeypatch.setattr(service.credit_metrics, 'usage_status', metric)
    assert await service.mark_usage_invoking('usage') == 1
    metric.assert_called_once_with(status='invoking')

    session = _Session(execute=AsyncMock(return_value=SimpleNamespace(rowcount=None)))
    monkeypatch.setattr(service, 'credit_session', lambda: AsyncContext(session))
    assert await service.touch_usage_invoking('usage') == 0


@pytest.mark.asyncio
async def test_prepaid_restoration_guards_and_fail_transition(monkeypatch) -> None:
    session = SimpleNamespace(scalar=AsyncMock())
    for usage in (
        SimpleNamespace(exempt=True, charged_credits=1, ledger_id='ledger'),
        SimpleNamespace(exempt=False, charged_credits=0, ledger_id='ledger'),
        SimpleNamespace(exempt=False, charged_credits=1, ledger_id=None),
    ):
        await service._restore_usage_prepaid(session, usage, 1)
    session.scalar.assert_not_awaited()

    usage = SimpleNamespace(exempt=False, charged_credits=1, ledger_id='ledger')
    session.scalar = AsyncMock(side_effect=[SimpleNamespace(id='refund')])
    await service._restore_usage_prepaid(session, usage, 1)
    session.scalar = AsyncMock(side_effect=[None, None])
    with pytest.raises(CreditError, match='unavailable'):
        await service._restore_usage_prepaid(session, usage, 1)

    inactive = SimpleNamespace(status='failed')
    session = _Session(scalar=AsyncMock(return_value=inactive), flush=AsyncMock())
    monkeypatch.setattr(service, 'credit_session', lambda: AsyncContext(session))
    assert await service.mark_usage_failed(
        'usage',
        service.SafeProviderError('failed', 'summary'),
        restore_prepaid=False,
    ) == 0

    active = SimpleNamespace(status='invoking')
    session.scalar.return_value = active
    metric = Mock()
    monkeypatch.setattr(service.credit_metrics, 'usage_status', metric)
    assert await service.mark_usage_failed(
        'usage',
        service.SafeProviderError('failed', 'summary'),
        restore_prepaid=False,
    ) == 1
    assert active.status == 'failed'
    metric.assert_called_once_with(status='failed')


def test_reconciliation_filters_and_validation_cover_all_options() -> None:
    refund = SimpleNamespace(id=SimpleNamespace(is_not=lambda _value: 'not-null', is_=lambda _value: 'null'))
    query = ReconciliationQuery(status='failed', compensated=True, user_id='user')
    assert len(service._reconciliation_conditions(query, refund)) == 7
    query = ReconciliationQuery(compensated=False)
    assert len(service._reconciliation_conditions(query, refund)) == 5

    with pytest.raises(CreditError):
        service._validate_reconcilable_usage(None)
    for usage in (
        SimpleNamespace(status='succeeded', exempt=False, charged_credits=1, ledger_id='ledger'),
        SimpleNamespace(status='failed', exempt=True, charged_credits=1, ledger_id='ledger'),
    ):
        with pytest.raises(CreditError):
            service._validate_reconcilable_usage(usage)


@pytest.mark.asyncio
async def test_compensation_returns_existing_and_rejects_balance_overflow(monkeypatch) -> None:
    usage = SimpleNamespace(
        id='usage',
        status='failed',
        exempt=False,
        charged_credits=2,
        ledger_id='ledger',
        user_id='user',
        user_name_snapshot='User',
        user_email_snapshot='user@example.test',
    )
    existing = SimpleNamespace(id='refund')
    session = _Session(scalar=AsyncMock(side_effect=[usage, existing]))
    result = await service.compensate_reconciliation_case(
        session,
        'usage',
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(),
    )
    assert result == (existing, False)

    account = SimpleNamespace(id='account')
    session.scalar = AsyncMock(side_effect=[usage, None])
    monkeypatch.setattr(service, 'get_or_create_account', AsyncMock(return_value=account))
    monkeypatch.setattr(
        service,
        '_lock_and_verify_account_matches_ledger',
        AsyncMock(return_value=account),
    )
    monkeypatch.setattr(service, 'update_account_balance', AsyncMock(return_value=None))
    with pytest.raises(CreditError, match='invalid'):
        await service.compensate_reconciliation_case(
            session,
            'usage',
            SimpleNamespace(),
            SimpleNamespace(),
            SimpleNamespace(),
        )
