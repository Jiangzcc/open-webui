from __future__ import annotations

import anyio
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from open_webui.env import DATABASE_SCHEMA
from sqlalchemy import inspect

from .db import engine
from .migrations.runner import _migration_config, run_provider_ops_migrations


def _validate_provider_ops_schema() -> None:
    with engine.connect() as connection:
        inspector = inspect(connection)
        required_tables = {
            'ext_provider_invocation',
            'ext_provider_price_snapshot',
            'ext_provider_billing_event',
            'ext_provider_request_record',
            'ext_provider_usage_bucket',
            'ext_provider_analytics_bucket',
            'ext_provider_sync_run',
        }
        missing = required_tables - set(inspector.get_table_names(schema=DATABASE_SCHEMA))
        if missing:
            raise RuntimeError(f'provider ops migration validation failed: missing tables {sorted(missing)}')
        expected = set(ScriptDirectory.from_config(_migration_config(DATABASE_SCHEMA)).get_heads())
        current = set(
            MigrationContext.configure(
                connection,
                opts={
                    'version_table': 'ext_provider_ops_schema_version',
                    'version_table_schema': DATABASE_SCHEMA,
                },
            ).get_current_heads()
        )
        if current != expected:
            raise RuntimeError(
                f'provider ops migration validation failed: expected {sorted(expected)}, got {sorted(current)}'
            )


async def initialize_provider_ops_extension(_app: FastAPI) -> None:
    await anyio.to_thread.run_sync(run_provider_ops_migrations)
    await anyio.to_thread.run_sync(_validate_provider_ops_schema)


__all__ = ['initialize_provider_ops_extension']
