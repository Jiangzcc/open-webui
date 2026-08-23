from __future__ import annotations

import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError
import open_webui.env
from open_webui.env import DATABASE_SCHEMA
from sqlalchemy import Connection, text

from .context import migration_context_options
from .spec import MigrationSpec

_LOCK_TIMEOUT_SECONDS = 10.0
_LOCK_POLL_SECONDS = 0.05
_UPSTREAM_MIGRATIONS_DIR = Path(open_webui.env.__file__).parent / 'migrations'
log = logging.getLogger(__name__)


def script_heads(spec: MigrationSpec) -> set[str]:
    """Return the head revision ids of one extension's own migration chain."""
    config = Config()
    config.set_main_option('script_location', str(spec.migrations_dir))
    return set(ScriptDirectory.from_config(config).get_heads())


def build_migration_config(spec: MigrationSpec, schema: str | None = None) -> Config:
    config = Config()
    config.set_main_option('script_location', str(spec.migrations_dir))
    config.attributes['target_metadata'] = spec.metadata
    config.attributes[spec.schema_attribute] = DATABASE_SCHEMA if schema is None else schema
    return config


def _sqlite_lock_path(spec: MigrationSpec, connection: Connection) -> Path | None:
    database = connection.engine.url.database
    if not database or database == ':memory:' or database.startswith('file::memory:'):
        return None
    path = Path(database).resolve()
    return path.with_name(f'{path.name}.{spec.sqlite_lock_suffix}')


def _acquire_sqlite_lock(spec: MigrationSpec, connection: Connection) -> Path | None:
    lock_path = _sqlite_lock_path(spec, connection)
    if lock_path is None:
        return None
    deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
    while True:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(descriptor)
            return lock_path
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f'timed out acquiring SQLite migration lock: {lock_path}')
            time.sleep(_LOCK_POLL_SECONDS)


def _release_sqlite_lock(lock_path: Path | None) -> None:
    if lock_path is None:
        return
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass


def _postgres_lock_key(spec: MigrationSpec) -> int:
    digest = hashlib.sha256(spec.lock_namespace.encode('utf-8')).digest()
    return int.from_bytes(digest[:8], byteorder='big', signed=True)


def _acquire_postgres_lock(spec: MigrationSpec, connection: Connection) -> int:
    key = _postgres_lock_key(spec)
    deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
    while True:
        acquired = connection.execute(text('SELECT pg_try_advisory_lock(:key)'), {'key': key}).scalar()
        if acquired:
            return key
        if time.monotonic() >= deadline:
            raise TimeoutError(f'timed out acquiring PostgreSQL {spec.label} migration lock')
        time.sleep(_LOCK_POLL_SECONDS)


def _release_postgres_lock(connection: Connection, key: int | None) -> None:
    if key is not None:
        connection.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': key})


def _acquire_database_lock(spec: MigrationSpec, connection: Connection) -> Any:
    if connection.dialect.name == 'postgresql':
        key = _acquire_postgres_lock(spec, connection)
        connection.commit()
        return key
    if connection.dialect.name == 'sqlite':
        return _acquire_sqlite_lock(spec, connection)
    return None


def _release_database_lock(spec: MigrationSpec, connection: Connection, lock: Any) -> None:
    if connection.dialect.name == 'postgresql':
        _release_postgres_lock(connection, lock)
        connection.commit()
    elif connection.dialect.name == 'sqlite':
        _release_sqlite_lock(lock)


def _validate_upstream_head(connection: Connection) -> None:
    config = Config()
    config.set_main_option('script_location', str(_UPSTREAM_MIGRATIONS_DIR))
    expected_heads = set(ScriptDirectory.from_config(config).get_heads())
    try:
        migration_context = MigrationContext.configure(
            connection,
            opts={
                'version_table': 'alembic_version',
                'version_table_schema': DATABASE_SCHEMA,
            },
        )
        current_heads = set(migration_context.get_current_heads())
    except Exception as error:
        raise RuntimeError('upstream Alembic head validation failed') from error
    if not expected_heads or current_heads != expected_heads:
        raise RuntimeError(
            f'upstream Alembic migration is not at head: expected {sorted(expected_heads)}, got {sorted(current_heads)}'
        )


def _upgrade(spec: MigrationSpec, connection: Connection, verify_upstream: bool, schema: str | None) -> None:
    config = build_migration_config(spec, schema)
    if verify_upstream:
        _validate_upstream_head(connection)
    config.attributes['connection'] = connection
    try:
        command.upgrade(config, 'head')
    except CommandError as error:
        if "Can't locate revision" in str(error):
            # 迁移链已 squash 为单一 0001 基线（复盘：开发期免兼容历史）。
            # 版本表仍指向旧链 revision 的存量库会走到这里：明确提示处置方式，
            # 避免裸 CommandError 让启动失败难以自诊断。
            raise RuntimeError(
                f'{spec.label} migration version table references a revision that no longer '
                f'exists (migration chain was squashed to a single baseline): {error}. '
                f'For a pre-squash database, delete the {spec.version_table} table '
                '(and the ext_* tables it governs if they were created by the old chain) '
                'or start from a fresh database.'
            ) from error
        raise
    if connection.in_transaction():
        connection.commit()


def _run_postgres_migration(
    spec: MigrationSpec, connection: Connection, verify_upstream: bool, schema: str | None
) -> None:
    key: int | None = None
    migration_error: BaseException | None = None
    try:
        key = _acquire_postgres_lock(spec, connection)
        connection.commit()
        _upgrade(spec, connection, verify_upstream=verify_upstream, schema=schema)
        if connection.in_transaction():
            connection.commit()
    except BaseException as error:
        migration_error = error
        if connection.in_transaction():
            connection.rollback()
        raise
    finally:
        try:
            _release_postgres_lock(connection, key)
            if connection.in_transaction():
                connection.commit()
        except Exception:
            if connection.in_transaction():
                connection.rollback()
            if migration_error is None:
                raise
            log.exception('Failed to release PostgreSQL %s migration lock after migration failure', spec.label)


def _run_non_postgres_migration(
    spec: MigrationSpec, connection: Connection, verify_upstream: bool, schema: str | None
) -> None:
    lock: Any = None
    migration_error: BaseException | None = None
    try:
        lock = _acquire_database_lock(spec, connection)
        _upgrade(spec, connection, verify_upstream=verify_upstream, schema=schema)
    except BaseException as error:
        migration_error = error
        if connection.in_transaction():
            connection.rollback()
        raise
    finally:
        try:
            _release_database_lock(spec, connection, lock)
        except Exception:
            if connection.in_transaction():
                connection.rollback()
            if migration_error is None:
                raise
            log.exception('Failed to release %s migration lock after migration failure', spec.label)


def run_extension_migrations(
    spec: MigrationSpec,
    connection: Connection | None = None,
    *,
    verify_upstream: bool = True,
    schema: str | None = None,
) -> None:
    """Upgrade the extension's independent migration chain to head; propagate failures."""
    owned_connection = connection is None
    live_connection = connection or spec.engine.connect()
    if live_connection.in_transaction():
        if owned_connection:
            live_connection.close()
        raise RuntimeError(f'{spec.label} migrations require a connection without an active transaction')

    try:
        if live_connection.dialect.name == 'postgresql':
            _run_postgres_migration(spec, live_connection, verify_upstream=verify_upstream, schema=schema)
        else:
            _run_non_postgres_migration(spec, live_connection, verify_upstream=verify_upstream, schema=schema)
    finally:
        if owned_connection:
            live_connection.close()


__all__ = ['build_migration_config', 'run_extension_migrations', 'script_heads']
