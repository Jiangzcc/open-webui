from __future__ import annotations

import anyio
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from open_webui.env import DATABASE_SCHEMA
from sqlalchemy import inspect

from .db import engine
from .migrations.runner import _migration_config, run_model_ops_migrations


def _validate_model_ops_schema() -> None:
    with engine.connect() as connection:
        inspector = inspect(connection)
        if 'ext_image_model_operation' not in inspector.get_table_names(schema=DATABASE_SCHEMA):
            raise RuntimeError('model ops migration validation failed: missing table')
        expected = set(ScriptDirectory.from_config(_migration_config(DATABASE_SCHEMA)).get_heads())
        current = set(
            MigrationContext.configure(
                connection,
                opts={
                    'version_table': 'ext_model_ops_schema_version',
                    'version_table_schema': DATABASE_SCHEMA,
                },
            ).get_current_heads()
        )
        if current != expected:
            raise RuntimeError(
                f'model ops migration validation failed: expected {sorted(expected)}, got {sorted(current)}'
            )
        checks = {
            item['name']
            for item in inspector.get_check_constraints('ext_image_model_operation', schema=DATABASE_SCHEMA)
        }
        if 'ck_ext_image_model_operation_sort_order' not in checks:
            raise RuntimeError('model ops migration validation failed: missing sort order check')


async def initialize_model_ops_extension(_app: FastAPI) -> None:
    await anyio.to_thread.run_sync(run_model_ops_migrations)
    await anyio.to_thread.run_sync(_validate_model_ops_schema)


__all__ = ['initialize_model_ops_extension']
