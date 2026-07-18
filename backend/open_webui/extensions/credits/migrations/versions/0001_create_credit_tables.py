"""Create independent credit extension tables.

Revision ID: 0001_create_credit_tables
Revises:
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
            "'accounting_correction', 'violation_deduction', 'other')",
            name='ck_ext_credit_ledger_reason_code',
        ),
        schema=schema,
    )
    op.create_index('ix_ext_credit_ledger_user_created', 'ext_credit_ledger', ['user_id', 'created_at'], schema=schema)
    op.create_index('ix_ext_credit_ledger_created', 'ext_credit_ledger', ['created_at'], schema=schema)
    op.create_index('ix_ext_credit_ledger_usage', 'ext_credit_ledger', ['usage_id'], schema=schema)
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


def downgrade() -> None:
    schema = _current_schema()
    op.drop_index('ix_ext_credit_price_enabled_service_action', table_name='ext_credit_price', schema=schema)
    op.drop_table('ext_credit_price', schema=schema)
    op.drop_index('ix_ext_credit_ledger_usage', table_name='ext_credit_ledger', schema=schema)
    op.drop_index('ix_ext_credit_ledger_created', table_name='ext_credit_ledger', schema=schema)
    op.drop_index('ix_ext_credit_ledger_user_created', table_name='ext_credit_ledger', schema=schema)
    op.drop_table('ext_credit_ledger', schema=schema)
    op.drop_index('ix_ext_credit_usage_user_created', table_name='ext_credit_usage', schema=schema)
    op.drop_index('ix_ext_credit_usage_status_updated', table_name='ext_credit_usage', schema=schema)
    op.drop_table('ext_credit_usage', schema=schema)
    op.drop_table('ext_credit_account', schema=schema)
