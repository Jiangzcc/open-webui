from __future__ import annotations

import asyncio
import logging
from time import time

import anyio
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from open_webui.env import DATABASE_SCHEMA
from opentelemetry import metrics
from sqlalchemy import inspect

from .constants import CREDIT_RECOVERY_INTERVAL_SECONDS, CREDIT_USAGE_STALE_SECONDS
from .db import engine
from .migrations.runner import _migration_config, run_credit_migrations
from .models import CreditBase
from .service import mark_stale_usage_unknown

log = logging.getLogger(__name__)
_RECOVERY_TASK_NAME = 'credit-usage-recovery'
_REQUIRED_TABLES = frozenset(table.name for table in CreditBase.metadata.sorted_tables)
_REQUIRED_CONSTRAINTS = {
    'ext_credit_account': frozenset({'ck_ext_credit_account_balance_nonnegative'}),
    'ext_credit_usage': frozenset(
        {
            'ck_ext_credit_usage_status',
            'ck_ext_credit_usage_channel',
            'ck_ext_credit_usage_charged_nonnegative',
            'ck_ext_credit_usage_exempt_consistency',
        }
    ),
    'ext_credit_ledger': frozenset(
        {
            'ck_ext_credit_ledger_balance_equation',
            'ck_ext_credit_ledger_balance_nonnegative',
            'ck_ext_credit_ledger_entry_type',
            'ck_ext_credit_ledger_request_source',
            'ck_ext_credit_ledger_reason_code',
        }
    ),
    'ext_credit_price': frozenset({'ck_ext_credit_price_base_nonempty'}),
}
_REQUIRED_INDEXES = {
    'ext_credit_ledger': frozenset({'ux_ext_credit_ledger_related_refund'}),
}
_recovery_counter = metrics.get_meter(__name__).create_counter(
    'webui.credits.usage.recovered_unknown',
    description='Counts stale unfinished credit usages transitioned to unknown.',
    unit='1',
)


def _now() -> int:
    return int(time())


def _schema_tables(inspector) -> set[str]:
    return set(inspector.get_table_names(schema=DATABASE_SCHEMA))


def _validate_credit_schema() -> None:
    with engine.connect() as connection:
        inspector = inspect(connection)
        missing_tables = _REQUIRED_TABLES - _schema_tables(inspector)
        if missing_tables:
            raise RuntimeError(f'credit migration validation failed: missing tables {sorted(missing_tables)}')

        config = _migration_config(DATABASE_SCHEMA)
        expected_heads = set(ScriptDirectory.from_config(config).get_heads())
        current_heads = set(
            MigrationContext.configure(
                connection,
                opts={
                    'version_table': 'ext_credit_schema_version',
                    'version_table_schema': DATABASE_SCHEMA,
                },
            ).get_current_heads()
        )
        if current_heads != expected_heads:
            raise RuntimeError(
                'credit migration validation failed: '
                f'expected version {sorted(expected_heads)}, got {sorted(current_heads)}'
            )

        for table_name, required in _REQUIRED_CONSTRAINTS.items():
            existing = {
                constraint['name'] for constraint in inspector.get_check_constraints(table_name, schema=DATABASE_SCHEMA)
            }
            missing = required - existing
            if missing:
                raise RuntimeError(
                    f'credit migration validation failed: {table_name} missing constraints {sorted(missing)}'
                )

        for table_name, required in _REQUIRED_INDEXES.items():
            existing = {index['name'] for index in inspector.get_indexes(table_name, schema=DATABASE_SCHEMA)}
            missing = required - existing
            if missing:
                raise RuntimeError(
                    f'credit migration validation failed: {table_name} missing indexes {sorted(missing)}'
                )


def _record_recovered_usages(count: int) -> None:
    if count > 0:
        _recovery_counter.add(count)


async def _recover_stale_usages() -> int:
    count = await mark_stale_usage_unknown(_now() - CREDIT_USAGE_STALE_SECONDS)
    _record_recovered_usages(count)
    return count


async def _credit_recovery_worker() -> None:
    while True:
        await asyncio.sleep(CREDIT_RECOVERY_INTERVAL_SECONDS)
        try:
            await _recover_stale_usages()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception('Credit usage recovery pass failed')


async def initialize_credit_extension(app: FastAPI) -> None:
    """Run migration validation and start the single recovery task."""
    existing = getattr(app.state, 'credit_recovery_task', None)
    if existing is not None and not existing.done():
        return

    await anyio.to_thread.run_sync(run_credit_migrations)
    await anyio.to_thread.run_sync(_validate_credit_schema)
    app.state.credit_recovery_task = asyncio.create_task(
        _credit_recovery_worker(),
        name=_RECOVERY_TASK_NAME,
    )


async def shutdown_credit_extension(app: FastAPI) -> None:
    """Cancel and await the recovery task before shared resources close."""
    task = getattr(app.state, 'credit_recovery_task', None)
    if task is None:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    delattr(app.state, 'credit_recovery_task')


__all__ = ['initialize_credit_extension', 'shutdown_credit_extension']
