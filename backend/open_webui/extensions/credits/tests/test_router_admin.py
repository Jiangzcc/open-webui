import asyncio
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from open_webui.extensions.credits.models import CreditPrice

from .router_test_support import AuthenticatedUser


def test_price_requests_reject_invalid_base_prices() -> None:
    from open_webui.extensions.credits.router import PriceRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PriceRequest.model_validate(
            {
                'service_type': 'image',
                'resource_id': 'model-a',
                'action': 'text-to-image',
                'base_price': 'not-a-decimal',
                'rules': {'schema_version': 1, 'dimensions': []},
            }
        )


def test_price_requests_reject_unknown_or_invalid_rules() -> None:
    from open_webui.extensions.credits.router import PriceRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PriceRequest.model_validate(
            {
                'service_type': 'image',
                'resource_id': 'model-a',
                'action': 'text-to-image',
                'base_price': '1',
                'rules': {'schema_version': 1, 'dimensions': [], 'unexpected': True},
            }
        )


def test_accounts_reject_invalid_pagination() -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    response = TestClient(app).get('/api/v1/credits/admin/accounts?skip=-1')

    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'invalid_pagination'
    assert TestClient(app).get('/api/v1/credits/admin/accounts?limit=101').status_code == 422


def test_accounts_return_a_public_error_for_an_unexpected_failure(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def unavailable(*_args, **_kwargs):
        raise RuntimeError('sensitive database failure')

    monkeypatch.setattr(credits_router, 'get_credit_users', unavailable)

    response = TestClient(app, raise_server_exceptions=False).get('/api/v1/credits/admin/accounts')

    assert response.status_code == 503
    assert response.json()['code'] == 'credit_service_unavailable'

    from open_webui.extensions.credits import router as credits_router

    class User:
        def __init__(self, user_id, name, email):
            self.id = user_id
            self.name = name
            self.email = email

    class Session:
        async def execute(self, _statement):
            return type('Result', (), {'all': lambda self: [('user-1', 8)]})()

    async def users(_filters, _skip, _limit, *, session):
        assert isinstance(session, Session)
        return {
            'users': [
                User('user-1', 'User One', 'user-1@example.test'),
                User('user-2', 'User Two', 'user-2@example.test'),
            ],
            'total': 2,
        }

    monkeypatch.setattr(credits_router, 'get_credit_users', users)
    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: Session()

    response = TestClient(app).get('/api/v1/credits/admin/accounts?query=user&skip=0&limit=2')

    assert response.status_code == 200
    assert response.json() == {
        'items': [
            {'user_id': 'user-1', 'name': 'User One', 'email': 'user-1@example.test', 'balance': 8},
            {'user_id': 'user-2', 'name': 'User Two', 'email': 'user-2@example.test', 'balance': 0},
        ],
        'total': 2,
    }


def test_price_create_persists_before_publishing_a_desensitized_event(router_database, monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    events = []

    async def database_session():
        async with router_database() as session:
            yield session

    async def publish(request, event, *, actor, subject_id, data):
        events.append((request, event, actor, subject_id, data))

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = database_session
    monkeypatch.setattr(credits_router, 'publish_credit_price_event', publish)

    response = TestClient(app, raise_server_exceptions=False).post(
        '/api/v1/credits/admin/prices',
        headers={'X-Request-ID': 'price-create-1'},
        json={
            'service_type': 'image',
            'resource_id': 'model-a',
            'action': 'text-to-image',
            'base_price': '3',
            'rules': {'schema_version': 1, 'dimensions': []},
        },
    )

    assert response.status_code == 200
    price_id = response.json()['id']
    assert events == [
        (
            events[0][0],
            'created',
            app.dependency_overrides[credits_router.get_admin_user](),
            price_id,
            {
                'price_id': price_id,
                'service_type': 'image',
                'resource_id': 'model-a',
                'action': 'text-to-image',
                'operator_id': 'admin-1',
                'request_id': 'price-create-1',
                'changed_fields': ['service_type', 'resource_id', 'action', 'base_price', 'rules', 'enabled'],
            },
        )
    ]

    async def persisted() -> CreditPrice | None:
        async with router_database() as session:
            return await session.get(CreditPrice, price_id)

    price = asyncio.run(persisted())
    assert price is not None
    assert price.base_price == '3'


def test_price_delete_persists_before_publishing_a_desensitized_event(router_database, monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    async def seed() -> None:
        async with router_database() as session, session.begin():
            session.add(
                CreditPrice(
                    id='price-delete-1',
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
    events = []

    async def database_session():
        async with router_database() as session:
            yield session

    async def publish(_request, event, *, actor, subject_id, data):
        events.append((event, actor, subject_id, data))

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = database_session
    monkeypatch.setattr(credits_router, 'publish_credit_price_event', publish)

    response = TestClient(app, raise_server_exceptions=False).delete(
        '/api/v1/credits/admin/prices/price-delete-1', headers={'X-Request-ID': 'price-delete-1'}
    )

    assert response.status_code == 200
    assert events[0][0] == 'deleted'
    assert events[0][2] == 'price-delete-1'
    assert events[0][3] == {
        'price_id': 'price-delete-1',
        'service_type': 'image',
        'resource_id': 'model-a',
        'action': 'text-to-image',
        'operator_id': 'admin-1',
        'request_id': 'price-delete-1',
        'changed_fields': [],
    }

    async def persisted() -> CreditPrice | None:
        async with router_database() as session:
            return await session.get(CreditPrice, 'price-delete-1')

    assert asyncio.run(persisted()) is None


def test_price_update_returns_not_found_when_the_price_does_not_exist(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    class Transaction:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    class Session:
        def begin(self):
            return Transaction()

        async def get(self, _model, _price_id):
            return None

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: Session()

    response = TestClient(app).put('/api/v1/credits/admin/prices/missing-price', json={'enabled': False})

    assert response.status_code == 404
    assert response.json()['detail']['code'] == 'price_not_found'


def test_price_delete_returns_not_found_when_the_price_does_not_exist() -> None:
    from open_webui.extensions.credits import router as credits_router

    class Transaction:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    class Session:
        def begin(self):
            return Transaction()

        async def get(self, _model, _price_id):
            return None

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: Session()

    response = TestClient(app).delete('/api/v1/credits/admin/prices/missing-price')

    assert response.status_code == 404
    assert response.json()['detail']['code'] == 'price_not_found'


def test_price_update_rejects_an_empty_change_set(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    response = TestClient(app).put('/api/v1/credits/admin/prices/price-1', json={})

    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'empty_price_update'


def test_price_update_commits_before_publishing_event(router_database, monkeypatch) -> None:
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
    events = []

    async def publish(*args, **kwargs):
        events.append((args, kwargs))

    async def database_session():
        async with router_database() as session:
            yield session

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = database_session
    monkeypatch.setattr(credits_router, 'publish_credit_price_event', publish)

    response = TestClient(app, raise_server_exceptions=False).put(
        '/api/v1/credits/admin/prices/price-1', json={'enabled': False}
    )

    assert response.status_code == 200
    assert response.json()['enabled'] is False
    assert len(events) == 1


@pytest.mark.asyncio
async def test_get_balance_if_exists_does_not_create_account(router_database) -> None:
    from open_webui.extensions.credits.repository import get_balance_if_exists

    async with router_database() as session:
        assert await get_balance_if_exists(session, 'absent-user') == 0
        await session.commit()
        assert (await session.get(CreditPrice, 'missing-price')) is None


def test_admin_price_errors_use_the_public_envelope_and_correlation_id(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    errors = []

    class Session:
        async def scalars(self, _statement):
            raise RuntimeError('database connection details must not reach the client')

    app.dependency_overrides[credits_router.get_async_session] = lambda: Session()
    monkeypatch.setattr(credits_router.log, 'error', lambda _message, **kwargs: errors.append(kwargs))

    response = TestClient(app, raise_server_exceptions=False).get('/api/v1/credits/admin/prices')

    assert response.status_code == 503
    assert response.json()['code'] == 'credit_service_unavailable'
    assert errors[0]['extra']['credit_correlation_id']


def test_price_events_use_the_compatibility_boundary(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    class Session:
        async def scalars(self, _statement):
            return type('Result', (), {'all': lambda self: []})()

    app.dependency_overrides[credits_router.get_async_session] = lambda: Session()
    calls = []

    async def publish(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(credits_router, 'publish_credit_price_event', publish)

    response = TestClient(app).get('/api/v1/credits/admin/prices')

    assert response.status_code == 200
    assert calls == []


def test_credit_dimensions_return_only_the_registered_image_dimensions() -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )

    response = TestClient(app).get('/api/v1/credits/admin/dimensions/image')

    assert response.status_code == 200
    assert response.json() == {
        'service_type': 'image',
        'dimensions': {
            'text-to-image': [
                {'key': 'size', 'rule_types': ['exact_map']},
                {'key': 'resolution', 'rule_types': ['exact_map']},
                {'key': 'aspect_ratio', 'rule_types': ['exact_map']},
                {'key': 'quality', 'rule_types': ['exact_map']},
                {'key': 'image_count', 'rule_types': ['quantity']},
                {'key': 'pixel_count', 'rule_types': ['proportional']},
            ],
            'image-to-image': [
                {'key': 'size', 'rule_types': ['exact_map']},
                {'key': 'resolution', 'rule_types': ['exact_map']},
                {'key': 'aspect_ratio', 'rule_types': ['exact_map']},
                {'key': 'quality', 'rule_types': ['exact_map']},
                {'key': 'image_count', 'rule_types': ['quantity']},
                {'key': 'pixel_count', 'rule_types': ['proportional']},
            ],
        },
    }


def test_credit_dimensions_include_video_generation_rules() -> None:
    from open_webui.extensions.credits import router as credits_router

    response = asyncio.run(credits_router.get_credit_dimensions('video', object()))

    assert set(response['dimensions']) == {
        'text-to-video',
        'image-to-video',
        'video-to-video',
    }
    assert response['dimensions']['text-to-video'][0] == {
        'key': 'duration',
        'rule_types': ['exact_map', 'numeric_tier', 'unit_blocks'],
    }


def test_unknown_credit_dimensions_return_not_found() -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )

    response = TestClient(app).get('/api/v1/credits/admin/dimensions/unknown-service')

    assert response.status_code == 404
    assert response.json()['detail']['code'] == 'service_type_not_found'


def test_main_imports_and_includes_the_credit_router_once() -> None:
    main_path = Path(__file__).parents[3] / 'main.py'
    source = main_path.read_text(encoding='utf-8')

    assert source.count('from open_webui.extensions.credits.router import router as credits_router') == 1
    assert source.count('app.include_router(credits_router)') == 1


def test_router_exposes_exactly_the_documented_credit_routes() -> None:
    from open_webui.extensions.credits import router as credits_router

    routes = {(route.path, next(iter(route.methods - {'HEAD'}))) for route in credits_router.router.routes}

    assert routes == {
        ('/api/v1/credits/me', 'GET'),
        ('/api/v1/credits/me/ledger', 'GET'),
        ('/api/v1/credits/quotes/image', 'POST'),
        # 新增的视频报价路由
        ('/api/v1/credits/quotes/video', 'POST'),
        ('/api/v1/credits/admin/accounts', 'GET'),
        ('/api/v1/credits/admin/accounts/{user_id}/adjustments', 'POST'),
        ('/api/v1/credits/admin/ledger', 'GET'),
        ('/api/v1/credits/admin/reconciliation', 'GET'),
        ('/api/v1/credits/admin/reconciliation/{usage_id}/compensate', 'POST'),
        ('/api/v1/credits/admin/prices', 'GET'),
        ('/api/v1/credits/admin/prices', 'POST'),
        ('/api/v1/credits/admin/prices/{price_id}', 'PUT'),
        ('/api/v1/credits/admin/prices/{price_id}', 'DELETE'),
        ('/api/v1/credits/admin/dimensions/{service_type}', 'GET'),
    }
