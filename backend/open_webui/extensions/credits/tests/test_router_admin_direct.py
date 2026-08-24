from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from open_webui.extensions.credits import router_admin
from open_webui.extensions.credits.errors import CreditError

USER = SimpleNamespace(id='admin-1', name='Admin', email='admin@example.test', role='admin')
SESSION = object()


class _Page:
    def __init__(self, **values):
        self.values = values

    def model_dump(self):
        return dict(self.values)


def _request():
    return SimpleNamespace(
        scope={},
        state=SimpleNamespace(token=None),
        headers={'X-Request-ID': 'request-1'},
        cookies={'token': 'session'},
        client=SimpleNamespace(host='127.0.0.1'),
    )


@pytest.fixture(autouse=True)
def _admission(monkeypatch):
    monkeypatch.setattr(router_admin, '_enforce_rate_limit', AsyncMock())
    monkeypatch.setattr(
        router_admin,
        '_audit_context',
        lambda _request: SimpleNamespace(request_id='request-1'),
    )


@pytest.mark.asyncio
async def test_redeem_admin_routes_cover_success_and_redaction(monkeypatch) -> None:
    page = _Page(items=[], total=0)
    monkeypatch.setattr(router_admin, 'list_redeem_batches', AsyncMock(return_value=page))
    assert await router_admin.get_redeem_batches(user=USER, session=SESSION) == page.model_dump()

    created = _Page(batch_id='batch-1', codes=['ONE-TIME'])
    monkeypatch.setattr(router_admin, 'create_redeem_batch', AsyncMock(return_value=created))
    request = _request()
    response = await router_admin.generate_redeem_batch(SimpleNamespace(), request, user=USER, session=SESSION)
    assert response.status_code == 201
    assert request.scope['audit_redact_bodies'] == frozenset({'response'})

    monkeypatch.setattr(router_admin, 'list_redeem_codes', AsyncMock(return_value=page))
    request = _request()
    response = await router_admin.get_redeem_batch_codes('batch', request, user=USER, session=SESSION)
    assert response.headers['cache-control'] == 'no-store, max-age=0'
    assert request.scope['audit_redact_bodies'] == frozenset({'response'})

    monkeypatch.setattr(router_admin, 'list_redeem_audit', AsyncMock(return_value=page))
    assert await router_admin.get_redeem_batch_audit('batch', user=USER, session=SESSION) == page.model_dump()

    monkeypatch.setattr(router_admin, 'void_redeem_batch', AsyncMock(return_value=2))
    assert await router_admin.void_credit_redeem_batch('batch', _request(), user=USER, session=SESSION) == {
        'voided_count': 2
    }
    monkeypatch.setattr(router_admin, 'void_redeem_code', AsyncMock(return_value=True))
    assert await router_admin.void_credit_redeem_code(
        'batch',
        'code',
        _request(),
        user=USER,
        session=SESSION,
    ) == {'voided': True}


@pytest.mark.asyncio
async def test_redeem_admin_routes_return_public_and_unexpected_errors(monkeypatch) -> None:
    public = JSONResponse(status_code=409, content={'code': 'public'})
    unexpected = JSONResponse(status_code=503, content={'code': 'unexpected'})
    monkeypatch.setattr(router_admin, '_public_error_response', lambda _error: public)
    monkeypatch.setattr(router_admin, '_unexpected_error_response', lambda _error: unexpected)

    for service_name, route_call in (
        ('list_redeem_batches', lambda: router_admin.get_redeem_batches(user=USER, session=SESSION)),
        (
            'list_redeem_audit',
            lambda: router_admin.get_redeem_batch_audit('batch', user=USER, session=SESSION),
        ),
    ):
        service = AsyncMock(side_effect=CreditError(code='credit_service_unavailable'))
        monkeypatch.setattr(router_admin, service_name, service)
        assert await route_call() is public
        service.side_effect = RuntimeError('db')
        assert await route_call() is unexpected


@pytest.mark.asyncio
async def test_repair_ledger_reconciliation_and_adjustment_routes(monkeypatch) -> None:
    ledger = SimpleNamespace(
        id='ledger-1',
        balance_before=3,
        balance_after=5,
        request_id='repair:incident',
        amount=2,
        request_source='internal_admin',
    )
    monkeypatch.setattr(router_admin, 'repair_account_from_ledger', AsyncMock(return_value=ledger))
    body = SimpleNamespace(
        incident_id='incident',
        expected_balance=3,
        note='confirmed',
        backup_confirmed=True,
    )
    repaired = await router_admin.repair_credit_account_from_ledger(
        'user-1',
        body,
        _request(),
        user=USER,
        session=SESSION,
    )
    assert repaired['balance_after'] == 5
    router_admin.repair_account_from_ledger.side_effect = router_admin.CreditRepairError('unsafe')
    with pytest.raises(HTTPException) as invalid:
        await router_admin.repair_credit_account_from_ledger(
            'user-1',
            body,
            _request(),
            user=USER,
            session=SESSION,
        )
    assert invalid.value.status_code == 422

    page = _Page(items=[], next_cursor=None)
    monkeypatch.setattr(router_admin, 'list_admin_ledger', AsyncMock(return_value=page))
    assert await router_admin.get_admin_credit_ledger(
        SimpleNamespace(),
        _user=USER,
        session=SESSION,
    ) == page.model_dump()
    monkeypatch.setattr(router_admin, 'list_reconciliation_cases', AsyncMock(return_value=page))
    assert await router_admin.get_credit_reconciliation_cases(
        SimpleNamespace(),
        user=USER,
        session=SESSION,
    ) == page.model_dump()

    monkeypatch.setattr(
        router_admin,
        'compensate_reconciliation_case',
        AsyncMock(return_value=(ledger, True)),
    )
    compensated = await router_admin.compensate_credit_reconciliation_case(
        'usage-1',
        SimpleNamespace(),
        _request(),
        user=USER,
        session=SESSION,
    )
    assert compensated == {'ledger_id': 'ledger-1', 'created': True, 'amount': 2}

    monkeypatch.setattr(router_admin, 'adjust_balance', AsyncMock(return_value=ledger))
    adjusted = await router_admin.create_credit_adjustment(
        'user-1',
        SimpleNamespace(),
        _request(),
        user=USER,
        session=SESSION,
    )
    assert adjusted['ledger_id'] == 'ledger-1'


@pytest.mark.asyncio
async def test_account_and_price_listing_routes(monkeypatch) -> None:
    with pytest.raises(HTTPException):
        await router_admin.get_credit_accounts(skip=-1, _user=USER, session=SESSION)

    users = {
        'users': [SimpleNamespace(id='user-1', name='User', email='user@example.test')],
        'total': 1,
    }
    monkeypatch.setattr(router_admin, 'get_credit_users', AsyncMock(return_value=users))
    session = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(all=lambda: [('user-1', 7)])
        )
    )
    result = await router_admin.get_credit_accounts(query='User', _user=USER, session=session)
    assert result['items'][0]['balance'] == 7

    monkeypatch.setattr(
        router_admin,
        'list_admin_credit_prices',
        AsyncMock(
            return_value=(
                [
                    SimpleNamespace(
                        id='price-1',
                        service_type='image',
                        resource_id='model',
                        action='text-to-image',
                        base_price='1',
                        rules={},
                        enabled=True,
                        updated_at=1,
                    )
                ],
                1,
            )
        ),
    )
    prices = await router_admin.list_credit_prices(SimpleNamespace(), session=SESSION)
    assert prices['total'] == 1

    dimensions = await router_admin.get_credit_dimensions('image')
    assert dimensions['service_type'] == 'image'
    with pytest.raises(HTTPException):
        await router_admin.get_credit_dimensions('unknown')


@pytest.mark.asyncio
async def test_admin_service_errors_are_sanitized(monkeypatch) -> None:
    response = JSONResponse(status_code=503, content={'code': 'unavailable'})
    monkeypatch.setattr(router_admin, '_unexpected_error_response', lambda _error: response)
    monkeypatch.setattr(router_admin, 'get_credit_users', AsyncMock(side_effect=RuntimeError('private db detail')))
    assert await router_admin.get_credit_accounts(_user=USER, session=SESSION) is response
    monkeypatch.setattr(
        router_admin,
        'list_admin_credit_prices',
        AsyncMock(side_effect=RuntimeError('private db detail')),
    )
    assert await router_admin.list_credit_prices(SimpleNamespace(), session=SESSION) is response


@pytest.mark.asyncio
async def test_price_crud_directly_covers_transaction_and_event_boundaries(monkeypatch) -> None:
    publish = AsyncMock()
    monkeypatch.setattr(router_admin, '_publish_price_event', publish)
    monkeypatch.setattr(router_admin, 'time', lambda: 100.0)
    body = router_admin.PriceRequest.model_validate(
        {
            'service_type': 'image',
            'resource_id': 'model-a',
            'action': 'text-to-image',
            'base_price': '1',
            'rules': {'schema_version': 1, 'dimensions': []},
            'enabled': True,
        }
    )
    session = _PriceSession()
    created = await router_admin.create_credit_price(body, _request(), user=USER, session=session)
    assert created['resource_id'] == 'model-a'
    assert session.added is not None
    publish.assert_awaited_once()

    session.scalar_result = 'existing'
    with pytest.raises(HTTPException) as duplicate:
        await router_admin.create_credit_price(body, _request(), user=USER, session=session)
    assert duplicate.value.status_code == 409

    price = session.added
    session.get_result = price
    update = router_admin.PriceUpdateRequest(enabled=False)
    changed = await router_admin.update_credit_price('price', update, _request(), user=USER, session=session)
    assert changed['enabled'] is False
    assert price.updated_at == 101

    session.get_result = None
    with pytest.raises(HTTPException) as missing:
        await router_admin.update_credit_price('missing', update, _request(), user=USER, session=session)
    assert missing.value.status_code == 404

    session.get_result = price
    deleted = await router_admin.delete_credit_price('price', _request(), user=USER, session=session)
    assert deleted == {'id': 'price'}
    assert session.deleted is price
    session.get_result = None
    with pytest.raises(HTTPException):
        await router_admin.delete_credit_price('missing', _request(), user=USER, session=session)


class _PriceSession:
    def __init__(self):
        self.scalar_result = None
        self.get_result = None
        self.added = None
        self.deleted = None

    def begin(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def scalar(self, _statement):
        return self.scalar_result

    def add(self, value):
        self.added = value

    async def flush(self):
        return None

    async def get(self, _model, _identifier):
        return self.get_result

    async def delete(self, value):
        self.deleted = value
