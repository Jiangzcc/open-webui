from __future__ import annotations

import hashlib
import hmac
import secrets
import string
from uuid import uuid4

from open_webui.env import WEBUI_SECRET_KEY
from open_webui.models.users import User
from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .errors import CreditError
from .models import (
    CreditRedeemAudit,
    CreditRedeemBatch,
    CreditRedeemCode,
)
from .repository import get_or_create_account, insert_ledger, update_account_balance
from .schemas import (
    RedeemAuditItem,
    RedeemAuditPage,
    RedeemBatchCreate,
    RedeemBatchCreated,
    RedeemBatchItem,
    RedeemBatchPage,
    RedeemCodeAdminItem,
    RedeemCodeAdminPage,
    RedeemCodeResult,
    RequestAuditContext,
    UserSnapshot,
)
from .service import _lock_and_verify_account_matches_ledger, _now

_CODE_PREFIX = 'OWC'
_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
_CODE_RANDOM_LENGTH = 26


def _canonical_code(value: str) -> str | None:
    if not value or any(char not in string.ascii_letters + string.digits + ' -' for char in value):
        return None
    compact = value.upper().replace('-', '').replace(' ', '')
    if len(compact) != len(_CODE_PREFIX) + _CODE_RANDOM_LENGTH or not compact.startswith(_CODE_PREFIX):
        return None
    random_part = compact[len(_CODE_PREFIX) :]
    if any(char not in _CODE_ALPHABET for char in random_part):
        return None
    return compact


def _hash_code(canonical: str) -> str:
    return hmac.new(
        WEBUI_SECRET_KEY.encode(),
        b'credit-redeem:v1\0' + canonical.encode('ascii'),
        hashlib.sha256,
    ).hexdigest()


def _new_code() -> tuple[str, str, str]:
    random_part = ''.join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_RANDOM_LENGTH))
    canonical = f'{_CODE_PREFIX}{random_part}'
    groups = [random_part[index : index + 5] for index in range(0, 20, 5)]
    groups.append(random_part[20:])
    display = '-'.join((_CODE_PREFIX, *groups))
    return display, _hash_code(canonical), f'…{random_part[-6:]}'


async def _current_user(session: AsyncSession, user_id: str) -> UserSnapshot:
    row = (await session.execute(select(User.id, User.name, User.email).where(User.id == user_id))).one_or_none()
    if row is None:
        raise CreditError(code='redeem_code_invalid')
    return UserSnapshot(id=row.id, name=row.name, email=row.email)


def _audit_row(
    *,
    batch_id: str,
    code_id: str | None,
    action: str,
    actor: UserSnapshot,
    audit: RequestAuditContext,
    metadata: dict[str, object] | None,
    created_at: int,
) -> CreditRedeemAudit:
    return CreditRedeemAudit(
        id=str(uuid4()),
        batch_id=batch_id,
        code_id=code_id,
        action=action,
        actor_id=actor.id,
        actor_name_snapshot=actor.name,
        actor_email_snapshot=actor.email,
        request_source=audit.source,
        request_id=audit.request_id,
        remote_address_hash=audit.remote_address_hash,
        metadata_snapshot=metadata,
        created_at=created_at,
    )


def _batch_item(
    batch: CreditRedeemBatch,
    *,
    redeemed_count: int,
    voided_count: int,
    now: int,
) -> RedeemBatchItem:
    unused_count = max(0, batch.code_count - redeemed_count - voided_count)
    unavailable = batch.voided_at is not None or (batch.expires_at is not None and batch.expires_at <= now)
    return RedeemBatchItem(
        id=batch.id,
        name=batch.name,
        face_value=batch.face_value,
        code_count=batch.code_count,
        redeemed_count=redeemed_count,
        voided_count=voided_count,
        unused_count=unused_count,
        available_count=0 if unavailable else unused_count,
        expires_at=batch.expires_at,
        per_user_limit=batch.per_user_limit,
        voided_at=batch.voided_at,
        created_by_id=batch.created_by_id,
        created_by_name_snapshot=batch.created_by_name_snapshot,
        created_at=batch.created_at,
    )


def _ensure_redeemable(
    batch: CreditRedeemBatch,
    code: CreditRedeemCode,
    *,
    now: int,
) -> None:
    if code.redeemed_at is not None:
        raise CreditError(code='redeem_code_used')
    if code.voided_at is not None or batch.voided_at is not None:
        raise CreditError(code='redeem_code_voided')
    if batch.expires_at is not None and batch.expires_at <= now:
        raise CreditError(code='redeem_code_expired')


async def _enforce_per_user_limit(
    session: AsyncSession,
    batch: CreditRedeemBatch,
    user_id: str,
) -> None:
    if batch.per_user_limit is None:
        return
    redeemed_count = int(
        await session.scalar(
            select(func.count(CreditRedeemCode.id)).where(
                CreditRedeemCode.batch_id == batch.id,
                CreditRedeemCode.redeemed_by_user_id == user_id,
                CreditRedeemCode.redeemed_at.is_not(None),
            )
        )
        or 0
    )
    if redeemed_count >= batch.per_user_limit:
        raise CreditError(code='redeem_code_limit_reached')


def _generate_unique_codes(quantity: int) -> list[tuple[str, str, str]]:
    generated: list[tuple[str, str, str]] = []
    hashes: set[str] = set()
    while len(generated) < quantity:
        candidate = _new_code()
        if candidate[1] not in hashes:
            hashes.add(candidate[1])
            generated.append(candidate)
    return generated


def _new_redeem_batch(
    form: RedeemBatchCreate,
    operator: UserSnapshot,
    *,
    batch_id: str,
    created_at: int,
) -> CreditRedeemBatch:
    return CreditRedeemBatch(
        id=batch_id,
        name=form.name,
        face_value=form.face_value,
        code_count=form.quantity,
        expires_at=form.expires_at,
        per_user_limit=form.per_user_limit,
        created_by_id=operator.id,
        created_by_name_snapshot=operator.name,
        created_by_email_snapshot=operator.email,
        created_at=created_at,
        updated_at=created_at,
    )


async def create_redeem_batch(
    session: AsyncSession,
    form: RedeemBatchCreate,
    operator: UserSnapshot,
    audit: RequestAuditContext,
) -> RedeemBatchCreated:
    created_at = _now()
    if form.expires_at is not None and form.expires_at <= created_at:
        raise CreditError(code='invalid_adjustment', context={'reason': 'redeem_expiry_not_future'})

    generated = _generate_unique_codes(form.quantity)
    batch_id = str(uuid4())
    batch = _new_redeem_batch(form, operator, batch_id=batch_id, created_at=created_at)
    async with session.begin():
        session.add(batch)
        session.add_all(
            [
                CreditRedeemCode(
                    id=str(uuid4()),
                    batch_id=batch_id,
                    code_hash=code_hash,
                    code_hint=hint,
                    created_at=created_at,
                )
                for display, code_hash, hint in generated
            ]
        )
        session.add(
            _audit_row(
                batch_id=batch_id,
                code_id=None,
                action='generate',
                actor=operator,
                audit=audit,
                metadata={'quantity': form.quantity, 'face_value': form.face_value},
                created_at=created_at,
            )
        )
    item = _batch_item(batch, redeemed_count=0, voided_count=0, now=created_at)
    return RedeemBatchCreated(**item.model_dump(), codes=tuple(display for display, _hash, _hint in generated))


async def list_redeem_batches(session: AsyncSession, *, skip: int, limit: int) -> RedeemBatchPage:
    total = int(await session.scalar(select(func.count(CreditRedeemBatch.id))) or 0)
    page_batches = (
        (
            await session.execute(
                select(CreditRedeemBatch)
                .order_by(CreditRedeemBatch.created_at.desc(), CreditRedeemBatch.id.desc())
                .offset(skip)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    # 统计只聚合当前页批次：全表 GROUP BY 会随卡密总量线性变慢（审查发现 #15）。
    stats: dict[str, tuple[int, int]] = {}
    if page_batches:
        batch_ids = [batch.id for batch in page_batches]
        stats = {
            batch_id: (int(redeemed), int(voided))
            for batch_id, redeemed, voided in (
                await session.execute(
                    select(
                        CreditRedeemCode.batch_id,
                        func.coalesce(func.sum(case((CreditRedeemCode.redeemed_at.is_not(None), 1), else_=0)), 0),
                        func.coalesce(func.sum(case((CreditRedeemCode.voided_at.is_not(None), 1), else_=0)), 0),
                    )
                    .where(CreditRedeemCode.batch_id.in_(batch_ids))
                    .group_by(CreditRedeemCode.batch_id)
                )
            ).all()
        }
    now = _now()
    return RedeemBatchPage(
        items=tuple(
            _batch_item(
                batch,
                redeemed_count=stats.get(batch.id, (0, 0))[0],
                voided_count=stats.get(batch.id, (0, 0))[1],
                now=now,
            )
            for batch in page_batches
        ),
        total=total,
    )


def _admin_code_item(row: CreditRedeemCode, batch: CreditRedeemBatch, *, expired: bool) -> RedeemCodeAdminItem:
    status = (
        'redeemed'
        if row.redeemed_at is not None
        else 'voided'
        if row.voided_at is not None or batch.voided_at is not None
        else 'expired'
        if expired
        else 'available'
    )
    return RedeemCodeAdminItem(
        id=row.id,
        hint=row.code_hint,
        status=status,
        redeemed_by_user_id=row.redeemed_by_user_id,
        redeemed_by_name_snapshot=row.redeemed_by_name_snapshot,
        redeemed_at=row.redeemed_at,
        voided_at=row.voided_at,
    )


async def list_redeem_codes(
    session: AsyncSession,
    batch_id: str,
    *,
    skip: int,
    limit: int,
) -> RedeemCodeAdminPage:
    batch = await session.get(CreditRedeemBatch, batch_id)
    if batch is None:
        raise CreditError(code='redeem_batch_not_found')
    rows = (
        (
            await session.execute(
                select(CreditRedeemCode)
                .where(CreditRedeemCode.batch_id == batch_id)
                .order_by(CreditRedeemCode.created_at, CreditRedeemCode.id)
                .offset(skip)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    total = int(
        await session.scalar(select(func.count(CreditRedeemCode.id)).where(CreditRedeemCode.batch_id == batch_id)) or 0
    )
    expired = batch.expires_at is not None and batch.expires_at <= _now()
    items = [_admin_code_item(row, batch, expired=expired) for row in rows]
    return RedeemCodeAdminPage(items=tuple(items), total=total)


async def list_redeem_audit(
    session: AsyncSession,
    batch_id: str,
    *,
    skip: int,
    limit: int,
) -> RedeemAuditPage:
    if await session.get(CreditRedeemBatch, batch_id) is None:
        raise CreditError(code='redeem_batch_not_found')
    rows = (
        (
            await session.execute(
                select(CreditRedeemAudit)
                .where(CreditRedeemAudit.batch_id == batch_id)
                .order_by(CreditRedeemAudit.created_at.desc(), CreditRedeemAudit.id.desc())
                .offset(skip)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    total = int(
        await session.scalar(select(func.count(CreditRedeemAudit.id)).where(CreditRedeemAudit.batch_id == batch_id))
        or 0
    )
    return RedeemAuditPage(
        items=tuple(
            RedeemAuditItem(
                id=row.id,
                action=row.action,
                code_id=row.code_id,
                actor_id=row.actor_id,
                actor_name_snapshot=row.actor_name_snapshot,
                request_source=row.request_source,
                request_id=row.request_id,
                metadata=row.metadata_snapshot if isinstance(row.metadata_snapshot, dict) else None,
                created_at=row.created_at,
            )
            for row in rows
        ),
        total=total,
    )


async def void_redeem_batch(
    session: AsyncSession,
    batch_id: str,
    operator: UserSnapshot,
    audit: RequestAuditContext,
) -> int:
    now = _now()
    async with session.begin():
        batch = await session.scalar(
            select(CreditRedeemBatch).where(CreditRedeemBatch.id == batch_id).with_for_update()
        )
        if batch is None:
            raise CreditError(code='redeem_batch_not_found')
        if batch.voided_at is not None:
            return 0
        result = await session.execute(
            update(CreditRedeemCode)
            .where(
                CreditRedeemCode.batch_id == batch_id,
                CreditRedeemCode.redeemed_at.is_(None),
                CreditRedeemCode.voided_at.is_(None),
            )
            .values(voided_at=now, voided_by_id=operator.id)
        )
        batch.voided_at = now
        batch.voided_by_id = operator.id
        batch.updated_at = now
        session.add(
            _audit_row(
                batch_id=batch_id,
                code_id=None,
                action='void_batch',
                actor=operator,
                audit=audit,
                metadata={'voided_count': int(result.rowcount or 0)},
                created_at=now,
            )
        )
    return int(result.rowcount or 0)


async def void_redeem_code(
    session: AsyncSession,
    batch_id: str,
    code_id: str,
    operator: UserSnapshot,
    audit: RequestAuditContext,
) -> bool:
    now = _now()
    async with session.begin():
        batch = await session.scalar(
            select(CreditRedeemBatch).where(CreditRedeemBatch.id == batch_id).with_for_update()
        )
        if batch is None:
            raise CreditError(code='redeem_batch_not_found')
        result = await session.execute(
            update(CreditRedeemCode)
            .where(
                CreditRedeemCode.id == code_id,
                CreditRedeemCode.batch_id == batch_id,
                CreditRedeemCode.redeemed_at.is_(None),
                CreditRedeemCode.voided_at.is_(None),
            )
            .values(voided_at=now, voided_by_id=operator.id)
        )
        if result.rowcount != 1:
            return False
        batch.updated_at = now
        session.add(
            _audit_row(
                batch_id=batch_id,
                code_id=code_id,
                action='void_code',
                actor=operator,
                audit=audit,
                metadata=None,
                created_at=now,
            )
        )
    return True


async def _locked_redeem_entities(
    session: AsyncSession,
    code_hash: str,
    *,
    now: int,
) -> tuple[CreditRedeemBatch, CreditRedeemCode]:
    """Serialize code claims through a real batch-row update across SQLite/Postgres."""
    code = await session.scalar(select(CreditRedeemCode).where(CreditRedeemCode.code_hash == code_hash))
    if code is None:
        raise CreditError(code='redeem_code_invalid')
    await session.execute(update(CreditRedeemBatch).where(CreditRedeemBatch.id == code.batch_id).values(updated_at=now))
    batch = await session.scalar(select(CreditRedeemBatch).where(CreditRedeemBatch.id == code.batch_id))
    fresh_code = await session.get(CreditRedeemCode, code.id)
    if batch is None or fresh_code is None:
        raise CreditError(code='redeem_code_invalid')
    await session.refresh(fresh_code)
    _ensure_redeemable(batch, fresh_code, now=now)
    return batch, fresh_code


def _redemption_ledger_values(
    batch: CreditRedeemBatch,
    code: CreditRedeemCode,
    user: UserSnapshot,
    audit: RequestAuditContext,
    account_id: str,
    balance: tuple[int, int],
    now: int,
) -> dict[str, object]:
    remote = {'remote_address_hash': audit.remote_address_hash} if audit.remote_address_hash is not None else {}
    return {
        'id': str(uuid4()),
        'account_id': account_id,
        'user_id': user.id,
        'user_name_snapshot': user.name,
        'user_email_snapshot': user.email,
        'amount': batch.face_value,
        'balance_before': balance[0],
        'balance_after': balance[1],
        'entry_type': 'system_adjustment',
        'reason_code': 'redeem',
        'note': f'Redeem-code batch: {batch.name}',
        'request_source': audit.source,
        'request_id': audit.request_id,
        'idempotency_key': f'redemption:{code.id}',
        'service_type': 'credits',
        'resource_id': batch.id,
        'action': 'redeem',
        'metadata_snapshot': {'batch_id': batch.id, 'code_id': code.id, **remote},
        'created_at': now,
    }


async def _claim_redeem_code(
    session: AsyncSession,
    code: CreditRedeemCode,
    user: UserSnapshot,
    ledger_id: str,
    now: int,
) -> None:
    claimed = await session.execute(
        update(CreditRedeemCode)
        .where(
            CreditRedeemCode.id == code.id,
            CreditRedeemCode.redeemed_at.is_(None),
            CreditRedeemCode.voided_at.is_(None),
        )
        .values(
            redeemed_by_user_id=user.id,
            redeemed_by_name_snapshot=user.name,
            redeemed_by_email_snapshot=user.email,
            redeemed_ledger_id=ledger_id,
            redeemed_at=now,
        )
    )
    if claimed.rowcount != 1:
        raise CreditError(code='redeem_code_used')


async def redeem_code(
    session: AsyncSession,
    raw_code: str,
    user: UserSnapshot,
    audit: RequestAuditContext,
) -> RedeemCodeResult:
    canonical = _canonical_code(raw_code)
    if canonical is None:
        raise CreditError(code='redeem_code_invalid')
    code_hash = _hash_code(canonical)
    now = _now()

    async with session.begin():
        batch, code = await _locked_redeem_entities(session, code_hash, now=now)
        current_user = await _current_user(session, user.id)
        await _enforce_per_user_limit(session, batch, current_user.id)
        account = await get_or_create_account(session, current_user, now=now)
        account = await _lock_and_verify_account_matches_ledger(session, account.id)
        balance = await update_account_balance(session, account, batch.face_value, now=now)
        if balance is None:
            raise CreditError(code='invalid_adjustment', context={'reason': 'balance_limit_exceeded'})
        ledger = await insert_ledger(
            session,
            _redemption_ledger_values(batch, code, current_user, audit, account.id, balance, now),
        )
        await _claim_redeem_code(session, code, current_user, ledger.id, now)
        session.add(
            _audit_row(
                batch_id=batch.id,
                code_id=code.id,
                action='redeem',
                actor=current_user,
                audit=audit,
                metadata={'ledger_id': ledger.id, 'credited': batch.face_value},
                created_at=now,
            )
        )
    return RedeemCodeResult(
        ledger_id=ledger.id,
        credited=batch.face_value,
        balance=balance[1],
        redeemed_at=now,
    )


__all__ = [
    'create_redeem_batch',
    'list_redeem_audit',
    'list_redeem_batches',
    'list_redeem_codes',
    'redeem_code',
    'void_redeem_batch',
    'void_redeem_code',
]
