from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

from alembic import command
from alembic.config import Config
from open_webui.env import DATABASE_SCHEMA
from open_webui.extensions.model_ops.db import ModelOpsBase, engine
from sqlalchemy import Connection, text

_LOCK_TIMEOUT_SECONDS = 10.0
_LOCK_POLL_SECONDS = 0.05
_LOCK_NAMESPACE = 'open-webui-model-ops-migrations'


def _migration_config(schema: str | None) -> Config:
    config = Config()
    config.set_main_option('script_location', str(Path(__file__).parent))
    config.attributes['target_metadata'] = ModelOpsBase.metadata
    config.attributes['model_ops_schema'] = DATABASE_SCHEMA if schema is None else schema
    return config


def _sqlite_lock_path(connection: Connection) -> Path | None:
    database = connection.engine.url.database
    if not database or database == ':memory:' or database.startswith('file::memory:'):
        return None
    path = Path(database).resolve()
    return path.with_name(f'{path.name}.model-ops-migrations.lock')


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


def _postgres_lock_key() -> int:
    digest = hashlib.sha256(_LOCK_NAMESPACE.encode()).digest()
    return int.from_bytes(digest[:8], byteorder='big', signed=True)


def run_model_ops_migrations(  # noqa: C901 - lock acquisition and cleanup share one transaction boundary
    connection: Connection | None = None,
    *,
    schema: str | None = None,
) -> None:
    owned = connection is None
    live = connection or engine.connect()
    if live.in_transaction():
        if owned:
            live.close()
        raise RuntimeError('model ops migrations require a connection without an active transaction')
    sqlite_lock: Path | None = None
    postgres_key: int | None = None
    try:
        if live.dialect.name == 'sqlite':
            sqlite_lock = _acquire_sqlite_lock(live)
        elif live.dialect.name == 'postgresql':
            postgres_key = _postgres_lock_key()
            live.execute(text('SELECT pg_advisory_lock(:key)'), {'key': postgres_key})
            live.commit()
        config = _migration_config(schema)
        config.attributes['connection'] = live
        command.upgrade(config, 'head')
        if live.in_transaction():
            live.commit()
    except BaseException:
        if live.in_transaction():
            live.rollback()
        raise
    finally:
        if live.dialect.name == 'postgresql' and postgres_key is not None:
            live.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': postgres_key})
            live.commit()
        if sqlite_lock is not None:
            try:
                sqlite_lock.unlink()
            except FileNotFoundError:
                pass
        if owned:
            live.close()


__all__ = ['run_model_ops_migrations']
