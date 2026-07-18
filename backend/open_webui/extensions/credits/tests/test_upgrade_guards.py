from __future__ import annotations

import ast
import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).parents[5]
BACKEND = ROOT / 'backend' / 'open_webui'


@dataclass(frozen=True)
class _Actor:
    id: str
    name: str
    email: str
    role: str


def _source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding='utf-8')


def _function(tree: ast.AST, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f'missing function {name}')


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _calls(function: ast.AST, name: str) -> list[ast.Call]:
    return [node for node in ast.walk(function) if isinstance(node, ast.Call) and _call_name(node) == name]


def _keyword(call: ast.Call, name: str) -> ast.expr:
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    raise AssertionError(f'missing {name!r} keyword')


def _statement_index(statements: Iterable[ast.stmt], predicate) -> int:
    for index, statement in enumerate(statements):
        if any(predicate(node) for node in ast.walk(statement)):
            return index
    raise AssertionError('required statement is missing')


def _assert_lifecycle_bridge(source: str) -> None:
    tree = ast.parse(source)
    lifespan = _function(tree, 'lifespan')
    statements = lifespan.body
    initialize_at = _statement_index(
        statements,
        lambda node: isinstance(node, ast.Call) and _call_name(node) == 'initialize_credit_extension',
    )
    ready_at = _statement_index(
        statements,
        lambda node: (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Attribute)
                and isinstance(target.value.value, ast.Name)
                and target.value.value.id == 'app'
                and target.value.attr == 'state'
                and target.attr == 'startup_complete'
                for target in node.targets
            )
        ),
    )
    shutdown_at = _statement_index(
        statements,
        lambda node: isinstance(node, ast.Call) and _call_name(node) == 'shutdown_credit_extension',
    )
    close_session_at = _statement_index(
        statements,
        lambda node: isinstance(node, ast.Call) and _call_name(node) == 'close_session',
    )

    assert initialize_at < ready_at
    assert shutdown_at < close_session_at


def _assert_image_wrapper(source: str, public_name: str, private_name: str, action: str) -> None:
    function = _function(ast.parse(source), public_name)
    calls = _calls(function, 'bill_image_call')
    assert len(calls) == 1
    call = calls[0]
    action_value = _keyword(call, 'action')
    invoke = _keyword(call, 'invoke')
    assert isinstance(action_value, ast.Constant) and action_value.value == action
    assert isinstance(invoke, ast.Lambda)
    assert len(_calls(invoke, private_name)) == 1


def _assert_frontend_mount(source: str, component: str) -> None:
    assert f"import {component} from '$lib/components/credits/{component}.svelte';" in source
    assert f'<{component}' in source


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _containing_function(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str | None:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
    return None


def _production_python_files() -> list[Path]:
    return [path for path in BACKEND.rglob('*.py') if 'tests' not in path.parts and '__pycache__' not in path.parts]


def _non_extension_schema_fingerprint(connection) -> dict[str, object]:
    inspector = inspect(connection)
    fingerprint: dict[str, object] = {}
    for table_name in inspector.get_table_names():
        if table_name.startswith('ext_') or table_name == 'alembic_version':
            continue
        fingerprint[table_name] = {
            'columns': tuple(
                (column['name'], str(column['type']), column['nullable'], str(column.get('default')))
                for column in inspector.get_columns(table_name)
            ),
            'indexes': tuple(
                sorted(
                    (index['name'], tuple(index['column_names']), index['unique'])
                    for index in inspector.get_indexes(table_name)
                )
            ),
            'unique': tuple(
                sorted(
                    (constraint['name'], tuple(constraint['column_names']))
                    for constraint in inspector.get_unique_constraints(table_name)
                )
            ),
            'foreign_keys': tuple(
                sorted(
                    (
                        constraint.get('name'),
                        tuple(constraint['constrained_columns']),
                        constraint.get('referred_table'),
                        tuple(constraint['referred_columns']),
                        constraint.get('options', {}).get('ondelete'),
                    )
                    for constraint in inspector.get_foreign_keys(table_name)
                )
            ),
            'checks': tuple(
                sorted(
                    (constraint['name'], constraint['sqltext'])
                    for constraint in inspector.get_check_constraints(table_name)
                )
            ),
        }
    return fingerprint


def test_guard_helpers_reject_a_fixture_with_removed_or_bypassed_bridges() -> None:
    main_source = _source('backend/open_webui/main.py')
    removed_lifecycle = main_source.replace('    await initialize_credit_extension(app)\n', '', 1)
    try:
        _assert_lifecycle_bridge(removed_lifecycle)
    except AssertionError:
        pass
    else:
        raise AssertionError('the lifecycle guard did not fail after its bridge was removed')

    image_source = _source('backend/open_webui/routers/images.py')
    bypassed_wrapper = image_source.replace(
        'invoke=lambda provider_form: _invoke_image_generations',
        'invoke=lambda provider_form: provider_form',
        1,
    )
    try:
        _assert_image_wrapper(bypassed_wrapper, 'image_generations', '_invoke_image_generations', 'text-to-image')
    except AssertionError:
        pass
    else:
        raise AssertionError('the image wrapper guard did not fail after its supplier bridge was replaced')


def test_static_bridges_keep_router_lifecycle_channels_and_frontend_mounts() -> None:
    main_source = _source('backend/open_webui/main.py')
    _assert_lifecycle_bridge(main_source)
    assert main_source.count('from open_webui.extensions.credits.router import router as credits_router') == 1
    assert main_source.count('app.include_router(credits_router)') == 1

    image_source = _source('backend/open_webui/routers/images.py')
    _assert_image_wrapper(image_source, 'image_generations', '_invoke_image_generations', 'text-to-image')
    _assert_image_wrapper(image_source, 'image_edits', '_invoke_image_edits', 'image-to-image')

    builtin_source = _source('backend/open_webui/tools/builtin.py')
    builtin_tree = ast.parse(builtin_source)
    for name, public_call in (('generate_image', 'image_generations'), ('edit_image', 'image_edits')):
        function = _function(builtin_tree, name)
        assert '__metadata__' in [argument.arg for argument in function.args.args]
        assert len(_calls(function, public_call)) == 1
        metadata = _keyword(_calls(function, public_call)[0], 'metadata')
        assert isinstance(metadata, ast.Call) and _call_name(metadata) == '_image_credit_metadata'
    metadata_function = _function(builtin_tree, '_image_credit_metadata')
    assert "'credit_channel': 'tool'" in ast.get_source_segment(builtin_source, metadata_function)

    middleware_source = _source('backend/open_webui/utils/middleware.py')
    middleware_tree = ast.parse(middleware_source)
    assert _function(middleware_tree, 'build_tool_credit_metadata')
    assert _function(middleware_tree, 'build_chat_image_credit_metadata')
    assert "credit_metadata['call_instance_id'] = tool_call_id" in middleware_source
    assert "'credit_channel': 'chat'" in middleware_source

    _assert_frontend_mount(_source('src/lib/components/layout/Sidebar/UserMenu.svelte'), 'CreditMenuEntry')
    _assert_frontend_mount(_source('src/lib/components/images/Images.svelte'), 'ImageCreditQuoteBadge')
    admin_source = _source('src/routes/(app)/admin/+layout.svelte')
    assert 'href="/admin/credits"' in admin_source
    assert "includes('/admin/credits')" in admin_source


def test_all_image_production_callers_use_public_wrappers_and_only_wrappers_call_private_invokers() -> None:
    expected_public_callers = {
        'backend/open_webui/routers/images.py': {'image_generations', 'image_edits'},
        'backend/open_webui/tools/builtin.py': {'image_generations', 'image_edits'},
        'backend/open_webui/utils/middleware.py': {'image_generations', 'image_edits'},
    }
    observed_public_callers: dict[str, set[str]] = {}

    for path in _production_python_files():
        tree = ast.parse(path.read_text(encoding='utf-8'))
        parents = _parent_map(tree)
        relative = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = _call_name(node)
            if called in {'image_generations', 'image_edits'}:
                observed_public_callers.setdefault(relative, set()).add(called)
            if called in {'_invoke_image_generations', '_invoke_image_edits'}:
                required_public = called.removeprefix('_invoke_')
                assert relative == 'backend/open_webui/routers/images.py'
                assert _containing_function(node, parents) == required_public

    for path, public_functions in expected_public_callers.items():
        assert public_functions <= observed_public_callers.get(path, set())


def test_credit_price_crud_routes_delegate_to_the_compatibility_event_boundary() -> None:
    source = _source('backend/open_webui/extensions/credits/router.py')
    tree = ast.parse(source)

    for function_name, operation in (
        ('create_credit_price', 'created'),
        ('update_credit_price', 'updated'),
        ('delete_credit_price', 'deleted'),
    ):
        function = _function(tree, function_name)
        publish_calls = _calls(function, '_publish_price_event')
        assert len(publish_calls) == 1
        operation_value = publish_calls[0].args[3]
        assert isinstance(operation_value, ast.Constant) and operation_value.value == operation

    publish = _function(tree, '_publish_price_event')
    compat_calls = _calls(publish, 'publish_credit_price_event')
    assert len(compat_calls) == 1
    payload = _keyword(compat_calls[0], 'data')
    assert isinstance(payload, ast.Dict)
    keys = {key.value for key in payload.keys if isinstance(key, ast.Constant) and isinstance(key.value, str)}
    assert keys == {
        'price_id',
        'service_type',
        'resource_id',
        'action',
        'operator_id',
        'request_id',
        'changed_fields',
    }
    assert 'rules' not in keys
    assert 'base_price' not in keys


def test_credit_migration_leaves_every_non_extension_schema_object_unchanged(tmp_path) -> None:
    from open_webui.extensions.credits.migrations.runner import run_credit_migrations

    engine = create_engine(f'sqlite:///{tmp_path / "upgrade-guard.sqlite"}')
    try:
        with engine.begin() as connection:
            connection.execute(text('CREATE TABLE user (id TEXT PRIMARY KEY, name TEXT NOT NULL)'))
            connection.execute(text('CREATE INDEX ix_user_name ON user (name)'))
            connection.execute(
                text(
                    'CREATE TABLE upstream_settings ('
                    'id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, value TEXT NOT NULL, '
                    'CONSTRAINT ck_upstream_settings_value CHECK (length(value) > 0), '
                    'FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE'
                    ')'
                )
            )
            before = _non_extension_schema_fingerprint(connection)

        with engine.connect() as connection:
            run_credit_migrations(connection=connection, verify_upstream=False)

        with engine.connect() as connection:
            assert _non_extension_schema_fingerprint(connection) == before
    finally:
        engine.dispose()


def test_compat_event_contract_keeps_all_operations_publishable_and_narrow() -> None:
    from open_webui import events
    from open_webui.extensions.credits import compat

    calls = []

    async def publish_event(_request, event, **kwargs):
        calls.append((event, kwargs))

    original = events.publish_event
    events.publish_event = publish_event
    actor = _Actor(id='admin-1', name='Admin', email='admin@example.test', role='admin')
    try:
        for operation in ('created', 'updated', 'deleted'):
            asyncio.run(
                compat.publish_credit_price_event(
                    object(),
                    operation,
                    actor=actor,
                    subject_id='price-1',
                    data={'changed_fields': ['enabled']},
                )
            )
    finally:
        events.publish_event = original

    assert [events.event_name(event) for event, _ in calls] == [
        events.EVENTS.MODEL_PROVIDER_MODEL_CREATED.name,
        events.EVENTS.MODEL_PROVIDER_CONFIG_UPDATED.name,
        events.EVENTS.MODEL_PROVIDER_MODEL_DELETED.name,
    ]
    assert all(kwargs['subject_type'] == 'credit_price' for _, kwargs in calls)
    expected_data = [
        {'credit_price_operation': operation, 'changed_fields': ['enabled']}
        for operation in ('created', 'updated', 'deleted')
    ]
    assert [kwargs['data'] for _, kwargs in calls] == expected_data
