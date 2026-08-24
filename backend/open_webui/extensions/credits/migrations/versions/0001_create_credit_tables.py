"""Create all credit-extension tables in one revision.

Revision ID: 0001_create_credit_tables
Revises:

开发阶段 squash（复盘 #13）：原 0001–0006 增量迁移合并为单一基线，净效果
与按序应用全部旧版本一致——

- 四张核心表（原 0001）+ 台账补偿守卫与账户索引（原 0002/0003）
- 台账 reason_code 校验直接含 ``redeem``（原 0006 终态）
- 三张卡密表（原 0004）；code 列为必填非空明文（原 0005 终态，
  不再保留 0005 的历史数据清理步骤）
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from open_webui.internal.db import JSONField

revision: str = '0001_create_credit_tables'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('credit_schema')


def _fk(name: str) -> str:
    schema = _current_schema()
    return f'{schema}.{name}.id' if schema else f'{name}.id'


def upgrade() -> None:
    schema = _current_schema()
    op.create_table(
        'ext_credit_account',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('balance', sa.BigInteger(), server_default=sa.text('0'), nullable=False),
        sa.Column('user_name_snapshot', sa.String(256), nullable=True),
        sa.Column('user_email_snapshot', sa.String(320), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_ext_credit_account_user'),
        sa.CheckConstraint('balance >= 0', name='ck_ext_credit_account_balance_nonnegative'),
        schema=schema,
    )
    op.create_table(
        'ext_credit_usage',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('user_name_snapshot', sa.String(256), nullable=True),
        sa.Column('user_email_snapshot', sa.String(320), nullable=True),
        sa.Column('idempotency_key', sa.String(128), nullable=False),
        sa.Column('request_hash', sa.String(128), nullable=False),
        sa.Column('service_type', sa.String(64), nullable=False),
        sa.Column('resource_id', sa.String(128), nullable=False),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('channel', sa.String(64), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('exempt', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('charged_credits', sa.BigInteger(), server_default=sa.text('0'), nullable=False),
        sa.Column('ledger_id', sa.String(128), nullable=True),
        sa.Column('pricing_snapshot', JSONField(), nullable=True),
        sa.Column('request_snapshot', JSONField(), nullable=True),
        sa.Column('result_snapshot', JSONField(), nullable=True),
        sa.Column('error_snapshot', JSONField(), nullable=True),
        sa.Column('invocation_started_at', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.Column('completed_at', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'idempotency_key', name='uq_ext_credit_usage_idempotency'),
        sa.UniqueConstraint('ledger_id', name='uq_ext_credit_usage_ledger'),
        sa.CheckConstraint(
            "status IN ('debited', 'invoking', 'succeeded', 'failed', 'unknown')",
            name='ck_ext_credit_usage_status',
        ),
        sa.CheckConstraint("channel IN ('web', 'api', 'chat', 'tool')", name='ck_ext_credit_usage_channel'),
        sa.CheckConstraint('charged_credits >= 0', name='ck_ext_credit_usage_charged_nonnegative'),
        sa.CheckConstraint(
            'exempt IS FALSE OR (charged_credits = 0 AND ledger_id IS NULL)',
            name='ck_ext_credit_usage_exempt_consistency',
        ),
        schema=schema,
    )
    op.create_index('ix_ext_credit_usage_status_updated', 'ext_credit_usage', ['status', 'updated_at'], schema=schema)
    op.create_index('ix_ext_credit_usage_user_created', 'ext_credit_usage', ['user_id', 'created_at'], schema=schema)
    op.create_table(
        'ext_credit_ledger',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('account_id', sa.String(128), nullable=False),
        sa.Column('usage_id', sa.String(128), nullable=True),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('user_name_snapshot', sa.String(256), nullable=True),
        sa.Column('user_email_snapshot', sa.String(320), nullable=True),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('balance_before', sa.BigInteger(), nullable=False),
        sa.Column('balance_after', sa.BigInteger(), nullable=False),
        sa.Column('entry_type', sa.String(32), nullable=False),
        sa.Column('reason_code', sa.String(64), nullable=True),
        sa.Column('note', sa.String(1000), nullable=True),
        sa.Column('operator_id', sa.String(128), nullable=True),
        sa.Column('operator_name_snapshot', sa.String(256), nullable=True),
        sa.Column('operator_email_snapshot', sa.String(320), nullable=True),
        sa.Column('request_source', sa.String(32), nullable=False),
        sa.Column('request_id', sa.String(128), nullable=False),
        sa.Column('idempotency_key', sa.String(128), nullable=True),
        sa.Column('service_type', sa.String(64), nullable=True),
        sa.Column('resource_id', sa.String(128), nullable=True),
        sa.Column('action', sa.String(64), nullable=True),
        sa.Column('pricing_snapshot', JSONField(), nullable=True),
        sa.Column('metadata_snapshot', JSONField(), nullable=True),
        sa.Column('related_ledger_id', sa.String(128), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['account_id'],
            [_fk('ext_credit_account')],
            ondelete='RESTRICT',
            name='fk_ext_credit_ledger_account',
        ),
        sa.ForeignKeyConstraint(
            ['usage_id'],
            [_fk('ext_credit_usage')],
            ondelete='RESTRICT',
            name='fk_ext_credit_ledger_usage',
        ),
        sa.CheckConstraint('balance_after = balance_before + amount', name='ck_ext_credit_ledger_balance_equation'),
        sa.CheckConstraint('balance_after >= 0', name='ck_ext_credit_ledger_balance_nonnegative'),
        sa.CheckConstraint(
            "entry_type IN ('consumption', 'admin_adjustment', 'system_adjustment')",
            name='ck_ext_credit_ledger_entry_type',
        ),
        sa.CheckConstraint(
            "request_source IN ('web', 'api', 'api_key', 'internal_admin')",
            name='ck_ext_credit_ledger_request_source',
        ),
        sa.CheckConstraint(
            "reason_code IS NULL OR reason_code IN ('offline_recharge', 'promotion_gift', 'manual_refund', "
            "'accounting_correction', 'violation_deduction', 'other', 'redeem')",
            name='ck_ext_credit_ledger_reason_code',
        ),
        schema=schema,
    )
    op.create_index('ix_ext_credit_ledger_user_created', 'ext_credit_ledger', ['user_id', 'created_at'], schema=schema)
    op.create_index('ix_ext_credit_ledger_created', 'ext_credit_ledger', ['created_at'], schema=schema)
    op.create_index('ix_ext_credit_ledger_usage', 'ext_credit_ledger', ['usage_id'], schema=schema)
    op.create_index('ix_ext_credit_ledger_account', 'ext_credit_ledger', ['account_id'], schema=schema)
    op.create_index(
        'ux_ext_credit_ledger_related_refund',
        'ext_credit_ledger',
        ['related_ledger_id'],
        unique=True,
        schema=schema,
    )
    op.create_table(
        'ext_credit_price',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('service_type', sa.String(64), nullable=False),
        sa.Column('resource_id', sa.String(128), nullable=False),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('base_price', sa.String(32), nullable=False),
        sa.Column('rules', JSONField(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('updated_by_id', sa.String(128), nullable=True),
        sa.Column('updated_by_name_snapshot', sa.String(256), nullable=True),
        sa.Column('updated_by_email_snapshot', sa.String(320), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('service_type', 'resource_id', 'action', name='uq_ext_credit_price_service'),
        sa.CheckConstraint("base_price <> ''", name='ck_ext_credit_price_base_nonempty'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_credit_price_enabled_service_action',
        'ext_credit_price',
        ['enabled', 'service_type', 'action'],
        schema=schema,
    )

    op.create_table(
        'ext_credit_redeem_batch',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('face_value', sa.BigInteger(), nullable=False),
        sa.Column('code_count', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.BigInteger(), nullable=True),
        sa.Column('per_user_limit', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.String(128), nullable=False),
        sa.Column('created_by_name_snapshot', sa.String(256), nullable=True),
        sa.Column('created_by_email_snapshot', sa.String(320), nullable=True),
        sa.Column('voided_at', sa.BigInteger(), nullable=True),
        sa.Column('voided_by_id', sa.String(128), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('face_value > 0', name='ck_ext_credit_redeem_batch_face_value'),
        sa.CheckConstraint('code_count > 0', name='ck_ext_credit_redeem_batch_code_count'),
        sa.CheckConstraint(
            'per_user_limit IS NULL OR (per_user_limit > 0 AND per_user_limit <= code_count)',
            name='ck_ext_credit_redeem_batch_user_limit',
        ),
        sa.CheckConstraint(
            'expires_at IS NULL OR expires_at > created_at',
            name='ck_ext_credit_redeem_batch_expiry',
        ),
        sa.CheckConstraint(
            '(voided_at IS NULL AND voided_by_id IS NULL) OR '
            '(voided_at IS NOT NULL AND voided_by_id IS NOT NULL)',
            name='ck_ext_credit_redeem_batch_void_fields',
        ),
        schema=schema,
    )
    op.create_index(
        'ix_ext_credit_redeem_batch_created',
        'ext_credit_redeem_batch',
        ['created_at'],
        schema=schema,
    )

    op.create_table(
        'ext_credit_redeem_code',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('batch_id', sa.String(128), nullable=False),
        sa.Column('code_hash', sa.String(64), nullable=False),
        sa.Column('code_hint', sa.String(16), nullable=False),
        sa.Column('redeemed_by_user_id', sa.String(128), nullable=True),
        sa.Column('redeemed_by_name_snapshot', sa.String(256), nullable=True),
        sa.Column('redeemed_by_email_snapshot', sa.String(320), nullable=True),
        sa.Column('redeemed_ledger_id', sa.String(128), nullable=True),
        sa.Column('redeemed_at', sa.BigInteger(), nullable=True),
        sa.Column('voided_at', sa.BigInteger(), nullable=True),
        sa.Column('voided_by_id', sa.String(128), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['batch_id'],
            [_fk('ext_credit_redeem_batch')],
            ondelete='RESTRICT',
            name='fk_ext_credit_redeem_code_batch',
        ),
        sa.ForeignKeyConstraint(
            ['redeemed_ledger_id'],
            [_fk('ext_credit_ledger')],
            ondelete='RESTRICT',
            name='fk_ext_credit_redeem_code_ledger',
        ),
        sa.CheckConstraint(
            'NOT (redeemed_at IS NOT NULL AND voided_at IS NOT NULL)',
            name='ck_ext_credit_redeem_code_terminal_state',
        ),
        sa.CheckConstraint(
            '(redeemed_at IS NULL AND redeemed_by_user_id IS NULL AND redeemed_ledger_id IS NULL) OR '
            '(redeemed_at IS NOT NULL AND redeemed_by_user_id IS NOT NULL AND redeemed_ledger_id IS NOT NULL)',
            name='ck_ext_credit_redeem_code_redemption_fields',
        ),
        sa.CheckConstraint(
            '(voided_at IS NULL AND voided_by_id IS NULL) OR '
            '(voided_at IS NOT NULL AND voided_by_id IS NOT NULL)',
            name='ck_ext_credit_redeem_code_void_fields',
        ),
        schema=schema,
    )
    op.create_index(
        'ux_ext_credit_redeem_code_hash',
        'ext_credit_redeem_code',
        ['code_hash'],
        unique=True,
        schema=schema,
    )
    op.create_index(
        'ux_ext_credit_redeem_code_ledger',
        'ext_credit_redeem_code',
        ['redeemed_ledger_id'],
        unique=True,
        schema=schema,
    )
    op.create_index('ix_ext_credit_redeem_code_batch', 'ext_credit_redeem_code', ['batch_id'], schema=schema)
    op.create_index(
        'ix_ext_credit_redeem_code_batch_user',
        'ext_credit_redeem_code',
        ['batch_id', 'redeemed_by_user_id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_credit_redeem_code_batch_state',
        'ext_credit_redeem_code',
        ['batch_id', 'redeemed_at', 'voided_at'],
        schema=schema,
    )

    op.create_table(
        'ext_credit_redeem_audit',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('batch_id', sa.String(128), nullable=False),
        sa.Column('code_id', sa.String(128), nullable=True),
        sa.Column('action', sa.String(32), nullable=False),
        sa.Column('actor_id', sa.String(128), nullable=False),
        sa.Column('actor_name_snapshot', sa.String(256), nullable=True),
        sa.Column('actor_email_snapshot', sa.String(320), nullable=True),
        sa.Column('request_source', sa.String(32), nullable=False),
        sa.Column('request_id', sa.String(128), nullable=False),
        sa.Column('remote_address_hash', sa.String(64), nullable=True),
        sa.Column('metadata_snapshot', JSONField(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['batch_id'],
            [_fk('ext_credit_redeem_batch')],
            ondelete='RESTRICT',
            name='fk_ext_credit_redeem_audit_batch',
        ),
        sa.ForeignKeyConstraint(
            ['code_id'],
            [_fk('ext_credit_redeem_code')],
            ondelete='RESTRICT',
            name='fk_ext_credit_redeem_audit_code',
        ),
        sa.CheckConstraint(
            "action IN ('generate', 'redeem', 'void_batch', 'void_code')",
            name='ck_ext_credit_redeem_audit_action',
        ),
        sa.CheckConstraint(
            "request_source IN ('web', 'api', 'api_key', 'internal_admin')",
            name='ck_ext_credit_redeem_audit_request_source',
        ),
        schema=schema,
    )
    op.create_index(
        'ix_ext_credit_redeem_audit_batch_created',
        'ext_credit_redeem_audit',
        ['batch_id', 'created_at'],
        schema=schema,
    )


def downgrade() -> None:
    schema = _current_schema()
    for index_name, table_name in (
        ('ix_ext_credit_redeem_audit_batch_created', 'ext_credit_redeem_audit'),
        ('ix_ext_credit_redeem_code_batch_state', 'ext_credit_redeem_code'),
        ('ix_ext_credit_redeem_code_batch_user', 'ext_credit_redeem_code'),
        ('ix_ext_credit_redeem_code_batch', 'ext_credit_redeem_code'),
        ('ux_ext_credit_redeem_code_ledger', 'ext_credit_redeem_code'),
        ('ux_ext_credit_redeem_code_hash', 'ext_credit_redeem_code'),
        ('ix_ext_credit_redeem_batch_created', 'ext_credit_redeem_batch'),
        ('ix_ext_credit_price_enabled_service_action', 'ext_credit_price'),
        ('ux_ext_credit_ledger_related_refund', 'ext_credit_ledger'),
        ('ix_ext_credit_ledger_account', 'ext_credit_ledger'),
        ('ix_ext_credit_ledger_usage', 'ext_credit_ledger'),
        ('ix_ext_credit_ledger_created', 'ext_credit_ledger'),
        ('ix_ext_credit_ledger_user_created', 'ext_credit_ledger'),
        ('ix_ext_credit_usage_user_created', 'ext_credit_usage'),
        ('ix_ext_credit_usage_status_updated', 'ext_credit_usage'),
    ):
        op.drop_index(index_name, table_name=table_name, schema=schema)
    for table_name in (
        'ext_credit_redeem_audit',
        'ext_credit_redeem_code',
        'ext_credit_redeem_batch',
        'ext_credit_price',
        'ext_credit_ledger',
        'ext_credit_usage',
        'ext_credit_account',
    ):
        op.drop_table(table_name, schema=schema)
