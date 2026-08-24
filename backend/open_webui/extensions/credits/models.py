from __future__ import annotations

from open_webui.env import DATABASE_SCHEMA
from open_webui.internal.db import JSONField
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from .db import CreditBase


def _credit_table(name: str) -> str:
    return f'{DATABASE_SCHEMA}.{name}' if DATABASE_SCHEMA else name


class CreditAccount(CreditBase):
    __tablename__ = 'ext_credit_account'
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_ext_credit_account_user'),
        CheckConstraint('balance >= 0', name='ck_ext_credit_account_balance_nonnegative'),
    )

    id = Column(String(128), primary_key=True)
    user_id = Column(String(128), nullable=False)
    balance = Column(BigInteger, nullable=False, server_default='0')
    user_name_snapshot = Column(String(256), nullable=True)
    user_email_snapshot = Column(String(320), nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class CreditUsage(CreditBase):
    __tablename__ = 'ext_credit_usage'
    __table_args__ = (
        UniqueConstraint('user_id', 'idempotency_key', name='uq_ext_credit_usage_idempotency'),
        UniqueConstraint('ledger_id', name='uq_ext_credit_usage_ledger'),
        CheckConstraint(
            "status IN ('debited', 'invoking', 'succeeded', 'failed', 'unknown')",
            name='ck_ext_credit_usage_status',
        ),
        CheckConstraint("channel IN ('web', 'api', 'chat', 'tool')", name='ck_ext_credit_usage_channel'),
        CheckConstraint('charged_credits >= 0', name='ck_ext_credit_usage_charged_nonnegative'),
        CheckConstraint(
            'exempt IS FALSE OR (charged_credits = 0 AND ledger_id IS NULL)',
            name='ck_ext_credit_usage_exempt_consistency',
        ),
        Index('ix_ext_credit_usage_status_updated', 'status', 'updated_at'),
        Index('ix_ext_credit_usage_user_created', 'user_id', 'created_at'),
    )

    id = Column(String(128), primary_key=True)
    user_id = Column(String(128), nullable=False)
    user_name_snapshot = Column(String(256), nullable=True)
    user_email_snapshot = Column(String(320), nullable=True)
    idempotency_key = Column(String(128), nullable=False)
    request_hash = Column(String(128), nullable=False)
    service_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    action = Column(String(64), nullable=False)
    channel = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False)
    exempt = Column(Boolean, nullable=False, server_default='false')
    charged_credits = Column(BigInteger, nullable=False, server_default='0')
    ledger_id = Column(String(128), nullable=True)
    pricing_snapshot = Column(JSONField, nullable=True)
    request_snapshot = Column(JSONField, nullable=True)
    result_snapshot = Column(JSONField, nullable=True)
    error_snapshot = Column(JSONField, nullable=True)
    invocation_started_at = Column(BigInteger, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    completed_at = Column(BigInteger, nullable=True)


class CreditLedger(CreditBase):
    __tablename__ = 'ext_credit_ledger'
    __table_args__ = (
        ForeignKeyConstraint(
            ['account_id'],
            [_credit_table('ext_credit_account') + '.id'],
            ondelete='RESTRICT',
            name='fk_ext_credit_ledger_account',
        ),
        ForeignKeyConstraint(
            ['usage_id'],
            [_credit_table('ext_credit_usage') + '.id'],
            ondelete='RESTRICT',
            name='fk_ext_credit_ledger_usage',
        ),
        CheckConstraint('balance_after = balance_before + amount', name='ck_ext_credit_ledger_balance_equation'),
        CheckConstraint('balance_after >= 0', name='ck_ext_credit_ledger_balance_nonnegative'),
        CheckConstraint(
            "entry_type IN ('consumption', 'admin_adjustment', 'system_adjustment')",
            name='ck_ext_credit_ledger_entry_type',
        ),
        CheckConstraint(
            "request_source IN ('web', 'api', 'api_key', 'internal_admin')",
            name='ck_ext_credit_ledger_request_source',
        ),
        CheckConstraint(
            "reason_code IS NULL OR reason_code IN ('offline_recharge', 'promotion_gift', 'manual_refund', "
            "'accounting_correction', 'violation_deduction', 'other', 'redeem')",
            name='ck_ext_credit_ledger_reason_code',
        ),
        Index('ix_ext_credit_ledger_account', 'account_id'),
        Index('ix_ext_credit_ledger_user_created', 'user_id', 'created_at'),
        Index('ix_ext_credit_ledger_created', 'created_at'),
        Index('ix_ext_credit_ledger_usage', 'usage_id'),
        Index('ux_ext_credit_ledger_related_refund', 'related_ledger_id', unique=True),
    )

    id = Column(String(128), primary_key=True)
    account_id = Column(String(128), nullable=False)
    usage_id = Column(String(128), nullable=True)
    user_id = Column(String(128), nullable=False)
    user_name_snapshot = Column(String(256), nullable=True)
    user_email_snapshot = Column(String(320), nullable=True)
    amount = Column(BigInteger, nullable=False)
    balance_before = Column(BigInteger, nullable=False)
    balance_after = Column(BigInteger, nullable=False)
    entry_type = Column(String(32), nullable=False)
    reason_code = Column(String(64), nullable=True)
    note = Column(String(1000), nullable=True)
    operator_id = Column(String(128), nullable=True)
    operator_name_snapshot = Column(String(256), nullable=True)
    operator_email_snapshot = Column(String(320), nullable=True)
    request_source = Column(String(32), nullable=False)
    request_id = Column(String(128), nullable=False)
    idempotency_key = Column(String(128), nullable=True)
    service_type = Column(String(64), nullable=True)
    resource_id = Column(String(128), nullable=True)
    action = Column(String(64), nullable=True)
    pricing_snapshot = Column(JSONField, nullable=True)
    metadata_snapshot = Column(JSONField, nullable=True)
    related_ledger_id = Column(String(128), nullable=True)
    created_at = Column(BigInteger, nullable=False)


class CreditPrice(CreditBase):
    __tablename__ = 'ext_credit_price'
    __table_args__ = (
        UniqueConstraint('service_type', 'resource_id', 'action', name='uq_ext_credit_price_service'),
        CheckConstraint("base_price <> ''", name='ck_ext_credit_price_base_nonempty'),
        Index('ix_ext_credit_price_enabled_service_action', 'enabled', 'service_type', 'action'),
    )

    id = Column(String(128), primary_key=True)
    service_type = Column(String(64), nullable=False)
    resource_id = Column(String(128), nullable=False)
    action = Column(String(64), nullable=False)
    base_price = Column(String(32), nullable=False)
    rules = Column(JSONField, nullable=False)
    enabled = Column(Boolean, nullable=False, server_default='true')
    updated_by_id = Column(String(128), nullable=True)
    updated_by_name_snapshot = Column(String(256), nullable=True)
    updated_by_email_snapshot = Column(String(320), nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class CreditRedeemBatch(CreditBase):
    __tablename__ = 'ext_credit_redeem_batch'
    __table_args__ = (
        CheckConstraint('face_value > 0', name='ck_ext_credit_redeem_batch_face_value'),
        CheckConstraint('code_count > 0', name='ck_ext_credit_redeem_batch_code_count'),
        CheckConstraint(
            'per_user_limit IS NULL OR (per_user_limit > 0 AND per_user_limit <= code_count)',
            name='ck_ext_credit_redeem_batch_user_limit',
        ),
        CheckConstraint(
            'expires_at IS NULL OR expires_at > created_at',
            name='ck_ext_credit_redeem_batch_expiry',
        ),
        CheckConstraint(
            '(voided_at IS NULL AND voided_by_id IS NULL) OR '
            '(voided_at IS NOT NULL AND voided_by_id IS NOT NULL)',
            name='ck_ext_credit_redeem_batch_void_fields',
        ),
        Index('ix_ext_credit_redeem_batch_created', 'created_at'),
    )

    id = Column(String(128), primary_key=True)
    name = Column(String(128), nullable=False)
    face_value = Column(BigInteger, nullable=False)
    code_count = Column(Integer, nullable=False)
    expires_at = Column(BigInteger, nullable=True)
    per_user_limit = Column(Integer, nullable=True)
    created_by_id = Column(String(128), nullable=False)
    created_by_name_snapshot = Column(String(256), nullable=True)
    created_by_email_snapshot = Column(String(320), nullable=True)
    voided_at = Column(BigInteger, nullable=True)
    voided_by_id = Column(String(128), nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class CreditRedeemCode(CreditBase):
    __tablename__ = 'ext_credit_redeem_code'
    __table_args__ = (
        ForeignKeyConstraint(
            ['batch_id'],
            [_credit_table('ext_credit_redeem_batch') + '.id'],
            ondelete='RESTRICT',
            name='fk_ext_credit_redeem_code_batch',
        ),
        ForeignKeyConstraint(
            ['redeemed_ledger_id'],
            [_credit_table('ext_credit_ledger') + '.id'],
            ondelete='RESTRICT',
            name='fk_ext_credit_redeem_code_ledger',
        ),
        Index('ux_ext_credit_redeem_code_hash', 'code_hash', unique=True),
        Index('ux_ext_credit_redeem_code_ledger', 'redeemed_ledger_id', unique=True),
        CheckConstraint(
            'NOT (redeemed_at IS NOT NULL AND voided_at IS NOT NULL)',
            name='ck_ext_credit_redeem_code_terminal_state',
        ),
        CheckConstraint(
            '(redeemed_at IS NULL AND redeemed_by_user_id IS NULL AND redeemed_ledger_id IS NULL) OR '
            '(redeemed_at IS NOT NULL AND redeemed_by_user_id IS NOT NULL AND redeemed_ledger_id IS NOT NULL)',
            name='ck_ext_credit_redeem_code_redemption_fields',
        ),
        CheckConstraint(
            '(voided_at IS NULL AND voided_by_id IS NULL) OR '
            '(voided_at IS NOT NULL AND voided_by_id IS NOT NULL)',
            name='ck_ext_credit_redeem_code_void_fields',
        ),
        Index('ix_ext_credit_redeem_code_batch', 'batch_id'),
        Index('ix_ext_credit_redeem_code_batch_user', 'batch_id', 'redeemed_by_user_id'),
        Index('ix_ext_credit_redeem_code_batch_state', 'batch_id', 'redeemed_at', 'voided_at'),
    )

    id = Column(String(128), primary_key=True)
    batch_id = Column(String(128), nullable=False)
    code_hash = Column(String(64), nullable=False)
    code_hint = Column(String(16), nullable=False)
    redeemed_by_user_id = Column(String(128), nullable=True)
    redeemed_by_name_snapshot = Column(String(256), nullable=True)
    redeemed_by_email_snapshot = Column(String(320), nullable=True)
    redeemed_ledger_id = Column(String(128), nullable=True)
    redeemed_at = Column(BigInteger, nullable=True)
    voided_at = Column(BigInteger, nullable=True)
    voided_by_id = Column(String(128), nullable=True)
    created_at = Column(BigInteger, nullable=False)


class CreditRedeemAudit(CreditBase):
    __tablename__ = 'ext_credit_redeem_audit'
    __table_args__ = (
        ForeignKeyConstraint(
            ['batch_id'],
            [_credit_table('ext_credit_redeem_batch') + '.id'],
            ondelete='RESTRICT',
            name='fk_ext_credit_redeem_audit_batch',
        ),
        ForeignKeyConstraint(
            ['code_id'],
            [_credit_table('ext_credit_redeem_code') + '.id'],
            ondelete='RESTRICT',
            name='fk_ext_credit_redeem_audit_code',
        ),
        CheckConstraint(
            "action IN ('generate', 'redeem', 'void_batch', 'void_code')",
            name='ck_ext_credit_redeem_audit_action',
        ),
        CheckConstraint(
            "request_source IN ('web', 'api', 'api_key', 'internal_admin')",
            name='ck_ext_credit_redeem_audit_request_source',
        ),
        Index('ix_ext_credit_redeem_audit_batch_created', 'batch_id', 'created_at'),
    )

    id = Column(String(128), primary_key=True)
    batch_id = Column(String(128), nullable=False)
    code_id = Column(String(128), nullable=True)
    action = Column(String(32), nullable=False)
    actor_id = Column(String(128), nullable=False)
    actor_name_snapshot = Column(String(256), nullable=True)
    actor_email_snapshot = Column(String(320), nullable=True)
    request_source = Column(String(32), nullable=False)
    request_id = Column(String(128), nullable=False)
    remote_address_hash = Column(String(64), nullable=True)
    metadata_snapshot = Column(JSONField, nullable=True)
    created_at = Column(BigInteger, nullable=False)


__all__ = [
    'CreditAccount',
    'CreditLedger',
    'CreditPrice',
    'CreditRedeemAudit',
    'CreditRedeemBatch',
    'CreditRedeemCode',
    'CreditUsage',
]
