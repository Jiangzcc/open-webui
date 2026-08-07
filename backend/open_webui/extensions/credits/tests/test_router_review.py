import asyncio
from hashlib import sha256
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from open_webui.extensions.credits.models import CreditAccount, CreditLedger, CreditPrice, CreditUsage
from sqlalchemy import func, select

from .router_test_support import AuthenticatedUser


def _admin_app(credits_router, session_dependency):
    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = session_dependency
    return app


def test_credit_error_response_is_the_direct_public_envelope(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router
    from open_webui.extensions.credits.errors import CreditError

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def unavailable(_session, _user):
        raise CreditError(code='credit_service_unavailable')

    monkeypatch.setattr(credits_router, 'get_balance', unavailable)

    response = TestClient(app, raise_server_exceptions=False).get('/api/v1/credits/me')

    assert response.status_code == 503
    assert response.json() == {
        'code': 'credit_service_unavailable',
        'message': 'Credit service is unavailable',
        'context': {},
    }


def test_admin_quote_requires_a_configured_price(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    async def prepare(_request, _image_input, _metadata, _user):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'text-to-image',
                        'dimensions': {},
                        'request_hash': 'admin-unconfigured',
                    },
                )()
            },
        )()

    async def balance(_session, _user_id):
        return 0

    async def no_price(_session, _service_type, _resource_id, _action):
        return None

    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', no_price)

    result = asyncio.run(
        credits_router.quote_image(
            object(),
            AuthenticatedUser(id='admin-1', name='Admin', email='admin@example.test', role='admin'),
            {'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
        )
    )

    assert result == {
        'balance': 0,
        'sufficient': False,
        'exempt': False,
        'configured': False,
        'factors': [],
        'charged_credits': None,
        'error': 'price_not_configured',
    }


def test_admin_quote_computes_configured_price_like_an_ordinary_user(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    async def prepare(*_args):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'text-to-image',
                        'dimensions': {},
                        'request_hash': 'admin-configured',
                    },
                )()
            },
        )()

    async def balance(*_args):
        return 10

    async def price(*_args):
        return type('Price', (), {'id': 'price-admin', 'updated_at': 1, 'enabled': True})()

    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', price)
    monkeypatch.setattr(
        credits_router,
        'compute_price',
        lambda *_: SimpleNamespace(charged_credits=3, factors=[]),
    )

    result = asyncio.run(
        credits_router.quote_image(
            object(),
            AuthenticatedUser(id='admin-1', name='Admin', email='admin@example.test', role='admin'),
            {'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
        )
    )

    assert result['configured'] is True
    assert result['exempt'] is False
    assert result['charged_credits'] == 3


def test_admin_quote_reports_incomplete_price_as_unconfigured(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router
    from open_webui.extensions.credits.errors import CreditError

    async def prepare(*_args):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'text-to-image',
                        'dimensions': {},
                        'request_hash': 'admin-incomplete',
                    },
                )()
            },
        )()

    async def balance(*_args):
        return 0

    async def price(*_args):
        return type('Price', (), {'id': 'price-a', 'updated_at': 1, 'enabled': True, 'rules': {'bad': True}})()

    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', price)

    def incomplete(*_args):
        raise CreditError(code='price_rule_incomplete')

    monkeypatch.setattr(credits_router, 'compute_price', incomplete)

    result = asyncio.run(
        credits_router.quote_image(
            object(),
            AuthenticatedUser(id='admin-1', name='Admin', email='admin@example.test', role='admin'),
            {'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
        )
    )

    assert result['configured'] is False
    assert result['exempt'] is False
    assert result['error'] == 'price_rule_incomplete'


def test_quote_cache_is_bounded(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    async def prepare(_request, image_input, _metadata, _user):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': image_input.model,
                        'action': 'text-to-image',
                        'dimensions': {},
                        'request_hash': f'hash:{image_input.model}',
                    },
                )()
            },
        )()

    async def balance(_session, _user_id):
        return 10

    async def price(_session, _service_type, resource_id, _action):
        return type('Price', (), {'id': f'price:{resource_id}', 'updated_at': 1, 'enabled': True})()

    credits_router._quote_cache.clear()
    monkeypatch.setattr(credits_router, 'CREDIT_QUOTE_CACHE_MAX_ENTRIES', 2, raising=False)
    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', price)
    monkeypatch.setattr(
        credits_router,
        'compute_price',
        lambda *_: type('Quote', (), {'charged_credits': 1, 'factors': ()})(),
    )
    user = AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test')

    for index in range(3):
        asyncio.run(
            credits_router.quote_image(
                object(),
                user,
                {
                    'resource_id': f'model-{index}',
                    'action': 'text-to-image',
                    'prompt': 'safe test prompt',
                    'dimensions': {},
                },
            )
        )

    assert len(credits_router._quote_cache) == 2


def test_quote_cache_invalidates_when_a_price_is_recreated(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    current_price = [type('Price', (), {'id': 'price-a', 'updated_at': 1, 'enabled': True})()]
    compute_calls = []

    async def prepare(*_args):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'text-to-image',
                        'dimensions': {},
                        'request_hash': 'same-request',
                    },
                )()
            },
        )()

    async def balance(*_args):
        return 10

    async def price(*_args):
        return current_price[0]

    def compute(active_price, *_args):
        compute_calls.append(active_price.id)
        return type('Quote', (), {'charged_credits': 1, 'factors': ()})()

    credits_router._quote_cache.clear()
    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', price)
    monkeypatch.setattr(credits_router, 'compute_price', compute)
    user = AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test')
    payload = {'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}}

    asyncio.run(credits_router.quote_image(object(), user, payload))
    current_price[0] = type('Price', (), {'id': 'price-b', 'updated_at': 1, 'enabled': True})()
    asyncio.run(credits_router.quote_image(object(), user, payload))

    assert compute_calls == ['price-a', 'price-b']


def test_quote_input_rejects_invalid_string_dimensions_before_adapter() -> None:
    from open_webui.extensions.credits import router as credits_router
    from open_webui.extensions.credits.errors import CreditError

    with pytest.raises(CreditError, match='Price rule is incomplete'):
        credits_router._quote_image_input(
            {
                'resource_id': 'model-a',
                'action': 'text-to-image',
                'prompt': 'safe test prompt',
                'dimensions': {'size': 1024},
            }
        )


def test_quote_cache_key_keeps_actions_separate(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    compute_calls = []

    async def prepare(action):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': action,
                        'dimensions': {},
                        'request_hash': 'forced-shared-hash',
                    },
                )()
            },
        )()

    async def prepare_generation(*_args):
        return await prepare('text-to-image')

    async def prepare_edit(*_args):
        return await prepare('image-to-image')

    async def balance(*_args):
        return 10

    async def price(*_args):
        return type('Price', (), {'updated_at': 1, 'enabled': True})()

    def compute(*_args):
        compute_calls.append(True)
        return type('Quote', (), {'charged_credits': 1, 'factors': ()})()

    credits_router._quote_cache.clear()
    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare_generation)
    monkeypatch.setattr(credits_router, 'prepare_edit_call', prepare_edit)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', price)
    monkeypatch.setattr(credits_router, 'compute_price', compute)
    user = AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test')

    for action in ('text-to-image', 'image-to-image'):
        asyncio.run(
            credits_router.quote_image(
                object(),
                user,
                {
                    'resource_id': 'model-a',
                    'action': action,
                    'prompt': 'safe test prompt',
                    'image': 'reference' if action == 'image-to-image' else None,
                    'dimensions': {},
                },
            )
        )

    assert len(compute_calls) == 2


def test_cached_quote_hit_records_a_success_metric(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    metrics = []

    async def prepare_generation(*_args):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'text-to-image',
                        'dimensions': {},
                        'request_hash': 'cached-request',
                    },
                )()
            },
        )()

    async def balance(*_args):
        return 10

    async def configured_price(*_args):
        return type('Price', (), {'id': 'price-a', 'updated_at': 1, 'enabled': True})()

    credits_router._quote_cache.clear()
    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare_generation)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', configured_price)
    monkeypatch.setattr(
        credits_router.credit_metrics,
        'quote_succeeded',
        lambda **attributes: metrics.append(attributes),
    )
    credits_router._quote_cache[('user-1', 'price-a', 'text-to-image:cached-request', 1)] = (
        float('inf'),
        {
            'balance': 10,
            'sufficient': True,
            'exempt': False,
            'configured': True,
            'factors': [],
            'charged_credits': 2,
            'error': None,
        },
    )
    user = AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test')

    asyncio.run(
        credits_router.quote_image(
            object(),
            user,
            {
                'resource_id': 'model-a',
                'action': 'text-to-image',
                'prompt': 'safe test prompt',
                'dimensions': {},
            },
        )
    )

    assert metrics == [{'model': 'model-a', 'action': 'text-to-image', 'charged_credits': 2}]


def test_price_create_rejects_unregistered_dimensions_before_database_access() -> None:
    from open_webui.extensions.credits import router as credits_router

    app = _admin_app(credits_router, lambda: object())
    response = TestClient(app, raise_server_exceptions=False).post(
        '/api/v1/credits/admin/prices',
        json={
            'service_type': 'image',
            'resource_id': 'model-a',
            'action': 'text-to-image',
            'base_price': '1',
            'rules': {
                'schema_version': 1,
                'dimensions': [{'kind': 'quantity', 'key': 'unregistered_dimension'}],
            },
        },
    )

    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'invalid_price_dimensions'


def test_price_create_rejects_quantity_rules_for_non_quantity_dimensions() -> None:
    from open_webui.extensions.credits import router as credits_router

    app = _admin_app(credits_router, lambda: object())
    response = TestClient(app, raise_server_exceptions=False).post(
        '/api/v1/credits/admin/prices',
        json={
            'service_type': 'image',
            'resource_id': 'model-a',
            'action': 'text-to-image',
            'base_price': '1',
            'rules': {
                'schema_version': 1,
                'dimensions': [{'kind': 'quantity', 'key': 'size'}],
            },
        },
    )

    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'invalid_price_dimensions'


def test_price_create_requires_default_for_discrete_dimensions() -> None:
    from open_webui.extensions.credits import router as credits_router

    response = TestClient(_admin_app(credits_router, lambda: object()), raise_server_exceptions=False).post(
        '/api/v1/credits/admin/prices',
        json={
            'service_type': 'image',
            'resource_id': 'model-a',
            'action': 'text-to-image',
            'base_price': '1',
            'rules': {
                'schema_version': 1,
                'dimensions': [{'kind': 'exact_map', 'key': 'quality', 'values': {'hd': '2'}}],
            },
        },
    )

    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'incomplete_price_dimension'


def test_price_update_rejects_unregistered_rules_without_committing(router_database, monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    async def seed() -> None:
        async with router_database() as session, session.begin():
            session.add(
                CreditPrice(
                    id='price-1',
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

    asyncio.run(seed())

    async def database_session():
        async with router_database() as session:
            yield session

    events = []

    async def publish(*_args, **_kwargs):
        events.append(True)

    monkeypatch.setattr(credits_router, 'publish_credit_price_event', publish)
    response = TestClient(_admin_app(credits_router, database_session), raise_server_exceptions=False).put(
        '/api/v1/credits/admin/prices/price-1',
        json={
            'rules': {
                'schema_version': 1,
                'dimensions': [{'kind': 'quantity', 'key': 'size'}],
            }
        },
    )

    async def persisted_rules():
        async with router_database() as session:
            return (await session.get(CreditPrice, 'price-1')).rules

    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'invalid_price_dimensions'
    assert asyncio.run(persisted_rules()) == {'schema_version': 1, 'dimensions': []}
    assert events == []


def test_price_update_advances_the_cache_version_within_the_same_second(router_database, monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    async def seed() -> None:
        async with router_database() as session, session.begin():
            session.add(
                CreditPrice(
                    id='price-1',
                    service_type='image',
                    resource_id='model-a',
                    action='text-to-image',
                    base_price='1',
                    rules={'schema_version': 1, 'dimensions': []},
                    enabled=True,
                    created_at=100,
                    updated_at=100,
                )
            )

    asyncio.run(seed())

    async def database_session():
        async with router_database() as session:
            yield session

    async def publish(*_args, **_kwargs):
        return None

    monkeypatch.setattr(credits_router, 'time', lambda: 100.0)
    monkeypatch.setattr(credits_router, 'publish_credit_price_event', publish)
    response = TestClient(_admin_app(credits_router, database_session), raise_server_exceptions=False).put(
        '/api/v1/credits/admin/prices/price-1', json={'enabled': False}
    )

    assert response.status_code == 200
    assert response.json()['updated_at'] == 101


def test_price_create_returns_conflict_for_an_existing_business_key(router_database, monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    async def seed() -> None:
        async with router_database() as session, session.begin():
            session.add(
                CreditPrice(
                    id='existing-price',
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

    asyncio.run(seed())

    async def database_session():
        async with router_database() as session:
            yield session

    events = []

    async def publish(*_args, **_kwargs):
        events.append(True)

    monkeypatch.setattr(credits_router, 'publish_credit_price_event', publish)
    response = TestClient(_admin_app(credits_router, database_session), raise_server_exceptions=False).post(
        '/api/v1/credits/admin/prices',
        json={
            'service_type': 'image',
            'resource_id': 'model-a',
            'action': 'text-to-image',
            'base_price': '2',
            'rules': {'schema_version': 1, 'dimensions': []},
        },
    )

    assert response.status_code == 409
    assert response.json()['detail']['code'] == 'price_already_exists'
    assert events == []


def test_invalid_price_event_request_id_is_rejected_before_the_price_is_committed(router_database) -> None:
    from open_webui.extensions.credits import router as credits_router

    async def database_session():
        async with router_database() as session:
            yield session

    response = TestClient(_admin_app(credits_router, database_session), raise_server_exceptions=False).post(
        '/api/v1/credits/admin/prices',
        headers={'X-Request-ID': 'r' * 129},
        json={
            'service_type': 'image',
            'resource_id': 'model-a',
            'action': 'text-to-image',
            'base_price': '1',
            'rules': {'schema_version': 1, 'dimensions': []},
        },
    )

    async def count_prices() -> int:
        async with router_database() as session:
            return await session.scalar(select(func.count()).select_from(CreditPrice))

    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'invalid_request_id'
    assert asyncio.run(count_prices()) == 0


def test_adjustment_audit_uses_api_key_source_and_hashes_the_peer_address() -> None:
    from open_webui.extensions.credits import router as credits_router
    from starlette.requests import Request

    scope = {
        'type': 'http',
        'method': 'POST',
        'path': '/',
        'headers': [(b'authorization', b'Bearer sk-secret-value')],
        'client': ('203.0.113.7', 41234),
    }

    audit = credits_router._audit_context(Request(scope))

    assert audit.source == 'api_key'
    assert len(audit.remote_address_hash) == 64
    assert audit.remote_address_hash != sha256(b'203.0.113.7').hexdigest()
    assert '203.0.113.7' not in audit.remote_address_hash


def test_adjustment_audit_distinguishes_web_and_bearer_api_sources() -> None:
    from open_webui.extensions.credits import router as credits_router
    from starlette.requests import Request

    bearer = Request(
        {
            'type': 'http',
            'method': 'POST',
            'path': '/',
            'headers': [(b'authorization', b'Bearer signed-web-token')],
        }
    )
    cookie = Request(
        {
            'type': 'http',
            'method': 'POST',
            'path': '/',
            'headers': [(b'cookie', b'token=signed-web-token')],
        }
    )

    assert credits_router._audit_context(bearer).source == 'api'
    assert credits_router._audit_context(cookie).source == 'web'


def test_adjustment_audit_accepts_custom_api_key_transport_state() -> None:
    from open_webui.extensions.credits import router as credits_router
    from starlette.requests import Request

    request = Request({'type': 'http', 'method': 'POST', 'path': '/', 'headers': []})
    request.state.token = type('Token', (), {'credentials': 'sk-custom-header-secret'})()

    audit = credits_router._audit_context(request)

    assert audit.source == 'api_key'


def test_accounts_use_the_compatibility_boundary(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    calls = []

    async def users(filters, skip, limit, *, session):
        calls.append((filters, skip, limit, session))
        return {'users': [], 'total': 0}

    app = _admin_app(credits_router, lambda: object())
    monkeypatch.setattr(credits_router, 'get_credit_users', users)

    response = TestClient(app).get('/api/v1/credits/admin/accounts?query=alice&skip=1&limit=2')

    assert response.status_code == 200
    assert calls[0][:3] == ({'query': 'alice'}, 1, 2)


def test_adjustment_audit_rejects_invalid_request_id_before_service(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    called = []

    async def adjust(*_args):
        called.append(True)

    monkeypatch.setattr(credits_router, 'adjust_balance', adjust)
    response = TestClient(_admin_app(credits_router, lambda: object()), raise_server_exceptions=False).post(
        '/api/v1/credits/admin/accounts/user-2/adjustments',
        headers={'X-Request-ID': 'r' * 129},
        json={'direction': 'increase', 'amount': 1, 'reason_code': 'promotion_gift'},
    )

    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'invalid_request_id'
    assert called == []


@pytest.mark.asyncio
async def test_me_balance_lookup_creates_the_lazy_account(router_database) -> None:
    from open_webui.extensions.credits import router as credits_router

    async def database_session():
        async with router_database() as session:
            yield session

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = database_session

    response = TestClient(app, raise_server_exceptions=False).get('/api/v1/credits/me')

    async with router_database() as session:
        account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == 'user-1'))
    assert response.status_code == 200
    assert response.json() == {'balance': 0}
    assert account is not None


@pytest.mark.asyncio
async def test_quote_reads_without_writing_credit_financial_records(router_database, monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    async with router_database() as session, session.begin():
        session.add(
            CreditPrice(
                id='price-1',
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

    async def prepare(_request, _image_input, _metadata, _user):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'text-to-image',
                        'dimensions': {},
                        'request_hash': 'read-only-quote',
                    },
                )()
            },
        )()

    credits_router._quote_cache.clear()
    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare)
    async with router_database() as session:
        result = await credits_router.quote_image(
            session,
            AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test'),
            {'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
        )
        counts = {
            model.__tablename__: await session.scalar(select(func.count()).select_from(model))
            for model in (CreditAccount, CreditLedger, CreditUsage)
        }

    assert result['charged_credits'] == 1
    assert counts == {'ext_credit_account': 0, 'ext_credit_ledger': 0, 'ext_credit_usage': 0}
