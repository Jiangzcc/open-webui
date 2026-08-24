from __future__ import annotations

import asyncio
import logging
from time import time

import anyio
from fastapi import FastAPI
from open_webui.extensions.migration_kit import SchemaGuard, validate_schema
from opentelemetry import metrics

from .constants import CREDIT_RECOVERY_INTERVAL_SECONDS, CREDIT_USAGE_STALE_SECONDS
from .migrations.runner import SPEC, run_credit_migrations
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
    'ext_credit_redeem_batch': frozenset(
        {
            'ck_ext_credit_redeem_batch_face_value',
            'ck_ext_credit_redeem_batch_code_count',
            'ck_ext_credit_redeem_batch_user_limit',
            'ck_ext_credit_redeem_batch_expiry',
            'ck_ext_credit_redeem_batch_void_fields',
        }
    ),
    'ext_credit_redeem_code': frozenset(
        {
            'ck_ext_credit_redeem_code_terminal_state',
            'ck_ext_credit_redeem_code_redemption_fields',
            'ck_ext_credit_redeem_code_void_fields',
        }
    ),
    'ext_credit_redeem_audit': frozenset(
        {'ck_ext_credit_redeem_audit_action', 'ck_ext_credit_redeem_audit_request_source'}
    ),
}
_REQUIRED_INDEXES = {
    'ext_credit_ledger': frozenset({'ux_ext_credit_ledger_related_refund'}),
    'ext_credit_redeem_code': frozenset(
        {'ux_ext_credit_redeem_code_hash', 'ux_ext_credit_redeem_code_ledger'}
    ),
}
_recovery_counter = metrics.get_meter(__name__).create_counter(
    'webui.credits.usage.recovered_unknown',
    description='Counts stale unfinished credit usages transitioned to unknown.',
    unit='1',
)


def _now() -> int:
    return int(time())


# 台账/卡密链的外键关系必须与迁移建出的完全一致（应用层不再另查）。
_SCHEMA_GUARD = SchemaGuard(
    spec=SPEC,
    required_tables=_REQUIRED_TABLES,
    required_checks=_REQUIRED_CONSTRAINTS,
    required_indexes=_REQUIRED_INDEXES,
    expected_foreign_keys={
        'ext_credit_ledger': frozenset({'ext_credit_account', 'ext_credit_usage'}),
        'ext_credit_redeem_code': frozenset({'ext_credit_redeem_batch', 'ext_credit_ledger'}),
        'ext_credit_redeem_audit': frozenset({'ext_credit_redeem_batch', 'ext_credit_redeem_code'}),
    },
)


def _validate_credit_schema() -> None:
    validate_schema(_SCHEMA_GUARD)


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
