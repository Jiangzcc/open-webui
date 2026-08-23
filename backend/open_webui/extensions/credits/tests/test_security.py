from __future__ import annotations

import ast
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.credits.compat import BillingIdentity
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.schemas import UserLedgerQuery

ROOT = Path(__file__).parents[5]


@dataclass
class Request:
    headers: dict[str, object]


@asynccontextmanager
async def _fake_credit_session():
    yield object()


def _router_source() -> ast.Module:
    return ast.parse((ROOT / 'backend/open_webui/extensions/credits/router.py').read_text(encoding='utf-8'))


def _router_support_source() -> ast.Module:
    # 拆分后错误信封与限流降级助手位于 router_support.py（复盘：超长文件拆分）。
    return ast.parse(
        (ROOT / 'backend/open_webui/extensions/credits/router_support.py').read_text(encoding='utf-8')
    )


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f'missing function {name}')


def _route_function(tree: ast.Module, name: str) -> ast.AsyncFunctionDef:
    function = _function(tree, name)
    assert isinstance(function, ast.AsyncFunctionDef)
    return function


def _decorator_path(function: ast.AsyncFunctionDef) -> str:
    for decorator in function.decorator_list:
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            if decorator.func.attr in {'get', 'post', 'put', 'delete'} and decorator.args:
                value = decorator.args[0]
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    return value.value
    raise AssertionError(f'missing route decorator for {function.name}')


def _dependency_names(function: ast.AsyncFunctionDef) -> set[str]:
    names = set()
    for argument in (*function.args.args, *function.args.kwonlyargs):
        default = next(
            (
                item
                for item in (*function.args.defaults, *function.args.kw_defaults)
                if isinstance(item, ast.Call)
                and isinstance(item.func, ast.Name)
                and item.func.id == 'Depends'
                and item.args
                and item.args[0] is argument
            ),
            None,
        )
        if default is not None and isinstance(default.args[0], ast.Name):
            names.add(default.args[0].id)
    for call in (node for node in ast.walk(function) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
        if call.func.id == 'Depends' and call.args and isinstance(call.args[0], ast.Name):
            names.add(call.args[0].id)
    return names


def test_credit_routes_keep_user_and_admin_authorization_boundaries() -> None:
    tree = _router_source()
    user_routes = {'/quotes/image', '/me', '/me/ledger'}
    admin_prefix = '/admin/'

    for function in (node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)):
        try:
            path = _decorator_path(function)
        except AssertionError:
            continue
        dependencies = _dependency_names(function)
        if path in user_routes:
            assert 'get_verified_user' in dependencies
            assert 'get_admin_user' not in dependencies
        if path.startswith(admin_prefix):
            assert 'get_admin_user' in dependencies
            assert 'get_verified_user' not in dependencies


def test_user_ledger_clamps_dates_and_schema_rejects_unbounded_page_size(monkeypatch) -> None:
    from open_webui.extensions.credits import service

    captured = {}

    async def list_ledger(_session, query, *, user_id=None):
        captured['query'] = query
        captured['user_id'] = user_id
        return [], None

    monkeypatch.setattr(service, '_now', lambda: 3 * 365 * 24 * 60 * 60)
    monkeypatch.setattr(service, 'list_ledger', list_ledger)
    page = asyncio.run(service.list_user_ledger(object(), 'user-1', UserLedgerQuery(since=1, limit=100)))

    assert page.items == ()
    assert captured['user_id'] == 'user-1'
    assert captured['query'].since == 2 * 365 * 24 * 60 * 60
    assert captured['query'].limit == 100
    with pytest.raises(ValueError):
        UserLedgerQuery(limit=101)


def test_idempotency_header_reaches_the_service_validation_and_blocks_provider(monkeypatch) -> None:
    from open_webui.extensions.credits import image_billing, service

    identity = BillingIdentity(user_id='user-1', name='User', email='user@example.test', role='user')
    prepared = SimpleNamespace(
        billing=SimpleNamespace(request_hash='a' * 64, channel='web'),
        provider_input=object(),
    )
    provider = AsyncMock()
    received_keys = []

    async def validate_then_begin(_session, _user, _context, key):
        received_keys.append(key)
        service._validate_idempotency_key(key)
        raise AssertionError('invalid idempotency input must not create usage')

    monkeypatch.setattr(image_billing.compat, 'map_billing_identity', lambda _raw: identity)
    monkeypatch.setattr(image_billing, '_authorize_image_call', AsyncMock(return_value=SimpleNamespace()))
    monkeypatch.setattr(image_billing, '_prepare_image_call', AsyncMock(return_value=prepared))
    monkeypatch.setattr(image_billing, '_to_provider_form', lambda _prepared, _action: object())
    monkeypatch.setattr(image_billing, 'credit_session', _fake_credit_session)
    monkeypatch.setattr(image_billing, 'begin_image_usage', validate_then_begin)

    with pytest.raises(CreditError) as raised:
        __import__('asyncio').run(
            image_billing.bill_image_call(
                request=Request(headers={'IDEMPOTENCY-KEY': 'bad\x01key'}),
                raw_form_data=object(),
                metadata=None,
                raw_user=object(),
                action='text-to-image',
                authorization_scope='direct',
                invoke=provider,
                finalize=AsyncMock(),
            )
        )

    assert raised.value.code == 'invalid_adjustment'
    assert received_keys == ['bad\x01key']
    provider.assert_not_awaited()


def test_credit_ui_uses_svelte_text_interpolation_for_user_controlled_values() -> None:
    component_root = ROOT / 'src' / 'lib' / 'components' / 'credits'
    component_sources = [path.read_text(encoding='utf-8') for path in component_root.rglob('*.svelte')]

    assert component_sources
    assert all('{@html' not in source for source in component_sources)
    assert '{@html' not in (ROOT / 'src/lib/components/images/Images.svelte').read_text(encoding='utf-8')


def test_router_error_envelope_and_rate_limit_happen_before_sensitive_quote_processing() -> None:
    support_tree = _router_support_source()
    unexpected = _function(support_tree, '_unexpected_error_response')
    unexpected_source = ast.get_source_segment(
        (ROOT / 'backend/open_webui/extensions/credits/router_support.py').read_text(encoding='utf-8'),
        unexpected,
    ) or ''
    assert "CreditError(code='credit_service_unavailable')" in unexpected_source
    assert 'str(error)' not in unexpected_source
    assert 'exc_info' not in unexpected_source

    tree = _router_source()
    quote = _route_function(tree, 'get_image_credit_quote')
    statements = quote.body
    rate_limit_at = next(
        index
        for index, statement in enumerate(statements)
        if any(
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_enforce_rate_limit'
            for node in ast.walk(statement)
        )
    )
    quote_at = next(
        index
        for index, statement in enumerate(statements)
        if any(
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'quote_image'
            for node in ast.walk(statement)
        )
    )
    assert rate_limit_at < quote_at


def test_rate_limit_source_guard_does_not_log_request_payloads() -> None:
    source = (ROOT / 'backend/open_webui/extensions/credits/router_support.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    fallback = _function(tree, '_record_rate_limit_fallback')
    fallback_source = ast.get_source_segment(source, fallback) or ''
    assert 'request' not in fallback_source
    assert 'headers' not in fallback_source
    assert 'prompt' not in fallback_source


@pytest.mark.parametrize(
    ('function_name', 'kwargs'),
    [
        ('generate_image', {'prompt': 'private prompt'}),
        ('edit_image', {'prompt': 'private prompt', 'image_urls': ['data:image/png;base64,secret']}),
    ],
)
def test_builtin_runtime_logs_do_not_include_provider_exception_text(
    monkeypatch, caplog, function_name: str, kwargs: dict[str, object]
) -> None:
    import json
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from open_webui.tools import builtin

    provider_function = 'image_generations' if function_name == 'generate_image' else 'image_edits'
    monkeypatch.setattr(
        builtin,
        provider_function,
        AsyncMock(side_effect=RuntimeError('Authorization Bearer secret prompt base64 remote-ip')),
    )
    caplog.set_level('ERROR', logger=builtin.__name__)

    result = asyncio.run(getattr(builtin, function_name)(**kwargs, __request__=SimpleNamespace()))
    rendered = '\n'.join(f'{record.getMessage()} {record.exc_text or ""}' for record in caplog.records)

    assert json.loads(result)['error']['code'] == 'credit_service_unavailable'
    assert 'Bearer secret' not in rendered
    assert 'private prompt' not in rendered
    assert 'base64' not in rendered
    assert 'remote-ip' not in rendered


def test_builtin_error_path_uses_a_sanitized_domain_envelope_without_secret_logging() -> None:
    source = (ROOT / 'backend/open_webui/tools/builtin.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    error_function = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_image_tool_error'
    )
    error_source = ast.get_source_segment(source, error_function) or ''
    assert "CreditError(code='credit_service_unavailable')" in error_source
    assert 'str(error)' not in error_source
    assert 'repr(error)' not in error_source

    for name in ('generate_image', 'edit_image'):
        function = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == name)
        exception_handlers = [node for node in ast.walk(function) if isinstance(node, ast.ExceptHandler)]
        assert any(
            any(
                isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == '_image_tool_error'
                for call in ast.walk(handler)
            )
            for handler in exception_handlers
        )


def test_structured_credit_log_fields_exclude_authorization_prompt_base64_and_raw_ip() -> None:
    tree = _router_support_source()
    unexpected = _function(tree, '_unexpected_error_response')
    log_calls = [
        node
        for node in ast.walk(unexpected)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'error'
    ]
    assert len(log_calls) == 1
    extra = next(keyword.value for keyword in log_calls[0].keywords if keyword.arg == 'extra')
    assert isinstance(extra, ast.Dict)
    keys = {key.value for key in extra.keys if isinstance(key, ast.Constant) and isinstance(key.value, str)}
    assert keys == {'credit_correlation_id', 'credit_error_type'}


def test_security_source_guard_does_not_allow_direct_private_image_invocations() -> None:
    images_path = ROOT / 'backend/open_webui/routers/images.py'
    tree = ast.parse(images_path.read_text(encoding='utf-8'))
    allowed_owners = {
        '_invoke_image_generations': {'image_generations'},
        '_invoke_image_edits': {'invoke_edit_creations'},
    }
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}

    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
        expected_owners = allowed_owners.get(call.func.id)
        if expected_owners is None:
            continue
        current = call
        owner = None
        while current in parents:
            current = parents[current]
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                owner = current.name
                break
        assert owner in expected_owners
