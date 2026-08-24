from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from alembic.util.exc import CommandError
from open_webui.extensions.migration_kit import runner

from .test_runner import _synthetic_spec


def test_sqlite_release_and_unknown_dialect_are_noops(tmp_path) -> None:
    runner._release_sqlite_lock(None)
    runner._release_sqlite_lock(tmp_path / 'missing.lock')
    connection = SimpleNamespace(dialect=SimpleNamespace(name='other'))
    assert runner._acquire_database_lock(_synthetic_spec(None), connection) is None
    runner._release_database_lock(_synthetic_spec(None), connection, None)


def test_postgres_database_lock_commits_acquire_and_release(monkeypatch) -> None:
    connection = SimpleNamespace(
        dialect=SimpleNamespace(name='postgresql'),
        commit=Mock(),
    )
    monkeypatch.setattr(runner, '_acquire_postgres_lock', lambda _spec, _connection: 7)
    monkeypatch.setattr(runner, '_release_postgres_lock', Mock())
    assert runner._acquire_database_lock(_synthetic_spec(None), connection) == 7
    runner._release_database_lock(_synthetic_spec(None), connection, 7)
    assert connection.commit.call_count == 2


def test_upstream_validation_maps_context_errors_and_head_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(
        runner.ScriptDirectory,
        'from_config',
        lambda _config: SimpleNamespace(get_heads=lambda: ['expected']),
    )
    monkeypatch.setattr(
        runner.MigrationContext,
        'configure',
        Mock(side_effect=RuntimeError('database')),
    )
    with pytest.raises(RuntimeError, match='validation failed'):
        runner._validate_upstream_head(object())

    monkeypatch.setattr(
        runner.MigrationContext,
        'configure',
        lambda *_args, **_kwargs: SimpleNamespace(get_current_heads=lambda: ['actual']),
    )
    with pytest.raises(RuntimeError, match='not at head'):
        runner._validate_upstream_head(object())


def test_upgrade_propagates_non_stale_command_error_and_commits(monkeypatch) -> None:
    connection = SimpleNamespace(
        in_transaction=Mock(return_value=False),
        commit=Mock(),
    )
    monkeypatch.setattr(runner.command, 'upgrade', Mock(side_effect=CommandError('other')))
    with pytest.raises(CommandError, match='other'):
        runner._upgrade(
            _synthetic_spec(None),
            connection,
            verify_upstream=False,
            schema=None,
        )

    runner.command.upgrade = Mock()
    connection.in_transaction.return_value = True
    runner._upgrade(
        _synthetic_spec(None),
        connection,
        verify_upstream=False,
        schema=None,
    )
    connection.commit.assert_called_once()


def test_postgres_migration_rolls_back_and_surfaces_release_failure(monkeypatch) -> None:
    connection = SimpleNamespace(
        active=True,
        commit=Mock(),
        rollback=Mock(),
        in_transaction=lambda: connection.active,
    )
    monkeypatch.setattr(runner, '_acquire_postgres_lock', lambda *_args: 1)

    def fail_upgrade(*_args, **_kwargs):
        raise ValueError('migration')

    monkeypatch.setattr(runner, '_upgrade', fail_upgrade)
    monkeypatch.setattr(
        runner,
        '_release_postgres_lock',
        Mock(side_effect=RuntimeError('release')),
    )
    with pytest.raises(ValueError, match='migration'):
        runner._run_postgres_migration(
            _synthetic_spec(None),
            connection,
            verify_upstream=False,
            schema=None,
        )
    assert connection.rollback.call_count >= 1


def test_non_postgres_release_failure_is_raised_without_migration_error(monkeypatch) -> None:
    connection = SimpleNamespace(
        in_transaction=Mock(return_value=False),
        rollback=Mock(),
    )
    monkeypatch.setattr(runner, '_acquire_database_lock', lambda *_args: object())
    monkeypatch.setattr(runner, '_upgrade', lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        runner,
        '_release_database_lock',
        Mock(side_effect=RuntimeError('release')),
    )
    with pytest.raises(RuntimeError, match='release'):
        runner._run_non_postgres_migration(
            _synthetic_spec(None),
            connection,
            verify_upstream=False,
            schema=None,
        )


def test_owned_connection_is_closed_after_success(monkeypatch) -> None:
    connection = SimpleNamespace(
        dialect=SimpleNamespace(name='other'),
        in_transaction=Mock(return_value=False),
        close=Mock(),
    )
    spec = _synthetic_spec(SimpleNamespace(connect=lambda: connection))
    monkeypatch.setattr(runner, '_run_non_postgres_migration', Mock())
    runner.run_extension_migrations(spec, verify_upstream=False)
    connection.close.assert_called_once()
