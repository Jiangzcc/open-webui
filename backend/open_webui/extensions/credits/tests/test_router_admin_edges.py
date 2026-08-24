from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from open_webui.extensions.credits import router_admin
from open_webui.extensions.credits.errors import CreditError

USER = SimpleNamespace(id='admin', name='Admin', email='admin@example.test')
SESSION = object()


def _request():
    return SimpleNamespace(scope={})


@pytest.fixture(autouse=True)
def _boundaries(monkeypatch):
    monkeypatch.setattr(router_admin, '_enforce_rate_limit', AsyncMock())
    monkeypatch.setattr(router_admin, '_user_snapshot', lambda _user: USER)
    monkeypatch.setattr(router_admin, '_audit_context', lambda _request: SimpleNamespace())
    monkeypatch.setattr(router_admin, '_public_error_response', lambda _error: 'public-error')
    monkeypatch.setattr(router_admin, '_unexpected_error_response', lambda _error: 'unexpected')


@pytest.mark.asyncio
async def test_redeem_admin_routes_map_public_and_unexpected_errors(monkeypatch) -> None:
    calls = (
        (
            router_admin.generate_redeem_batch,
            'create_redeem_batch',
            (SimpleNamespace(), _request()),
        ),
        (
            router_admin.get_redeem_batch_codes,
            'list_redeem_codes',
            ('batch', _request()),
        ),
        (
            router_admin.void_credit_redeem_batch,
            'void_redeem_batch',
            ('batch', _request()),
        ),
        (
            router_admin.void_credit_redeem_code,
            'void_redeem_code',
            ('batch', 'code', _request()),
        ),
    )
    for route, dependency, args in calls:
        monkeypatch.setattr(
            router_admin,
            dependency,
            AsyncMock(side_effect=CreditError(code='credit_service_unavailable')),
        )
        assert await route(*args, user=USER, session=SESSION) == 'public-error'
        monkeypatch.setattr(router_admin, dependency, AsyncMock(side_effect=RuntimeError))
        assert await route(*args, user=USER, session=SESSION) == 'unexpected'


@pytest.mark.asyncio
async def test_ledger_reconciliation_and_compensation_map_errors(monkeypatch) -> None:
    for dependency, route, args in (
        ('list_admin_ledger', router_admin.get_admin_credit_ledger, (SimpleNamespace(),)),
        (
            'list_reconciliation_cases',
            router_admin.get_credit_reconciliation_cases,
            (SimpleNamespace(),),
        ),
        (
            'compensate_reconciliation_case',
            router_admin.compensate_credit_reconciliation_case,
            ('usage', SimpleNamespace(), _request()),
        ),
    ):
        for error, expected in (
            (CreditError(code='credit_service_unavailable'), 'public-error'),
            (RuntimeError(), 'unexpected'),
        ):
            monkeypatch.setattr(router_admin, dependency, AsyncMock(side_effect=error))
            if route is router_admin.get_admin_credit_ledger:
                result = await route(*args, _user=USER, session=SESSION)
            else:
                result = await route(*args, user=USER, session=SESSION)
            assert result == expected


@pytest.mark.asyncio
async def test_adjustment_rejects_bad_audit_and_maps_service_errors(monkeypatch) -> None:
    body = SimpleNamespace()
    monkeypatch.setattr(router_admin, '_audit_context', lambda _request: (_ for _ in ()).throw(ValueError()))
    with pytest.raises(HTTPException) as captured:
        await router_admin.create_credit_adjustment(
            'target',
            body,
            _request(),
            user=USER,
            session=SESSION,
        )
    assert captured.value.status_code == 422

    monkeypatch.setattr(router_admin, '_audit_context', lambda _request: SimpleNamespace())
    for error, expected in (
        (CreditError(code='credit_service_unavailable'), 'public-error'),
        (RuntimeError(), 'unexpected'),
    ):
        monkeypatch.setattr(router_admin, 'adjust_balance', AsyncMock(side_effect=error))
        assert await router_admin.create_credit_adjustment(
            'target',
            body,
            _request(),
            user=USER,
            session=SESSION,
        ) == expected


@pytest.mark.asyncio
async def test_account_listing_fetches_balances_and_maps_database_failure(monkeypatch) -> None:
    item = SimpleNamespace(id='user', name='User', email='user@example.test')
    monkeypatch.setattr(
        router_admin,
        'get_credit_users',
        AsyncMock(return_value={'users': [item], 'total': 1}),
    )
    session = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(all=lambda: [('user', 7)])
        )
    )
    result = await router_admin.get_credit_accounts(session=session, _user=USER)
    assert result['items'][0]['balance'] == 7
    session.execute.side_effect = RuntimeError
    assert await router_admin.get_credit_accounts(session=session, _user=USER) == 'unexpected'


def test_price_validation_and_audit_helpers_reject_invalid_inputs(monkeypatch) -> None:
    with pytest.raises(HTTPException) as captured:
        router_admin._validate_price_dimensions(
            'unknown',
            'unknown',
            SimpleNamespace(dimensions=[]),
        )
    assert captured.value.status_code == 422

    monkeypatch.setattr(router_admin, '_audit_context', lambda _request: (_ for _ in ()).throw(ValueError()))
    with pytest.raises(HTTPException) as captured:
        router_admin._request_price_audit(_request())
    assert captured.value.status_code == 422


@pytest.mark.asyncio
async def test_price_mutation_error_boundaries(monkeypatch) -> None:
    request = _request()
    monkeypatch.setattr(router_admin, '_request_price_audit', lambda _request: SimpleNamespace())
    body = router_admin.PriceUpdateRequest(enabled=False)
    session = SimpleNamespace(
        begin=lambda: (_ for _ in ()).throw(RuntimeError('begin')),
        get=AsyncMock(),
    )
    assert await router_admin.update_credit_price(
        'price',
        body,
        request,
        user=USER,
        session=session,
    ) == 'unexpected'

    class _Context:
        async def __aenter__(self):
            return None

        async def __aexit__(self, *_args):
            return None

    session.begin = lambda: _Context()
    session.get.return_value = None
    with pytest.raises(HTTPException) as captured:
        await router_admin.update_credit_price(
            'price',
            body,
            request,
            user=USER,
            session=session,
        )
    assert captured.value.status_code == 404

    session.get.return_value = SimpleNamespace(
        id='price',
        service_type='image',
        resource_id='model',
        action='text-to-image',
        base_price='1',
        enabled=True,
        created_at=1,
        updated_at=1,
    )
    session.delete = AsyncMock(side_effect=RuntimeError)
    assert await router_admin.delete_credit_price(
        'price',
        request,
        user=USER,
        session=session,
    ) == 'unexpected'
