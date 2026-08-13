"""Add provider platform price, usage, analytics, and sync tables.

Revision ID: 0002_add_platform_sync_tables
Revises: 0001_create_provider_invocations
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from open_webui.internal.db import JSONField

revision: str = '0002_add_platform_sync_tables'
down_revision: str | None = '0001_create_provider_invocations'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('provider_ops_schema')


def upgrade() -> None:
    schema = _current_schema()
    op.add_column(
        'ext_provider_invocation', sa.Column('actual_cost_total', sa.String(64), nullable=True), schema=schema
    )
    op.add_column(
        'ext_provider_invocation', sa.Column('actual_cost_currency', sa.String(3), nullable=True), schema=schema
    )
    op.add_column('ext_provider_invocation', sa.Column('cost_accuracy', sa.String(16), nullable=True), schema=schema)
    op.add_column(
        'ext_provider_invocation', sa.Column('billing_event_at', sa.BigInteger(), nullable=True), schema=schema
    )
    op.create_table(
        'ext_provider_price_snapshot',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('provider_model_id', sa.String(256), nullable=False),
        sa.Column('unit_price', sa.String(64), nullable=False),
        sa.Column('unit', sa.String(64), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('first_seen_at', sa.BigInteger(), nullable=False),
        sa.Column('last_seen_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'provider',
            'provider_model_id',
            'unit',
            'currency',
            'unit_price',
            name='uq_ext_provider_price_value',
        ),
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_price_model_seen',
        'ext_provider_price_snapshot',
        ['provider', 'provider_model_id', 'last_seen_at', 'id'],
        schema=schema,
    )
    op.create_table(
        'ext_provider_usage_bucket',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('provider_model_id', sa.String(256), nullable=False),
        sa.Column('timeframe', sa.String(16), nullable=False),
        sa.Column('bucket_start', sa.String(64), nullable=False),
        sa.Column('bucket_start_at', sa.BigInteger(), nullable=False),
        sa.Column('api_key_id', sa.String(128), nullable=True),
        sa.Column('unit', sa.String(64), nullable=False),
        sa.Column('quantity', sa.String(64), nullable=False),
        sa.Column('unit_price', sa.String(64), nullable=False),
        sa.Column('percent_discount', sa.String(64), nullable=True),
        sa.Column('cost_subtotal', sa.String(64), nullable=False),
        sa.Column('cost_discount', sa.String(64), nullable=False),
        sa.Column('cost_total', sa.String(64), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('synced_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_usage_bucket_time',
        'ext_provider_usage_bucket',
        ['provider', 'bucket_start_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_usage_model_time',
        'ext_provider_usage_bucket',
        ['provider', 'provider_model_id', 'bucket_start_at', 'id'],
        schema=schema,
    )
    op.create_table(
        'ext_provider_analytics_bucket',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('provider_model_id', sa.String(256), nullable=False),
        sa.Column('timeframe', sa.String(16), nullable=False),
        sa.Column('bucket_start', sa.String(64), nullable=False),
        sa.Column('bucket_start_at', sa.BigInteger(), nullable=False),
        sa.Column('metrics_json', JSONField(), nullable=False),
        sa.Column('synced_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'provider',
            'provider_model_id',
            'timeframe',
            'bucket_start',
            name='uq_ext_provider_analytics_bucket',
        ),
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_analytics_bucket_time',
        'ext_provider_analytics_bucket',
        ['provider', 'bucket_start_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_analytics_model_time',
        'ext_provider_analytics_bucket',
        ['provider', 'provider_model_id', 'bucket_start_at', 'id'],
        schema=schema,
    )
    op.create_table(
        'ext_provider_sync_run',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('resources_json', JSONField(), nullable=False),
        sa.Column('counts_json', JSONField(), nullable=True),
        sa.Column('error_code', sa.String(64), nullable=True),
        sa.Column('window_start_at', sa.BigInteger(), nullable=False),
        sa.Column('window_end_at', sa.BigInteger(), nullable=False),
        sa.Column('started_at', sa.BigInteger(), nullable=False),
        sa.Column('completed_at', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('running', 'succeeded', 'failed')", name='ck_ext_provider_sync_run_status'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_sync_run_provider_started',
        'ext_provider_sync_run',
        ['provider', 'started_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_sync_run_status_started',
        'ext_provider_sync_run',
        ['status', 'started_at', 'id'],
        schema=schema,
    )


def downgrade() -> None:
    schema = _current_schema()
    for table_name, indexes in (
        (
            'ext_provider_sync_run',
            ('ix_ext_provider_sync_run_status_started', 'ix_ext_provider_sync_run_provider_started'),
        ),
        (
            'ext_provider_analytics_bucket',
            ('ix_ext_provider_analytics_model_time', 'ix_ext_provider_analytics_bucket_time'),
        ),
        (
            'ext_provider_usage_bucket',
            ('ix_ext_provider_usage_model_time', 'ix_ext_provider_usage_bucket_time'),
        ),
        ('ext_provider_price_snapshot', ('ix_ext_provider_price_model_seen',)),
    ):
        for index_name in indexes:
            op.drop_index(index_name, table_name=table_name, schema=schema)
        op.drop_table(table_name, schema=schema)
    for column_name in ('billing_event_at', 'cost_accuracy', 'actual_cost_currency', 'actual_cost_total'):
        op.drop_column('ext_provider_invocation', column_name, schema=schema)
