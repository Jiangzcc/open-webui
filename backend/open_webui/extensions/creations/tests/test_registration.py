from __future__ import annotations

from types import SimpleNamespace

import pytest
from open_webui.extensions.creations import registration


def _app() -> SimpleNamespace:
    return SimpleNamespace(state=SimpleNamespace())


@pytest.mark.asyncio
async def test_initialization_runs_migration_then_schema_validation(monkeypatch) -> None:
    calls: list[str] = []

    async def run_sync(function):
        calls.append(function.__name__)
        function()

    monkeypatch.setattr(registration.anyio.to_thread, 'run_sync', run_sync)

    def run_creation_migrations():  # noqa: A001 - mirrors the registered name
        calls.append('migrated')

    def _validate_creation_schema():  # noqa: A001 - mirrors the registered name
        calls.append('validated')

    monkeypatch.setattr(registration, 'run_creation_migrations', run_creation_migrations)
    monkeypatch.setattr(registration, '_validate_creation_schema', _validate_creation_schema)
    monkeypatch.setattr(registration, 'recover_incomplete_generation_tasks', lambda _request: _async_value(0))
    app = _app()
    await registration.initialize_creations_extension(app)
    assert calls == [
        'run_creation_migrations',
        'migrated',
        '_validate_creation_schema',
        'validated',
    ]
    assert app.state.creation_generation_tasks == {}
    await registration.shutdown_creations_extension(app)


@pytest.mark.asyncio
async def test_initialization_failure_propagates(monkeypatch) -> None:
    async def fail(_function):
        raise RuntimeError('creation migration failed')

    monkeypatch.setattr(registration.anyio.to_thread, 'run_sync', fail)
    with pytest.raises(RuntimeError, match='creation migration failed'):
        await registration.initialize_creations_extension(_app())


@pytest.mark.asyncio
async def test_initialization_registers_generation_task_registry(monkeypatch) -> None:
    app = _app()
    monkeypatch.setattr(registration, 'run_creation_migrations', lambda: None)
    monkeypatch.setattr(registration, '_validate_creation_schema', lambda: None)
    monkeypatch.setattr(registration, 'recover_incomplete_generation_tasks', lambda _request: _async_value(0))
    await registration.initialize_creations_extension(app)
    assert app.state.creation_generation_tasks == {}
    assert not hasattr(app.state, 'credit_recovery_task')
    await registration.shutdown_creations_extension(app)


async def _async_value(value):
    return value


def test_initialize_creations_extension_has_shutdown_partner() -> None:
    assert hasattr(registration, 'shutdown_creations_extension')


def test_main_py_initializes_creations_after_credits_and_includes_router_once() -> None:
    from pathlib import Path

    main_path = Path(__file__).resolve().parents[3] / 'main.py'
    source = main_path.read_text(encoding='utf-8')
    assert 'initialize_creations_extension' in source
    assert 'creations_router' in source
    assert 'initialize_credit_extension' in source
    # creations initializer must come after the credits initializer
    assert source.index('initialize_credit_extension') < source.index('initialize_creations_extension')
    # router included exactly once
    assert source.count('include_router(creations_router)') == 1
    assert source.index('shutdown_creations_extension(app)') < source.index('shutdown_credit_extension(app)')
