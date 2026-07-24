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
from open_webui.env import DATABASE_SCHEMA
from open_webui.extensions.creations.db import CreationBase, engine
from sqlalchemy import Connection, text

_LOCK_TIMEOUT_SECONDS = 10.0
_LOCK_POLL_SECONDS = 0.05
_LOCK_NAMESPACE = 'open-webui-creations-migrations'
log = logging.getLogger(__name__)


def _sqlite_lock_path(connection: Connection) -> Path | None:
    database = connection.engine.url.database
    if not database or database == ':memory:' or database.startswith('file::memory:'):
        return None
    path = Path(database).resolve()
    return path.with_name(f'{path.name}.creation-migrations.lock')


def _acquire_sqlite_lock(connection: Connection) -> Path | None:
    lock_path = _sqlite_lock_path(connection)
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


def _postgres_lock_key() -> int:
    digest = hashlib.sha256(_LOCK_NAMESPACE.encode('utf-8')).digest()
    return int.from_bytes(digest[:8], byteorder='big', signed=True)


def _acquire_postgres_lock(connection: Connection) -> int:
    key = _postgres_lock_key()
    deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
    while True:
        acquired = connection.execute(text('SELECT pg_try_advisory_lock(:key)'), {'key': key}).scalar()
        if acquired:
            return key
        if time.monotonic() >= deadline:
            raise TimeoutError('timed out acquiring PostgreSQL creation migration lock')
        time.sleep(_LOCK_POLL_SECONDS)


def _release_postgres_lock(connection: Connection, key: int | None) -> None:
    if key is not None:
        connection.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': key})


def _acquire_database_lock(connection: Connection) -> Any:
    if connection.dialect.name == 'postgresql':
        key = _acquire_postgres_lock(connection)
        connection.commit()
        return key
    if connection.dialect.name == 'sqlite':
        return _acquire_sqlite_lock(connection)
    return None


def _release_database_lock(connection: Connection, lock: Any) -> None:
    if connection.dialect.name == 'postgresql':
        _release_postgres_lock(connection, lock)
        connection.commit()
    elif connection.dialect.name == 'sqlite':
        _release_sqlite_lock(lock)


def _upstream_config() -> Config:
    config = Config()
    config.set_main_option('script_location', str(Path(__file__).parents[3] / 'migrations'))
    return config


def _validate_upstream_head(connection: Connection) -> None:
    expected_heads = set(ScriptDirectory.from_config(_upstream_config()).get_heads())
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


def _migration_config(schema: str | None) -> Config:
    config = Config()
    config.set_main_option('script_location', str(Path(__file__).parent))
    config.attributes['target_metadata'] = CreationBase.metadata
    config.attributes['creation_schema'] = DATABASE_SCHEMA if schema is None else schema
    return config


def _upgrade(connection: Connection, verify_upstream: bool, schema: str | None) -> None:
    config = _migration_config(schema)
    if verify_upstream:
        _validate_upstream_head(connection)
    config.attributes['connection'] = connection
    command.upgrade(config, 'head')
    if connection.in_transaction():
        connection.commit()


def _run_postgres_migration(connection: Connection, verify_upstream: bool, schema: str | None) -> None:
    key: int | None = None
    migration_error: BaseException | None = None
    try:
        key = _acquire_postgres_lock(connection)
        connection.commit()
        _upgrade(connection, verify_upstream=verify_upstream, schema=schema)
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
            log.exception('Failed to release PostgreSQL creation migration lock after migration failure')


def _run_non_postgres_migration(connection: Connection, verify_upstream: bool, schema: str | None) -> None:
    lock: Any = None
    migration_error: BaseException | None = None
    try:
        lock = _acquire_database_lock(connection)
        _upgrade(connection, verify_upstream=verify_upstream, schema=schema)
    except BaseException as error:
        migration_error = error
        if connection.in_transaction():
            connection.rollback()
        raise
    finally:
        try:
            _release_database_lock(connection, lock)
        except Exception:
            if connection.in_transaction():
                connection.rollback()
            if migration_error is None:
                raise
            log.exception('Failed to release creation migration lock after migration failure')


def run_creation_migrations(
    connection: Connection | None = None,
    *,
    verify_upstream: bool = True,
    schema: str | None = None,
) -> None:
    """Upgrade the independent creation migration chain to head; propagate migration failures."""
    owned_connection = connection is None
    live_connection = connection or engine.connect()
    if live_connection.in_transaction():
        if owned_connection:
            live_connection.close()
        raise RuntimeError('creation migrations require a connection without an active transaction')

    try:
        if live_connection.dialect.name == 'postgresql':
            _run_postgres_migration(live_connection, verify_upstream=verify_upstream, schema=schema)
        else:
            _run_non_postgres_migration(live_connection, verify_upstream=verify_upstream, schema=schema)
    finally:
        if owned_connection:
            live_connection.close()


__all__ = ['run_creation_migrations']
