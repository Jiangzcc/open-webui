from __future__ import annotations

import logging

import anyio
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from open_webui.env import DATABASE_SCHEMA
from sqlalchemy import inspect

from .db import engine
from .migrations.runner import _migration_config, run_creation_migrations
from .models import CreationBase

log = logging.getLogger(__name__)

_REQUIRED_TABLES = frozenset(table.name for table in CreationBase.metadata.sorted_tables)
_REQUIRED_UNIQUE = {'ext_creation_media_item': frozenset({'uq_ext_creation_media_file'})}
_REQUIRED_CHECKS = {
    'ext_creation_media_item': frozenset(
        {
            'ck_ext_creation_media_kind',
            'ck_ext_creation_media_task',
            'ck_ext_creation_media_source',
        }
    ),
}
_REQUIRED_INDEXES = {
    'ext_creation_media_item': frozenset(
        {
            'ix_ext_creation_media_user_visible_created',
            'ix_ext_creation_media_visible_created',
            'ix_ext_creation_media_batch',
        }
    ),
}


def _schema_tables(inspector) -> set[str]:
    return set(inspector.get_table_names(schema=DATABASE_SCHEMA))


def _validate_creation_schema() -> None:
    with engine.connect() as connection:
        inspector = inspect(connection)
        missing_tables = _REQUIRED_TABLES - _schema_tables(inspector)
        if missing_tables:
            raise RuntimeError(f'creation migration validation failed: missing tables {sorted(missing_tables)}')

        config = _migration_config(DATABASE_SCHEMA)
        expected_heads = set(ScriptDirectory.from_config(config).get_heads())
        current_heads = set(
            MigrationContext.configure(
                connection,
                opts={
                    'version_table': 'ext_creation_schema_version',
                    'version_table_schema': DATABASE_SCHEMA,
                },
            ).get_current_heads()
        )
        if current_heads != expected_heads:
            raise RuntimeError(
                'creation migration validation failed: '
                f'expected version {sorted(expected_heads)}, got {sorted(current_heads)}'
            )

        for table_name, required in _REQUIRED_UNIQUE.items():
            existing = {
                constraint['name']
                for constraint in inspector.get_unique_constraints(table_name, schema=DATABASE_SCHEMA)
            }
            missing = required - existing
            if missing:
                raise RuntimeError(
                    f'creation migration validation failed: {table_name} missing unique constraints {sorted(missing)}'
                )

        for table_name, required in _REQUIRED_CHECKS.items():
            existing = {
                constraint['name'] for constraint in inspector.get_check_constraints(table_name, schema=DATABASE_SCHEMA)
            }
            missing = required - existing
            if missing:
                raise RuntimeError(
                    f'creation migration validation failed: {table_name} missing check constraints {sorted(missing)}'
                )

        for table_name, required in _REQUIRED_INDEXES.items():
            existing = {index['name'] for index in inspector.get_indexes(table_name, schema=DATABASE_SCHEMA)}
            missing = required - existing
            if missing:
                raise RuntimeError(
                    f'creation migration validation failed: {table_name} missing indexes {sorted(missing)}'
                )

        for table_name in _REQUIRED_TABLES:
            foreign_keys = inspector.get_foreign_keys(table_name, schema=DATABASE_SCHEMA)
            if foreign_keys:
                raise RuntimeError(f'creation migration validation failed: {table_name} must not declare foreign keys')


async def initialize_creations_extension(app: FastAPI) -> None:
    """Run the creation migration chain and validate the resulting schema.

    Creations has no background worker and no shutdown hook: capture
    finalization piggy-backs on the credits terminal transaction, and soft
    deletes need no periodic reconciliation.
    """
    await anyio.to_thread.run_sync(run_creation_migrations)
    await anyio.to_thread.run_sync(_validate_creation_schema)


__all__ = ['initialize_creations_extension']
