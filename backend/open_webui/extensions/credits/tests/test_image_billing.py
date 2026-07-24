from __future__ import annotations

import asyncio
import inspect
from contextlib import asynccontextmanager
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock

import pytest
from fastapi import HTTPException
from open_webui.extensions.credits.compat import BillingIdentity
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.image_billing import bill_image_call


@dataclass
class Request:
    headers: dict[str, object]


class FakeTxSession:
    """Stand-in for an async session that supports ``async with session.begin():``."""

    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def begin(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc is None:
            self.commits += 1
        else:
            self.rollbacks += 1
        return False


@asynccontextmanager
async def fake_credit_session():
    yield FakeTxSession()


def usage(
    status: str = 'debited',
    *,
    result_snapshot: object = None,
    error_snapshot: object = None,
):
    return SimpleNamespace(
        id='usage-1',
        status=status,
        result_snapshot=result_snapshot,
        error_snapshot=error_snapshot,
    )


@pytest.fixture
def billing_module(monkeypatch):
    import open_webui.extensions.credits.image_billing as module

    identity = BillingIdentity(user_id='user-1', name='User', email='user@example.test', role='user')
    prepared = SimpleNamespace(
        billing=SimpleNamespace(request_hash='a' * 64, channel='web'),
        provider_input=object(),
    )
    provider_form = object()
    monkeypatch.setattr(module.compat, 'map_billing_identity', lambda _raw: identity)
    monkeypatch.setattr(module, '_authorize_image_call', AsyncMock())
    monkeypatch.setattr(module, '_prepare_image_call', AsyncMock(return_value=prepared))
    monkeypatch.setattr(module, '_to_provider_form', lambda _prepared, _action: provider_form)
    monkeypatch.setattr(module, 'credit_session', fake_credit_session)
    monkeypatch.setattr(module, 'mark_usage_invoking', AsyncMock(return_value=1))
    monkeypatch.setattr(module, 'mark_usage_succeeded', AsyncMock(return_value=1))
    monkeypatch.setattr(module, 'mark_usage_succeeded_in_session', AsyncMock(return_value=1))
    monkeypatch.setattr(module, 'mark_usage_failed', AsyncMock(return_value=1))
    return module, identity, prepared, provider_form


async def call_bill(
    *,
    invoke,
    finalize=None,
    request=None,
    raw_form_data=object(),
    metadata=None,
    raw_user=object(),
    action='text-to-image',
    authorization_scope='direct',
):
    return await bill_image_call(
        request=request or Request(headers={}),
        raw_form_data=raw_form_data,
        metadata=metadata,
        raw_user=raw_user,
        action=action,
        authorization_scope=authorization_scope,
        invoke=invoke,
        finalize=finalize or AsyncMock(),
    )


@pytest.mark.asyncio
async def test_terminal_finalize_and_success_share_one_transaction(billing_module, monkeypatch) -> None:
    module, identity, prepared, provider_form = billing_module
    begin = AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='new'))
    monkeypatch.setattr(module, 'begin_image_usage', begin)
    internal_result = SimpleNamespace(images=(SimpleNamespace(url='/api/v1/files/result-1/content'),))
    invoke = AsyncMock(return_value=internal_result)
    finalize = AsyncMock()

    result = await call_bill(
        invoke=invoke,
        finalize=finalize,
        request=Request(headers={'Idempotency-Key': 'request-key'}),
    )

    assert result == [{'url': '/api/v1/files/result-1/content'}]
    assert begin.await_args.args[2] is prepared.billing
    assert begin.await_args.args[3] == 'request-key'
    module.mark_usage_invoking.assert_awaited_once_with('usage-1')
    invoke.assert_awaited_once_with(prepared, provider_form)
    finalize.assert_awaited_once_with(ANY, prepared, internal_result, 'usage-1')
    module.mark_usage_succeeded_in_session.assert_awaited_once_with(ANY, 'usage-1', ['/api/v1/files/result-1/content'])
    module.mark_usage_succeeded.assert_not_awaited()
    module._authorize_image_call.assert_awaited_once_with(identity, 'text-to-image', 'direct')


@pytest.mark.asyncio
async def test_direct_scope_skips_feature_switch_and_permission(monkeypatch) -> None:
    import open_webui.extensions.credits.image_billing as module

    current_user = SimpleNamespace(id='user-1', name='User', email='user@example.test', role='user')
    identity = BillingIdentity(user_id='user-1', name='User', email='user@example.test', role='user')
    session = AuthorizationSession(current_user)
    monkeypatch.setattr(module, 'credit_session', lambda: authorization_session(session))
    config = AsyncMock()
    monkeypatch.setattr(module.compat, 'get_runtime_image_config', config)
    permission = AsyncMock()
    monkeypatch.setattr(module, 'has_permission', permission)

    snapshot = await module._authorize_image_call(identity, 'text-to-image', 'direct')

    assert snapshot.id == 'user-1'
    config.assert_not_awaited()
    permission.assert_not_awaited()


@pytest.mark.asyncio
async def test_terminal_preparation_failure_leaves_usage_invoking(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='new')),
    )
    module.mark_usage_failed.reset_mock()
    invoke = AsyncMock(side_effect=module.ImageTerminalPreparationError())

    with pytest.raises(CreditError) as raised:
        await call_bill(invoke=invoke)

    assert raised.value.code == 'credit_service_unavailable'
    assert raised.value.context['reason'] == 'terminal_preparation_failed'
    module.mark_usage_failed.assert_not_awaited()


@pytest.mark.asyncio
async def test_finalize_failure_leaves_usage_invoking_and_never_marks_provider_failed(
    billing_module, monkeypatch
) -> None:
    module, _, _, _ = billing_module
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='new')),
    )
    module.mark_usage_failed.reset_mock()
    invoke = AsyncMock(return_value=[{'url': '/api/v1/files/result-1/content'}])
    finalize = AsyncMock(side_effect=RuntimeError('db died'))

    with pytest.raises(CreditError) as raised:
        await call_bill(invoke=invoke, finalize=finalize)

    assert raised.value.code == 'credit_service_unavailable'
    module.mark_usage_failed.assert_not_awaited()
    module.mark_usage_succeeded_in_session.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('scope', 'channel'),
    [('direct', 'web'), ('direct', 'api'), ('chat', 'chat'), ('tool', 'tool')],
)
async def test_scope_channel_matrix_accepts_only_trusted_pairs(scope, channel) -> None:
    from open_webui.extensions.credits.image_billing import validate_authorization_scope

    assert validate_authorization_scope(scope, channel) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('scope', 'channel'),
    [('direct', 'chat'), ('chat', 'web'), ('tool', 'chat'), ('chat', 'tool'), ('weird', 'web')],
)
async def test_scope_channel_matrix_rejects_untrusted_pairs(scope, channel) -> None:
    from open_webui.extensions.credits.image_billing import validate_authorization_scope

    with pytest.raises(CreditError) as raised:
        validate_authorization_scope(scope, channel)
    assert raised.value.code == 'credit_service_unavailable'


def test_bill_image_call_requires_authorization_scope_and_finalize() -> None:
    import inspect

    from open_webui.extensions.credits.image_billing import bill_image_call

    signature = inspect.signature(bill_image_call)
    assert signature.parameters['authorization_scope'].default is inspect.Parameter.empty
    assert signature.parameters['finalize'].default is inspect.Parameter.empty
    invoke_param = signature.parameters['invoke']
    assert invoke_param.default is inspect.Parameter.empty


@pytest.mark.asyncio
async def test_local_file_urls_are_normalized_before_persisting_success(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='new')),
    )
    invoke = AsyncMock(
        return_value=[
            {'url': 'http://localhost:8080/api/v1/files/result-1/content'},
            {'url': '/api/v1/files/result-2/content'},
        ]
    )

    result = await call_bill(invoke=invoke)

    assert result == [
        {'url': '/api/v1/files/result-1/content'},
        {'url': '/api/v1/files/result-2/content'},
    ]
    module.mark_usage_succeeded_in_session.assert_awaited_once_with(
        ANY,
        'usage-1',
        ['/api/v1/files/result-1/content', '/api/v1/files/result-2/content'],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('outcome', 'stored', 'expected_code'),
    [
        ('processing', {}, 'usage_processing'),
        ('failed', {'error_snapshot': {'code': 'http_429', 'summary': 'hidden'}}, 'provider_failed'),
        ('unknown', {}, 'credit_service_unavailable'),
    ],
)
async def test_non_success_replays_never_invoke_provider(
    billing_module, monkeypatch, outcome, stored, expected_code
) -> None:
    module, _, _, _ = billing_module
    existing = usage(outcome, **stored)
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(return_value=SimpleNamespace(usage=existing, outcome=outcome)),
    )
    invoke = AsyncMock()

    with pytest.raises(CreditError) as raised:
        await call_bill(
            invoke=invoke,
            request=Request(headers={'idempotency-key': 'request-key'}),
        )

    assert raised.value.code == expected_code
    assert 'summary' not in raised.value.context
    invoke.assert_not_awaited()
    module.mark_usage_invoking.assert_not_awaited()


@pytest.mark.asyncio
async def test_succeeded_replay_returns_stored_internal_urls_without_provider(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    existing = usage('succeeded', result_snapshot={'urls': ['/api/v1/files/result-1/content']})
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(return_value=SimpleNamespace(usage=existing, outcome='succeeded')),
    )
    invoke = AsyncMock()

    result = await call_bill(
        invoke=invoke,
        request=Request(headers={'idempotency-key': 'request-key'}),
    )

    assert result == [{'url': '/api/v1/files/result-1/content'}]
    invoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_provider_failure_is_persisted_without_exception_text(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='new')),
    )
    invoke = AsyncMock(side_effect=RuntimeError('secret-provider-token'))

    with pytest.raises(CreditError) as raised:
        await call_bill(invoke=invoke, action='image-to-image')

    assert raised.value.code == 'provider_failed'
    assert 'secret-provider-token' not in str(raised.value.context)
    safe_error = module.mark_usage_failed.await_args.args[1]
    assert safe_error.code == 'provider_failed'
    assert safe_error.summary == 'Image provider request failed'
    assert 'secret-provider-token' not in safe_error.summary


@pytest.mark.asyncio
async def test_cancelled_provider_call_propagates_without_failed_transition(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='new')),
    )
    invoke = AsyncMock(side_effect=asyncio.CancelledError())

    with pytest.raises(asyncio.CancelledError):
        await call_bill(invoke=invoke)

    module.mark_usage_failed.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(('transition', 'side_effect'), [(0, None), (None, RuntimeError('db secret'))])
async def test_invoking_transition_failure_blocks_provider(
    billing_module, monkeypatch, transition, side_effect
) -> None:
    module, _, _, _ = billing_module
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='new')),
    )
    module.mark_usage_invoking.return_value = transition
    module.mark_usage_invoking.side_effect = side_effect
    invoke = AsyncMock()

    with pytest.raises(CreditError) as raised:
        await call_bill(invoke=invoke)

    assert raised.value.code == 'credit_service_unavailable'
    invoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_metadata_derives_stable_hashed_key_without_storing_raw_context(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    begin = AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='processing'))
    monkeypatch.setattr(module, 'begin_image_usage', begin)
    metadata = {
        'credit_channel': 'tool',
        'chat_id': 'chat-secret',
        'message_id': 'message-secret',
        'call_instance_id': 'tool-call-secret',
    }

    for _ in range(2):
        with pytest.raises(CreditError):
            await call_bill(invoke=AsyncMock(), metadata=metadata)

    keys = [call.args[3] for call in begin.await_args_list]
    assert keys[0] == keys[1]
    assert keys[0].startswith('image:')
    assert len(keys[0]) == 70
    assert all(secret not in keys[0] for secret in ('chat-secret', 'message-secret', 'tool-call-secret'))


@pytest.mark.asyncio
async def test_authorization_failure_happens_before_usage_and_provider(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    module._authorize_image_call.side_effect = CreditError(
        code='credit_service_unavailable', context={'reason': 'unauthorized'}
    )
    begin = AsyncMock()
    monkeypatch.setattr(module, 'begin_image_usage', begin)
    invoke = AsyncMock()

    with pytest.raises(CreditError):
        await call_bill(invoke=invoke)

    begin.assert_not_awaited()
    invoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_header_key_takes_precedence_over_stable_metadata(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    begin = AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='processing'))
    monkeypatch.setattr(module, 'begin_image_usage', begin)

    with pytest.raises(CreditError):
        await call_bill(
            invoke=AsyncMock(),
            request=Request(headers={'IDEMPOTENCY-KEY': 'header-key'}),
            metadata={
                'credit_channel': 'chat',
                'chat_id': 'chat-1',
                'message_id': 'message-1',
                'call_instance_id': 'call-1',
            },
        )

    assert begin.await_args.args[3] == 'header-key'


@pytest.mark.asyncio
async def test_malformed_success_snapshot_fails_closed_without_provider(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(
            return_value=SimpleNamespace(
                usage=usage('succeeded', result_snapshot={'urls': ['https://provider.example/result']}),
                outcome='succeeded',
            )
        ),
    )
    invoke = AsyncMock()

    with pytest.raises(CreditError) as raised:
        await call_bill(invoke=invoke)

    assert raised.value.code == 'credit_service_unavailable'
    invoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_success_status_failure_does_not_reinvoke_provider(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='new')),
    )
    module.mark_usage_succeeded_in_session.return_value = 0
    invoke = AsyncMock(return_value=[{'url': '/api/v1/files/result-1/content'}])

    with pytest.raises(CreditError) as raised:
        await call_bill(invoke=invoke)

    assert raised.value.code == 'credit_service_unavailable'
    invoke.assert_awaited_once()


class AuthorizationRow:
    def __init__(self, current_user):
        self.current_user = current_user

    def one_or_none(self):
        return self.current_user


class AuthorizationSession:
    def __init__(self, current_user):
        self.current_user = current_user

    async def execute(self, _statement):
        return AuthorizationRow(self.current_user)


@asynccontextmanager
async def authorization_session(session):
    yield session


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('current_user', 'identity_role'),
    [
        (None, 'user'),
        (SimpleNamespace(id='user-1', name='User', email='user@example.test', role='pending'), 'user'),
        (SimpleNamespace(id='user-1', name='User', email='user@example.test', role='user'), 'admin'),
    ],
)
async def test_authorization_rejects_missing_pending_and_spoofed_roles(
    monkeypatch, current_user, identity_role
) -> None:
    import open_webui.extensions.credits.image_billing as module

    identity = BillingIdentity(user_id='user-1', name='User', email='user@example.test', role=identity_role)
    session = AuthorizationSession(current_user)
    monkeypatch.setattr(module, 'credit_session', lambda: authorization_session(session))

    with pytest.raises(HTTPException) as raised:
        await module._authorize_image_call(identity, 'text-to-image')

    assert raised.value.status_code == 403


@pytest.mark.asyncio
async def test_authorization_checks_enable_and_permission_with_same_session(monkeypatch) -> None:
    import open_webui.extensions.credits.image_billing as module

    current_user = SimpleNamespace(id='user-1', name='User', email='user@example.test', role='user')
    identity = BillingIdentity(user_id='user-1', name='User', email='user@example.test', role='user')
    session = AuthorizationSession(current_user)
    monkeypatch.setattr(module, 'credit_session', lambda: authorization_session(session))
    monkeypatch.setattr(
        module.compat,
        'get_runtime_image_config',
        AsyncMock(
            return_value=SimpleNamespace(
                ENABLE_IMAGE_GENERATION=True,
                ENABLE_IMAGE_EDIT=True,
                USER_PERMISSIONS={'features': {'image_generation': True}},
            )
        ),
    )
    permission = AsyncMock(return_value=True)
    monkeypatch.setattr(module, 'has_permission', permission)

    snapshot = await module._authorize_image_call(identity, 'image-to-image')

    assert snapshot.id == current_user.id
    assert permission.await_args.kwargs['db'] is session


@pytest.mark.asyncio
async def test_authorization_denies_disabled_feature_before_permission(monkeypatch) -> None:
    import open_webui.extensions.credits.image_billing as module

    current_user = SimpleNamespace(id='user-1', name='User', email='user@example.test', role='user')
    identity = BillingIdentity(user_id='user-1', name='User', email='user@example.test', role='user')
    session = AuthorizationSession(current_user)
    monkeypatch.setattr(module, 'credit_session', lambda: authorization_session(session))
    monkeypatch.setattr(
        module.compat,
        'get_runtime_image_config',
        AsyncMock(return_value=SimpleNamespace(ENABLE_IMAGE_GENERATION=False, USER_PERMISSIONS={})),
    )
    permission = AsyncMock()
    monkeypatch.setattr(module, 'has_permission', permission)

    with pytest.raises(HTTPException) as raised:
        await module._authorize_image_call(identity, 'text-to-image')

    assert raised.value.status_code == 403
    permission.assert_not_awaited()


@pytest.mark.asyncio
async def test_authorization_database_failure_is_sanitized(monkeypatch) -> None:
    import open_webui.extensions.credits.image_billing as module

    identity = BillingIdentity(user_id='user-1', name='User', email='user@example.test', role='user')
    session = AuthorizationSession(None)
    session.execute = AsyncMock(side_effect=RuntimeError('database-secret-token'))
    monkeypatch.setattr(module, 'credit_session', lambda: authorization_session(session))

    with pytest.raises(CreditError) as raised:
        await module._authorize_image_call(identity, 'text-to-image')

    assert raised.value.code == 'credit_service_unavailable'
    assert 'database-secret-token' not in str(raised.value.context)


@pytest.mark.asyncio
async def test_provider_failure_status_write_failure_is_service_unavailable(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='new')),
    )
    module.mark_usage_failed.return_value = 0

    with pytest.raises(CreditError) as raised:
        await call_bill(invoke=AsyncMock(side_effect=RuntimeError('provider-secret')))

    assert raised.value.code == 'credit_service_unavailable'
    assert 'provider-secret' not in str(raised.value.context)


@pytest.mark.asyncio
async def test_precharge_database_failure_blocks_provider_and_is_sanitized(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    monkeypatch.setattr(
        module,
        'begin_image_usage',
        AsyncMock(side_effect=RuntimeError('database-secret-token')),
    )
    invoke = AsyncMock()

    with pytest.raises(CreditError) as raised:
        await call_bill(invoke=invoke)

    assert raised.value.code == 'credit_service_unavailable'
    assert 'database-secret-token' not in str(raised.value.context)
    invoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_lazy_service_proxies_preserve_import_direction(monkeypatch) -> None:
    import open_webui.extensions.credits.db as credit_db
    import open_webui.extensions.credits.image_billing as module
    import open_webui.extensions.credits.service as service

    marker = object()
    begin = AsyncMock(return_value=marker)
    invoking = AsyncMock(return_value=1)
    succeeded = AsyncMock(return_value=1)
    failed = AsyncMock(return_value=1)
    monkeypatch.setattr(service, 'begin_image_usage', begin)
    monkeypatch.setattr(service, 'mark_usage_invoking', invoking)
    monkeypatch.setattr(service, 'mark_usage_succeeded', succeeded)
    monkeypatch.setattr(service, 'mark_usage_failed', failed)
    monkeypatch.setattr(credit_db, 'credit_session', fake_credit_session)
    user = SimpleNamespace(id='user-1')
    context = object()
    safe_error = object()

    async with module.credit_session() as session:
        assert session is not None
    assert await module.begin_image_usage(object(), user, context, 'request-key') is marker
    assert await module.mark_usage_invoking('usage-1') == 1
    assert await module.mark_usage_succeeded('usage-1', ['/api/v1/files/result/content']) == 1
    assert await module.mark_usage_failed('usage-1', safe_error) == 1

    begin.assert_awaited_once()
    invoking.assert_awaited_once_with('usage-1')
    succeeded.assert_awaited_once()
    failed.assert_awaited_once_with('usage-1', safe_error)


@pytest.mark.asyncio
async def test_request_without_stable_context_gets_fresh_request_scoped_key(billing_module, monkeypatch) -> None:
    module, _, _, _ = billing_module
    begin = AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='processing'))
    monkeypatch.setattr(module, 'begin_image_usage', begin)

    for _ in range(2):
        with pytest.raises(CreditError):
            await call_bill(invoke=AsyncMock())

    first, second = (call.args[3] for call in begin.await_args_list)
    assert first != second
    assert len(first) == len(second) == 36


@pytest.mark.skip(
    reason='imports routers.images, whose upstream Alembic migration hangs on this machine; '
    'credit-envelope behaviour is covered by the unit tests above and Task 11 browser acceptance'
)
def test_public_image_http_route_returns_the_credit_error_envelope(monkeypatch) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from open_webui.routers import images

    async def enabled_config():
        return type('Config', (), {'ENABLE_IMAGE_GENERATION': True, 'USER_PERMISSIONS': {}})()

    async def fail_credit(*_args, **_kwargs):
        raise CreditError(code='insufficient_credits', context={'required': 3})

    app = FastAPI()
    app.include_router(images.router)
    app.dependency_overrides[images.get_verified_user] = lambda: type(
        'User',
        (),
        {'id': 'user-1', 'role': 'admin'},
    )()
    monkeypatch.setattr(images, 'get_image_config', enabled_config)
    monkeypatch.setattr(images, 'image_generations', fail_credit)

    response = TestClient(app, raise_server_exceptions=False).post('/generations', json={'prompt': 'safe prompt'})

    assert response.status_code == 402
    assert response.json() == {
        'code': 'insufficient_credits',
        'message': 'Insufficient credits',
        'context': {'required': 3},
    }


@pytest.mark.skip(
    reason='imports routers.images, whose upstream Alembic migration hangs on this machine; '
    'credit-envelope behaviour is covered by the unit tests above and Task 11 browser acceptance'
)
def test_public_image_edit_http_route_returns_the_credit_error_envelope(monkeypatch) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from open_webui.routers import images

    async def enabled_config():
        return type('Config', (), {'ENABLE_IMAGE_EDIT': True, 'USER_PERMISSIONS': {}})()

    async def fail_credit(*_args, **_kwargs):
        raise CreditError(code='price_not_configured')

    app = FastAPI()
    app.include_router(images.router)
    app.dependency_overrides[images.get_verified_user] = lambda: type(
        'User',
        (),
        {'id': 'user-1', 'role': 'admin'},
    )()
    monkeypatch.setattr(images, 'get_image_config', enabled_config)
    monkeypatch.setattr(images, 'image_edits', fail_credit)

    response = TestClient(app, raise_server_exceptions=False).post(
        '/edit',
        json={'image': 'data:image/png;base64,AA==', 'prompt': 'safe prompt'},
    )

    assert response.status_code == 409
    assert response.json() == {
        'code': 'price_not_configured',
        'message': 'Price is not configured',
        'context': {},
    }


@pytest.mark.skip(
    reason='imports routers.images, whose upstream Alembic migration hangs on this machine; '
    'signature contracts are covered by creations/tests/test_image_entrypoints.py AST tests'
)
def test_images_module_imports_without_cycle_and_preserves_public_signatures() -> None:
    import open_webui.routers.images as images

    generation = inspect.signature(images.image_generations)
    edit = inspect.signature(images.image_edits)

    assert list(generation.parameters) == ['request', 'form_data', 'authorization_scope', 'metadata', 'user']
    assert generation.parameters['authorization_scope'].default is inspect.Parameter.empty
    assert generation.parameters['metadata'].default is None
    assert generation.parameters['user'].default is None
    assert list(edit.parameters) == ['request', 'form_data', 'authorization_scope', 'metadata', 'user']
    assert edit.parameters['authorization_scope'].default is inspect.Parameter.empty
    assert edit.parameters['metadata'].default is None
    assert repr(edit.parameters['user'].default).startswith('Depends(')
    assert callable(images._invoke_image_generations)
    assert callable(images._invoke_image_edits)


@pytest.mark.skip(
    reason='imports routers.images, whose upstream Alembic migration hangs on this machine; '
    'delegation contracts are covered by creations/tests/test_image_entrypoints.py AST tests'
)
@pytest.mark.asyncio
async def test_public_image_wrappers_delegate_new_provider_dto_through_billing(monkeypatch) -> None:
    import open_webui.routers.images as images
    from open_webui.extensions.creations.schemas import CapturedImageBatch, CapturedImageResult

    provider_generation = object()
    provider_edit = object()
    generation_form = object()
    edit_form = object()
    user = object()
    metadata = {'chat_id': 'chat-1'}

    def _batch(url):
        return CapturedImageBatch(
            images=(
                CapturedImageResult(
                    url=url,
                    file_id='fid',
                    file_user_id='uid',
                    file_created_at=1,
                    mime_type='image/png',
                ),
            )
        )

    inner_generation = AsyncMock(return_value=_batch('/api/v1/files/generation/content'))
    inner_edit = AsyncMock(return_value=_batch('/api/v1/files/edit/content'))
    monkeypatch.setattr(images, '_invoke_image_generations', inner_generation)
    monkeypatch.setattr(images, '_invoke_image_edits', inner_edit)

    captured = {}

    async def fake_bill_image_call(**kwargs):
        provider_form = provider_generation if kwargs['action'] == 'text-to-image' else provider_edit
        captured[kwargs['action']] = {
            'scope': kwargs['authorization_scope'],
            'finalize': kwargs['finalize'],
        }
        batch = await kwargs['invoke'](object(), provider_form)
        return [{'url': item.url} for item in batch.images]

    monkeypatch.setattr(images, 'bill_image_call', fake_bill_image_call)

    generation_result = await images.image_generations(Request(headers={}), generation_form, 'direct', metadata, user)
    edit_result = await images.image_edits(Request(headers={}), edit_form, 'direct', metadata, user)

    assert generation_result == [{'url': '/api/v1/files/generation/content'}]
    assert edit_result == [{'url': '/api/v1/files/edit/content'}]
    assert captured['text-to-image']['scope'] == 'direct'
    assert captured['image-to-image']['scope'] == 'direct'
    assert callable(captured['text-to-image']['finalize'])
    assert callable(captured['image-to-image']['finalize'])
    inner_generation.assert_awaited_once_with(ANY, provider_generation, metadata, user)
    inner_edit.assert_awaited_once_with(ANY, provider_edit, metadata, user)
