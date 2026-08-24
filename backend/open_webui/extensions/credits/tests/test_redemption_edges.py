from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from open_webui.extensions.credits import redemption
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.schemas import RedeemBatchCreate, UserSnapshot
from open_webui.extensions.tests.async_test_support import TransactionalSession as _Session

USER = UserSnapshot(id='user', name='User', email='user@example.test')
AUDIT = SimpleNamespace(source='web', request_id='request', remote_address_hash=None)


def test_code_canonicalization_and_unique_generation_edges(monkeypatch) -> None:
    assert redemption._canonical_code('') is None
    assert redemption._canonical_code('invalid!') is None
    assert redemption._canonical_code('OWC' + 'I' * 26) is None

    values = iter(
        [
            ('first', 'same', 'hint'),
            ('duplicate', 'same', 'hint'),
            ('second', 'other', 'hint'),
        ]
    )
    monkeypatch.setattr(redemption, '_new_code', lambda: next(values))
    assert redemption._generate_unique_codes(2) == [
        ('first', 'same', 'hint'),
        ('second', 'other', 'hint'),
    ]


@pytest.mark.asyncio
async def test_missing_user_and_expired_batch_creation_are_rejected(monkeypatch) -> None:
    session = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(one_or_none=lambda: None)
        )
    )
    with pytest.raises(CreditError, match='invalid'):
        await redemption._current_user(session, 'missing')

    monkeypatch.setattr(redemption, '_now', lambda: 10)
    form = RedeemBatchCreate(
        name='Expired',
        face_value=1,
        quantity=1,
        expires_at=10,
    )
    with pytest.raises(CreditError, match='adjustment'):
        await redemption.create_redeem_batch(object(), form, USER, AUDIT)


@pytest.mark.asyncio
async def test_redeem_admin_listing_rejects_missing_batches() -> None:
    session = SimpleNamespace(get=AsyncMock(return_value=None))
    with pytest.raises(CreditError, match='batch'):
        await redemption.list_redeem_codes(session, 'missing', skip=0, limit=10)
    with pytest.raises(CreditError, match='batch'):
        await redemption.list_redeem_audit(session, 'missing', skip=0, limit=10)


@pytest.mark.asyncio
async def test_void_batch_and_code_cover_missing_already_voided_and_conflict_paths() -> None:
    session = _Session(scalar=AsyncMock(return_value=None), execute=AsyncMock(), add=Mock())
    with pytest.raises(CreditError, match='batch'):
        await redemption.void_redeem_batch(session, 'missing', USER, AUDIT)
    with pytest.raises(CreditError, match='batch'):
        await redemption.void_redeem_code(session, 'missing', 'code', USER, AUDIT)

    session.scalar.return_value = SimpleNamespace(voided_at=1)
    assert await redemption.void_redeem_batch(session, 'batch', USER, AUDIT) == 0

    batch = SimpleNamespace(voided_at=None, updated_at=1)
    session.scalar.return_value = batch
    session.execute.return_value = SimpleNamespace(rowcount=0)
    assert await redemption.void_redeem_code(session, 'batch', 'code', USER, AUDIT) is False


@pytest.mark.asyncio
async def test_locked_entities_and_claim_reject_stale_rows() -> None:
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=None),
        execute=AsyncMock(),
        get=AsyncMock(),
        refresh=AsyncMock(),
    )
    with pytest.raises(CreditError, match='invalid'):
        await redemption._locked_redeem_entities(session, 'hash', now=1)

    code = SimpleNamespace(id='code', batch_id='batch')
    session.scalar = AsyncMock(side_effect=[code, None])
    with pytest.raises(CreditError, match='invalid'):
        await redemption._locked_redeem_entities(session, 'hash', now=1)

    session.execute.return_value = SimpleNamespace(rowcount=0)
    with pytest.raises(CreditError, match='used'):
        await redemption._claim_redeem_code(session, code, USER, 'ledger', 1)


@pytest.mark.asyncio
async def test_redeem_rejects_malformed_code_and_balance_overflow(monkeypatch) -> None:
    with pytest.raises(CreditError, match='invalid'):
        await redemption.redeem_code(object(), 'bad!', USER, AUDIT)

    batch = SimpleNamespace(face_value=2, id='batch')
    code = SimpleNamespace(id='code')
    session = _Session()
    monkeypatch.setattr(
        redemption,
        '_locked_redeem_entities',
        AsyncMock(return_value=(batch, code)),
    )
    monkeypatch.setattr(redemption, '_current_user', AsyncMock(return_value=USER))
    monkeypatch.setattr(redemption, '_enforce_per_user_limit', AsyncMock())
    account = SimpleNamespace(id='account')
    monkeypatch.setattr(redemption, 'get_or_create_account', AsyncMock(return_value=account))
    monkeypatch.setattr(
        redemption,
        '_lock_and_verify_account_matches_ledger',
        AsyncMock(return_value=account),
    )
    monkeypatch.setattr(redemption, 'update_account_balance', AsyncMock(return_value=None))
    valid = redemption._new_code()[0]
    with pytest.raises(CreditError, match='adjustment'):
        await redemption.redeem_code(session, valid, USER, AUDIT)
