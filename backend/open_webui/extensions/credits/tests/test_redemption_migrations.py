from __future__ import annotations

import pytest
from open_webui.extensions.credits import registration
from open_webui.extensions.credits.models import CreditRedeemBatch, CreditRedeemCode
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from .test_migrations import _upgrade_sqlite

REDEMPTION_TABLES = {
    'ext_credit_redeem_batch',
    'ext_credit_redeem_code',
    'ext_credit_redeem_audit',
}


def test_redemption_migration_is_the_credit_head_and_registers_all_runtime_guards(sqlite_database) -> None:
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)
    inspector = inspect(engine)

    assert REDEMPTION_TABLES <= set(inspector.get_table_names())
    with engine.connect() as connection:
        assert connection.execute(text('SELECT version_num FROM ext_credit_schema_version')).scalar_one() == (
            '0001_create_credit_tables'
        )

    for table_name in REDEMPTION_TABLES:
        assert table_name in registration._REQUIRED_TABLES
    assert {
        'ck_ext_credit_redeem_batch_face_value',
        'ck_ext_credit_redeem_batch_code_count',
        'ck_ext_credit_redeem_batch_user_limit',
        'ck_ext_credit_redeem_batch_expiry',
        'ck_ext_credit_redeem_batch_void_fields',
    } <= registration._REQUIRED_CONSTRAINTS['ext_credit_redeem_batch']
    assert {
        'ck_ext_credit_redeem_code_terminal_state',
        'ck_ext_credit_redeem_code_redemption_fields',
        'ck_ext_credit_redeem_code_void_fields',
        'ck_ext_credit_redeem_code_code_nonempty',
    } <= registration._REQUIRED_CONSTRAINTS['ext_credit_redeem_code']
    assert {
        'ck_ext_credit_redeem_audit_action'
    } <= registration._REQUIRED_CONSTRAINTS['ext_credit_redeem_audit']
    assert 'ux_ext_credit_redeem_code_hash' in registration._REQUIRED_INDEXES['ext_credit_redeem_code']


def test_redemption_schema_enforces_hash_and_ledger_uniqueness(sqlite_database) -> None:
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)
    inspector = inspect(engine)

    unique_columns = {
        tuple(item['column_names'])
        for item in inspector.get_unique_constraints('ext_credit_redeem_code')
    }
    unique_columns.update(
        tuple(item['column_names'])
        for item in inspector.get_indexes('ext_credit_redeem_code')
        if item.get('unique')
    )

    assert ('code_hash',) in unique_columns
    assert ('redeemed_ledger_id',) in unique_columns

    code_columns = {column['name'] for column in inspector.get_columns('ext_credit_redeem_code')}
    assert 'code' in code_columns
    code_constraints = {
        constraint['name'] for constraint in inspector.get_check_constraints('ext_credit_redeem_code')
    }
    assert 'ck_ext_credit_redeem_code_code_nonempty' in code_constraints


def test_redemption_database_rejects_empty_plaintext_code(sqlite_database) -> None:
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)

    with engine.begin() as connection:
        connection.execute(
            CreditRedeemBatch.__table__.insert().values(
                id='batch-1',
                name='Batch',
                face_value=10,
                code_count=1,
                created_by_id='admin-1',
                created_at=1,
                updated_at=1,
            )
        )

    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                CreditRedeemCode.__table__.insert().values(
                    id='empty-code',
                    batch_id='batch-1',
                    code_hash='b' * 64,
                    code_hint='…BBBBBB',
                    code='',
                    created_at=1,
                )
            )


def test_redemption_database_rejects_invalid_batch_limits_and_terminal_states(sqlite_database) -> None:
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)

    valid_batch = {
        'id': 'batch-1',
        'name': 'Batch',
        'face_value': 10,
        'code_count': 1,
        'per_user_limit': 1,
        'created_by_id': 'admin-1',
        'created_at': 1,
        'updated_at': 1,
    }
    with engine.begin() as connection:
        connection.execute(CreditRedeemBatch.__table__.insert().values(**valid_batch))

    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                CreditRedeemBatch.__table__.insert().values(
                    **{
                        **valid_batch,
                        'id': 'invalid-batch',
                        'per_user_limit': 2,
                    }
                )
            )

    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                CreditRedeemCode.__table__.insert().values(
                    id='invalid-code',
                    batch_id='batch-1',
                    code_hash='a' * 64,
                    code_hint='…AAAAAA',
                    code='OWC-AAAAA',
                    redeemed_by_user_id='user-1',
                    redeemed_ledger_id='ledger-1',
                    redeemed_at=2,
                    voided_at=2,
                    created_at=1,
                )
            )

    with engine.connect() as connection:
        assert connection.execute(select(CreditRedeemBatch.id)).scalars().all() == ['batch-1']
        assert connection.execute(select(CreditRedeemCode.id)).scalars().all() == []
