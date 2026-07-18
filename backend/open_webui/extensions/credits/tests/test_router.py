from fastapi import FastAPI
from fastapi.testclient import TestClient

from .router_test_support import AuthenticatedUser


def test_me_returns_the_verified_users_balance(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def balance(_session, user):
        assert user.id == 'user-1'
        return 42

    monkeypatch.setattr(credits_router, 'get_balance', balance)

    response = TestClient(app).get('/api/v1/credits/me')

    assert response.status_code == 200
    assert response.json() == {'balance': 42}


def test_me_ledger_uses_the_authenticated_user_and_returns_page(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def ledger(_session, user_id, query):
        assert user_id == 'user-1'
        assert query.limit == 2
        return type('Page', (), {'model_dump': lambda self: {'items': [], 'next_cursor': None}})()

    monkeypatch.setattr(credits_router, 'list_user_ledger', ledger)

    response = TestClient(app).get('/api/v1/credits/me/ledger?limit=2')

    assert response.status_code == 200
    assert response.json() == {'items': [], 'next_cursor': None}


def test_user_ledger_returns_a_public_error_for_an_unexpected_failure(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def unavailable(_session, _user_id, _query):
        raise RuntimeError('sensitive database failure')

    monkeypatch.setattr(credits_router, 'list_user_ledger', unavailable)

    response = TestClient(app, raise_server_exceptions=False).get('/api/v1/credits/me/ledger')

    assert response.status_code == 503
    assert response.json()['code'] == 'credit_service_unavailable'


def test_credit_errors_use_the_public_envelope(monkeypatch) -> None:
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
    assert response.json()['code'] == 'credit_service_unavailable'


def test_unexpected_errors_are_logged_with_a_correlation_id_and_use_the_public_envelope(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()
    errors = []

    async def unavailable(_session, _user):
        raise RuntimeError('database connection details must not reach the client')

    monkeypatch.setattr(credits_router, 'get_balance', unavailable)
    monkeypatch.setattr(credits_router.log, 'error', lambda _message, **kwargs: errors.append(kwargs))

    response = TestClient(app, raise_server_exceptions=False).get('/api/v1/credits/me')

    assert response.status_code == 503
    assert response.json()['code'] == 'credit_service_unavailable'
    assert errors[0]['extra']['credit_correlation_id']
    assert errors[0]['extra']['credit_error_type'] == 'RuntimeError'


def test_admin_ledger_uses_admin_dependency(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def ledger(_session, query):
        assert query.limit == 3
        return type('Page', (), {'model_dump': lambda self: {'items': [], 'next_cursor': None}})()

    monkeypatch.setattr(credits_router, 'list_admin_ledger', ledger)

    response = TestClient(app).get('/api/v1/credits/admin/ledger?limit=3')

    assert response.status_code == 200
    assert response.json() == {'items': [], 'next_cursor': None}


def test_admin_ledger_returns_a_public_error_for_an_unexpected_failure(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def unavailable(_session, _query):
        raise RuntimeError('sensitive database failure')

    monkeypatch.setattr(credits_router, 'list_admin_ledger', unavailable)

    response = TestClient(app, raise_server_exceptions=False).get('/api/v1/credits/admin/ledger')

    assert response.status_code == 503
    assert response.json()['code'] == 'credit_service_unavailable'


def test_admin_adjustment_returns_a_public_error_for_an_unexpected_failure(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def unavailable(*_args):
        raise RuntimeError('sensitive database failure')

    monkeypatch.setattr(credits_router, 'adjust_balance', unavailable)

    response = TestClient(app, raise_server_exceptions=False).post(
        '/api/v1/credits/admin/accounts/user-2/adjustments',
        json={'direction': 'increase', 'amount': 1, 'reason_code': 'promotion_gift'},
    )

    assert response.status_code == 503
    assert response.json()['code'] == 'credit_service_unavailable'

    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def adjustment(_session, target, operator, request, audit):
        assert target.id == 'user-2'
        assert operator.id == 'admin-1'
        assert request.amount == 5
        assert audit.source == 'internal_admin'
        return type('Ledger', (), {'id': 'ledger-1', 'request_source': audit.source, 'request_id': audit.request_id})()

    monkeypatch.setattr(credits_router, 'adjust_balance', adjustment)

    response = TestClient(app).post(
        '/api/v1/credits/admin/accounts/user-2/adjustments',
        headers={'X-Request-ID': 'request-1'},
        json={
            'direction': 'increase',
            'amount': 5,
            'reason_code': 'promotion_gift',
        },
    )

    assert response.status_code == 200
    assert response.json() == {'ledger_id': 'ledger-1', 'source': 'internal_admin', 'request_id': 'request-1'}


def test_audit_context_generates_a_unique_request_id_without_a_header() -> None:
    from open_webui.extensions.credits import router as credits_router
    from starlette.requests import Request

    request_scope = {'type': 'http', 'method': 'POST', 'path': '/', 'headers': []}

    first = credits_router._audit_context(Request(request_scope))
    second = credits_router._audit_context(Request(request_scope))

    assert first.request_id != second.request_id
    assert len(first.request_id) == 36
    assert first.source == 'internal_admin'


def test_adjustment_rejects_a_client_supplied_audit_source(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    response = TestClient(app).post(
        '/api/v1/credits/admin/accounts/user-2/adjustments',
        json={'direction': 'increase', 'amount': 1, 'reason_code': 'promotion_gift', 'source': 'api_key'},
    )

    assert response.status_code == 422


def test_rate_limit_excess_returns_429(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    class Limited:
        def is_limited(self, _key):
            return True

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()
    monkeypatch.setattr(credits_router, '_quote_limiter', Limited())

    response = TestClient(app).post(
        '/api/v1/credits/quotes/image',
        json={'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
    )

    assert response.status_code == 429


def test_rate_limiter_uses_synchronous_redis_operations() -> None:
    from open_webui.utils.rate_limit import RateLimiter

    class SyncRedis:
        def __init__(self):
            self.calls = []
            self.values = {}

        def incr(self, key):
            self.calls.append(('incr', key))
            self.values[key] = self.values.get(key, 0) + 1
            return self.values[key]

        def expire(self, key, seconds):
            self.calls.append(('expire', key, seconds))

        def mget(self, keys):
            self.calls.append(('mget', tuple(keys)))
            return [self.values.get(key) for key in keys]

    redis = SyncRedis()
    limiter = RateLimiter(redis, limit=2, window=60)

    assert limiter.is_limited('credits:quote:user-1') is False
    assert limiter.is_limited('credits:quote:user-1') is False
    assert limiter.is_limited('credits:quote:user-1') is True
    assert [call[0] for call in redis.calls].count('incr') == 3
    assert [call[0] for call in redis.calls].count('mget') == 3


def test_disabled_credit_rate_limiter_does_not_count_requests() -> None:
    from open_webui.extensions.credits import router as credits_router

    limiter = credits_router.CreditRateLimiter(None, limit=1, window=60, enabled=False)
    limiter._memory_store.clear()

    assert limiter.is_limited('credits:quote:user-1') is False
    assert limiter.is_limited('credits:quote:user-1') is False


def test_credit_rate_limiter_records_a_metric_when_redis_falls_back(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    class FailingRedis:
        def incr(self, _key):
            raise RuntimeError('redis is unavailable')

    metrics = []
    monkeypatch.setattr(
        credits_router,
        '_rate_limit_fallback_counter',
        type('Counter', (), {'add': lambda _self, value, attributes: metrics.append((value, attributes))})(),
    )
    limiter = credits_router.CreditRateLimiter(FailingRedis(), limit=2, window=60)
    limiter._memory_store.clear()

    assert limiter.is_limited('credits:quote:user-1') is False
    assert metrics == [(1, {'credit.rate_limit.operation': 'quote'})]


def test_ledger_and_adjustment_share_operation_limiters(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    class Limiter:
        def __init__(self):
            self.keys = []

        def is_limited(self, key):
            self.keys.append(key)
            return False

    limiter = Limiter()
    monkeypatch.setattr(credits_router, '_ledger_limiter', limiter)
    monkeypatch.setattr(credits_router, '_adjustment_limiter', limiter)

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def user_ledger(_session, _user_id, _query):
        return type('Page', (), {'model_dump': lambda self: {'items': [], 'next_cursor': None}})()

    async def adjust(_session, _target, _operator, _request, audit):
        return type('Ledger', (), {'id': 'ledger-1', 'request_source': audit.source, 'request_id': audit.request_id})()

    monkeypatch.setattr(credits_router, 'list_user_ledger', user_ledger)
    monkeypatch.setattr(credits_router, 'adjust_balance', adjust)

    client = TestClient(app)
    assert client.get('/api/v1/credits/me/ledger').status_code == 200
    assert (
        client.post(
            '/api/v1/credits/admin/accounts/user-2/adjustments',
            json={'direction': 'increase', 'amount': 1, 'reason_code': 'promotion_gift'},
        ).status_code
        == 200
    )
    assert limiter.keys == ['credits:ledger:user-1', 'credits:adjustment:admin-1']
