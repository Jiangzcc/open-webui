from __future__ import annotations

from time import time
from typing import Final
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .constants import (
    MAX_CREDIT_VALUE,
    MAX_NOTE_LENGTH,
    MAX_REQUEST_ID_LENGTH,
    MAX_USER_EMAIL_LENGTH,
    MAX_USER_ID_LENGTH,
    MAX_USER_NAME_LENGTH,
)
from .metrics import credit_metrics
from .models import CreditAccount, CreditLedger
from .repository import insert_ledger
from .schemas import UserSnapshot

_REPAIR_REQUEST_PREFIX: Final = 'repair:'
_REPAIR_SOURCE: Final = 'internal_admin'
_REPAIR_ENTRY_TYPE: Final = 'system_adjustment'
_REPAIR_REASON: Final = 'ledger_reconciliation'


class CreditRepairError(ValueError):
    """Raised when an explicit operator-led ledger repair cannot be safely applied."""


def _repair_request_id(incident_id: str) -> str:
    if not isinstance(incident_id, str):
        raise CreditRepairError('incident_id must be a printable ASCII string')
    normalized = incident_id.strip()
    maximum_incident_length = MAX_REQUEST_ID_LENGTH - len(_REPAIR_REQUEST_PREFIX)
    if (
        not normalized
        or len(normalized) > maximum_incident_length
        or any(not '\x20' <= character <= '\x7e' for character in normalized)
    ):
        raise CreditRepairError('incident_id must fit in the audit request id')
    return f'{_REPAIR_REQUEST_PREFIX}{normalized}'


def _validate_operator(operator: UserSnapshot) -> None:
    values = (
        ('id', operator.id, MAX_USER_ID_LENGTH, False),
        ('name', operator.name, MAX_USER_NAME_LENGTH, True),
        ('email', operator.email, MAX_USER_EMAIL_LENGTH, True),
    )
    for field, value, limit, nullable in values:
        if value is None and nullable:
            continue
        if (
            not isinstance(value, str)
            or not value
            or len(value) > limit
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            raise CreditRepairError(f'operator {field} is invalid')


def _validate_repair_inputs(expected_balance: int, note: str, backup_confirmed: bool) -> str:
    if backup_confirmed is not True:
        raise CreditRepairError('A verified backup confirmation is required before repairing an account')
    if isinstance(expected_balance, bool) or not isinstance(expected_balance, int):
        raise CreditRepairError('expected_balance must be an integer')
    if not 0 <= expected_balance <= MAX_CREDIT_VALUE:
        raise CreditRepairError('expected_balance is outside the supported credit balance range')
    if not isinstance(note, str) or not (normalized_note := note.strip()):
        raise CreditRepairError('note must describe the verified repair incident')
    if len(normalized_note) > MAX_NOTE_LENGTH:
        raise CreditRepairError('note exceeds the maximum supported length')
    return normalized_note


async def _locked_account(session: AsyncSession, user_id: str) -> CreditAccount:
    account = await session.scalar(select(CreditAccount).where(CreditAccount.user_id == user_id).with_for_update())
    if account is None:
        raise CreditRepairError('credit account does not exist; no repair was applied')
    return account


async def _ledger_total(session: AsyncSession, account_id: str) -> int:
    total = await session.scalar(
        select(func.coalesce(func.sum(CreditLedger.amount), 0)).where(CreditLedger.account_id == account_id)
    )
    return int(total)


async def _existing_evidence(session: AsyncSession, account_id: str, request_id: str) -> CreditLedger | None:
    return await session.scalar(
        select(CreditLedger).where(
            CreditLedger.account_id == account_id,
            CreditLedger.entry_type == _REPAIR_ENTRY_TYPE,
            CreditLedger.request_id == request_id,
        )
    )


async def repair_account_from_ledger(
    session: AsyncSession,
    user_id: str,
    operator: UserSnapshot,
    incident_id: str,
    expected_balance: int,
    note: str,
    *,
    backup_confirmed: bool = False,
) -> CreditLedger:
    """Calibrate one account to its ledger total after a verified database backup.

    This non-HTTP operational entry point is intentionally not exported by the credits router.
    An operator must take and verify a database backup before passing ``backup_confirmed=True``.
    The provided ``expected_balance`` must equal the freshly calculated full ledger sum, so a
    stale investigation cannot alter an account. The operation is idempotent for an incident ID.
    """
    request_id = _repair_request_id(incident_id)
    normalized_note = _validate_repair_inputs(expected_balance, note, backup_confirmed)
    _validate_operator(operator)
    repaired_at = int(time())

    async with session.begin():
        account = await _locked_account(session, user_id)
        ledger_total = await _ledger_total(session, account.id)
        if not 0 <= ledger_total <= MAX_CREDIT_VALUE:
            raise CreditRepairError('ledger total is outside the supported non-negative credit balance range')
        if ledger_total != expected_balance:
            raise CreditRepairError('expected_balance does not match the current full ledger sum')

        existing = await _existing_evidence(session, account.id, request_id)
        if existing is not None:
            if account.balance != ledger_total:
                raise CreditRepairError('account changed after this incident was repaired; use a new incident id')
            return existing

        observed_account_balance = account.balance
        difference = observed_account_balance - ledger_total
        if difference:
            result = await session.execute(
                update(CreditAccount)
                .where(CreditAccount.id == account.id)
                .values(balance=ledger_total, updated_at=repaired_at)
            )
            if result.rowcount != 1:
                raise CreditRepairError('account could not be calibrated')

        evidence = await insert_ledger(
            session,
            {
                'id': str(uuid4()),
                'account_id': account.id,
                'user_id': account.user_id,
                'user_name_snapshot': account.user_name_snapshot,
                'user_email_snapshot': account.user_email_snapshot,
                'amount': 0,
                'balance_before': ledger_total,
                'balance_after': ledger_total,
                'entry_type': _REPAIR_ENTRY_TYPE,
                'reason_code': 'accounting_correction',
                'note': normalized_note,
                'operator_id': operator.id,
                'operator_name_snapshot': operator.name,
                'operator_email_snapshot': operator.email,
                'request_source': _REPAIR_SOURCE,
                'request_id': request_id,
                'metadata_snapshot': {
                    'incident_id': incident_id.strip(),
                    'observed_account_balance': observed_account_balance,
                    'difference': difference,
                    'operator': {'id': operator.id, 'name': operator.name, 'email': operator.email},
                    'reason': _REPAIR_REASON,
                    'repaired_at': repaired_at,
                },
                'created_at': repaired_at,
            },
        )

        verified_account_balance = await session.scalar(
            select(CreditAccount.balance).where(CreditAccount.id == account.id)
        )
        verified_ledger_total = await _ledger_total(session, account.id)
        if verified_account_balance != verified_ledger_total:
            raise CreditRepairError('post-repair verification failed; transaction was rolled back')
        if difference:
            credit_metrics.consistency_anomaly()
        return evidence


__all__ = ['CreditRepairError', 'repair_account_from_ledger']
