from fastapi import FastAPI
from fastapi.testclient import TestClient

from .router_test_support import AuthenticatedUser


def _admin_app(credits_router, session):
    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_admin_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: session
    return app


def test_adjustment_rejects_oversized_target_id_before_database_access() -> None:
    from open_webui.extensions.credits import router as credits_router

    response = TestClient(_admin_app(credits_router, object()), raise_server_exceptions=False).post(
        f'/api/v1/credits/admin/accounts/{"u" * 129}/adjustments',
        json={'direction': 'increase', 'amount': 1, 'reason_code': 'promotion_gift'},
    )

    assert response.status_code == 422


def test_price_paths_reject_oversized_price_id_before_database_access() -> None:
    from open_webui.extensions.credits import router as credits_router

    client = TestClient(_admin_app(credits_router, object()), raise_server_exceptions=False)

    assert client.put(f'/api/v1/credits/admin/prices/{"p" * 129}', json={'enabled': False}).status_code == 422
    assert client.delete(f'/api/v1/credits/admin/prices/{"p" * 129}').status_code == 422


def test_dimension_path_rejects_oversized_service_type() -> None:
    from open_webui.extensions.credits import router as credits_router

    response = TestClient(_admin_app(credits_router, object())).get(f'/api/v1/credits/admin/dimensions/{"s" * 65}')

    assert response.status_code == 422


def test_user_ledger_accepts_the_documented_category_filter(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def ledger(_session, _user_id, query):
        assert query.category == 'income'
        return type('Page', (), {'model_dump': lambda self: {'items': [], 'next_cursor': None}})()

    monkeypatch.setattr(credits_router, 'list_user_ledger', ledger)

    response = TestClient(app).get('/api/v1/credits/me/ledger?category=income')

    assert response.status_code == 200


def test_price_listing_applies_bounded_pagination() -> None:
    from open_webui.extensions.credits import router as credits_router

    class Session:
        async def scalars(self, statement):
            assert statement._limit_clause.value == 100
            assert statement._offset_clause.value == 2
            return type('Result', (), {'all': lambda self: []})()

    client = TestClient(_admin_app(credits_router, Session()))

    assert client.get('/api/v1/credits/admin/prices?skip=2&limit=100').status_code == 200
    assert client.get('/api/v1/credits/admin/prices?limit=101').status_code == 422
