from __future__ import annotations

from dataclasses import asdict
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.schemas import RedeemCodeResult
from open_webui.utils import audit as audit_module
from open_webui.utils.audit import AuditLevel, AuditLogger, AuditLoggingMiddleware

from .router_test_support import AuthenticatedUser


class NeverLimited:
    def is_limited(self, _key: str) -> bool:
        return False


def _app(monkeypatch, *, user_role: str = 'user') -> tuple[FastAPI, object]:
    from open_webui.extensions.credits import router as credits_router
    from open_webui.extensions.credits import router_admin

    app = FastAPI()
    app.include_router(credits_router.router)
    user = AuthenticatedUser(
        id='admin-1' if user_role == 'admin' else 'user-1',
        name='Admin One' if user_role == 'admin' else 'User One',
        email='admin@example.test' if user_role == 'admin' else 'user@example.test',
        role=user_role,
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()
    app.dependency_overrides[credits_router.get_verified_user] = lambda: user
    app.dependency_overrides[router_admin.get_admin_user] = lambda: user
    monkeypatch.setattr(credits_router, '_redeem_limiter', NeverLimited())
    monkeypatch.setattr(router_admin, '_redeem_admin_limiter', NeverLimited())
    return app, credits_router


def test_redeem_requires_the_secret_header_before_calling_service(monkeypatch) -> None:
    app, credits_router = _app(monkeypatch)
    calls: list[object] = []

    async def redeem(*args):
        calls.append(args)
        return RedeemCodeResult(ledger_id='ledger-1', credited=10, balance=10, redeemed_at=1)

    monkeypatch.setattr(credits_router, 'redeem_code', redeem)
    response = TestClient(app).post('/api/v1/credits/redeem')

    assert response.status_code == 422
    assert calls == []


def test_redeem_uses_verified_identity_without_echoing_or_logging_the_code(monkeypatch) -> None:
    app, credits_router = _app(monkeypatch)
    raw_code = 'OWC-ABCDE-FGHJK-MNPQR-STUVW-XYZ234'
    captured: dict[str, object] = {}
    unexpected: list[dict[str, object]] = []

    async def redeem(_session, code, user, request_audit):
        captured.update(code=code, user=user, audit=request_audit)
        return RedeemCodeResult(ledger_id='ledger-1', credited=10, balance=17, redeemed_at=1)

    monkeypatch.setattr(credits_router, 'redeem_code', redeem)
    monkeypatch.setattr(credits_router.log, 'error', lambda _message, **kwargs: unexpected.append(kwargs))
    response = TestClient(app).post(
        '/api/v1/credits/redeem',
        headers={'X-Credit-Redeem-Code': raw_code, 'X-Request-ID': 'redeem-route-1'},
    )

    assert unexpected == []
    assert response.status_code == 200
    assert response.json() == {'ledger_id': 'ledger-1', 'credited': 10, 'balance': 17, 'redeemed_at': 1}
    assert raw_code not in response.text
    assert captured['code'] == raw_code
    assert captured['user'].id == 'user-1'
    assert captured['audit'].request_id == 'redeem-route-1'


def test_redeem_domain_errors_do_not_echo_secret_or_internal_context(monkeypatch) -> None:
    app, credits_router = _app(monkeypatch)
    raw_code = 'OWC-ABCDE-FGHJK-MNPQR-STUVW-XYZ234'

    async def reject(*_args):
        raise CreditError(code='redeem_code_used', context={'code_hash': 'must-not-leak'})

    monkeypatch.setattr(credits_router, 'redeem_code', reject)
    response = TestClient(app).post(
        '/api/v1/credits/redeem',
        headers={'X-Credit-Redeem-Code': raw_code},
    )

    assert response.status_code == 409
    assert response.json()['code'] == 'redeem_code_used'
    assert response.json()['context'] == {}
    assert raw_code not in response.text
    assert 'must-not-leak' not in response.text


@pytest.mark.parametrize(
    'path,method',
    [
        ('/api/v1/credits/admin/redeem-batches', 'get'),
        ('/api/v1/credits/admin/redeem-batches', 'post'),
        ('/api/v1/credits/admin/redeem-batches/batch-1/codes', 'get'),
        ('/api/v1/credits/admin/redeem-batches/batch-1/audit', 'get'),
        ('/api/v1/credits/admin/redeem-batches/batch-1/void', 'post'),
        ('/api/v1/credits/admin/redeem-batches/batch-1/codes/code-1/void', 'post'),
    ],
)
def test_all_redeem_admin_routes_require_admin(path: str, method: str, monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router
    from open_webui.extensions.credits import router_admin

    app = FastAPI()
    app.include_router(credits_router.router)

    def forbidden():
        raise HTTPException(status_code=403, detail='Admin access required')

    app.dependency_overrides[router_admin.get_admin_user] = forbidden
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()
    body = {'name': 'Batch', 'face_value': 10, 'quantity': 1} if path.endswith('redeem-batches') else None
    response = TestClient(app).request(method.upper(), path, json=body)

    assert response.status_code == 403


def test_invalid_request_id_remains_a_validation_error(monkeypatch) -> None:
    app, credits_router = _app(monkeypatch)
    calls: list[object] = []

    async def redeem(*args):
        calls.append(args)
        return RedeemCodeResult(ledger_id='ledger-1', credited=1, balance=1, redeemed_at=1)

    monkeypatch.setattr(credits_router, 'redeem_code', redeem)
    response = TestClient(app).post(
        '/api/v1/credits/redeem',
        headers={
            'X-Credit-Redeem-Code': 'OWC-ABCDE-FGHJK-MNPQR-STUVW-XYZ234',
            'X-Request-ID': 'x' * 129,
        },
    )

    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'invalid_request_id'
    assert calls == []


def test_batch_generation_redacts_one_time_codes_from_request_response_audit(
    monkeypatch,
) -> None:
    from open_webui.extensions.credits import router_admin

    app, credits_router = _app(monkeypatch, user_role='admin')
    one_time_code = 'OWC-ABCDE-FGHJK-MNPQR-STUVW-XYZ234'

    async def create_batch(_session, body, operator, request_audit):
        assert body.quantity == 1
        assert operator.id == 'admin-1'
        assert request_audit.request_id == 'generate-route-1'
        return SimpleNamespace(
            model_dump=lambda: {
                'id': 'batch-1',
                'name': 'Batch',
                'face_value': 10,
                'code_count': 1,
                'redeemed_count': 0,
                'voided_count': 0,
                'unused_count': 1,
                'available_count': 1,
                'expires_at': None,
                'per_user_limit': None,
                'voided_at': None,
                'created_by_id': 'admin-1',
                'created_by_name_snapshot': 'Admin One',
                'created_at': 1,
                'codes': [one_time_code],
            }
        )

    monkeypatch.setattr(router_admin, 'create_redeem_batch', create_batch)
    monkeypatch.setattr(audit_module, 'AUDIT_LOG_LEVEL', 'REQUEST_RESPONSE')
    entries = []

    def capture(_self, entry, *args, **kwargs):
        entries.append(entry)

    monkeypatch.setattr(AuditLogger, 'write', capture)
    app.add_middleware(AuditLoggingMiddleware, audit_level=AuditLevel.REQUEST_RESPONSE)

    response = TestClient(app).post(
        '/api/v1/credits/admin/redeem-batches',
        json={'name': 'Batch', 'face_value': 10, 'quantity': 1},
        headers={
            'Authorization': 'Bearer test-token',
            'X-Request-ID': 'generate-route-1',
        },
    )

    assert response.status_code == 201
    assert response.json()['codes'] == [one_time_code]
    assert response.headers['cache-control'] == 'no-store, max-age=0'
    assert len(entries) == 1
    logged = asdict(entries[0])
    assert logged['response_object'] == '[REDACTED]'
    assert one_time_code not in repr(logged)
    assert logged['request_object'] != '[REDACTED]'


def test_admin_code_list_exposes_plaintext_but_never_code_hash(monkeypatch) -> None:
    from open_webui.extensions.credits import router_admin

    app, credits_router = _app(monkeypatch, user_role='admin')

    async def list_codes(_session, _batch_id, *, skip, limit):
        assert (skip, limit) == (0, 50)
        return SimpleNamespace(
            model_dump=lambda: {
                'items': [
                    {
                        'id': 'code-1',
                        'code': 'OWC-AAAAA-BBBBB-CCCCC-DDDDD-XYZ234',
                        'hint': '…XYZ234',
                        'status': 'available',
                        'redeemed_by_user_id': None,
                        'redeemed_by_name_snapshot': None,
                        'redeemed_at': None,
                        'voided_at': None,
                    }
                ],
                'total': 1,
            }
        )

    monkeypatch.setattr(router_admin, 'list_redeem_codes', list_codes)
    response = TestClient(app).get('/api/v1/credits/admin/redeem-batches/batch-1/codes')

    assert response.status_code == 200
    assert response.json()['items'][0]['code'] == 'OWC-AAAAA-BBBBB-CCCCC-DDDDD-XYZ234'
    assert response.headers['cache-control'] == 'no-store, max-age=0'
    assert 'hash' not in response.text.lower()


def test_admin_code_list_response_redacted_from_request_response_audit(monkeypatch) -> None:
    from open_webui.extensions.credits import router_admin

    app, credits_router = _app(monkeypatch, user_role='admin')
    persisted_code = 'OWC-AAAAA-BBBBB-CCCCC-DDDDD-XYZ234'

    async def list_codes(_session, _batch_id, *, skip, limit):
        return SimpleNamespace(
            model_dump=lambda: {
                'items': [
                    {
                        'id': 'code-1',
                        'code': persisted_code,
                        'hint': '…XYZ234',
                        'status': 'available',
                        'redeemed_by_user_id': None,
                        'redeemed_by_name_snapshot': None,
                        'redeemed_at': None,
                        'voided_at': None,
                    }
                ],
                'total': 1,
            }
        )

    monkeypatch.setattr(router_admin, 'list_redeem_codes', list_codes)
    monkeypatch.setattr(audit_module, 'AUDIT_LOG_LEVEL', 'REQUEST_RESPONSE')
    entries = []

    def capture(_self, entry, *args, **kwargs):
        entries.append(entry)

    monkeypatch.setattr(AuditLogger, 'write', capture)
    app.add_middleware(
        AuditLoggingMiddleware,
        audit_level=AuditLevel.REQUEST_RESPONSE,
        audit_get_requests=True,
    )

    response = TestClient(app).get(
        '/api/v1/credits/admin/redeem-batches/batch-1/codes',
        headers={'Authorization': 'Bearer test-token'},
    )

    assert response.status_code == 200
    assert response.json()['items'][0]['code'] == persisted_code
    assert len(entries) == 1
    logged = asdict(entries[0])
    assert logged['response_object'] == '[REDACTED]'
    assert persisted_code not in repr(logged)
