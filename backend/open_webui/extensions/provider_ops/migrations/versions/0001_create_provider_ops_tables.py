"""Create all provider-ops tables in one revision.

Revision ID: 0001_create_provider_ops_tables
Revises:

开发阶段 squash（复盘 #13）：原 0001–0004 增量迁移合并为单一基线，净效果
与按序应用全部旧版本一致——

- ext_provider_invocation：调用观测（原 0001）+ 实际成本列（原 0002）
- 平台同步四表（原 0002）
- ext_provider_sync_run：心跳列 + running 唯一部分索引（原 0004 终态；
  0004 针对存量重复 running 行的数据修复在新库上无意义，不保留）
- 计费事件与权威请求记录（原 0003）
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from open_webui.internal.db import JSONField

revision: str = '0001_create_provider_ops_tables'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('provider_ops_schema')


def upgrade() -> None:
    schema = _current_schema()
    op.create_table(
        'ext_provider_invocation',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('task_id', sa.String(128), nullable=True),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('media_kind', sa.String(16), nullable=False),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('provider_model_id', sa.String(256), nullable=False),
        sa.Column('attempt_no', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('provider_request_id', sa.String(128), nullable=True),
        sa.Column('provider_gateway_request_id', sa.String(128), nullable=True),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('queue_position', sa.Integer(), nullable=True),
        sa.Column('input_sha256', sa.String(64), nullable=False),
        sa.Column('provider_metrics_json', JSONField(), nullable=True),
        sa.Column('error_code', sa.String(64), nullable=True),
        sa.Column('error_snapshot_json', JSONField(), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('submitted_at', sa.BigInteger(), nullable=True),
        sa.Column('provider_started_at', sa.BigInteger(), nullable=True),
        sa.Column('provider_completed_at', sa.BigInteger(), nullable=True),
        sa.Column('completed_at', sa.BigInteger(), nullable=True),
        sa.Column('execution_duration_ms', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.Column('actual_cost_total', sa.String(64), nullable=True),
        sa.Column('actual_cost_currency', sa.String(3), nullable=True),
        sa.Column('cost_accuracy', sa.String(16), nullable=True),
        sa.Column('billing_event_at', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_request_id', name='uq_ext_provider_invocation_request'),
        sa.CheckConstraint("media_kind IN ('image', 'video')", name='ck_ext_provider_invocation_media_kind'),
        sa.CheckConstraint(
            "status IN ('created', 'submitted', 'queued', 'running', 'succeeded', 'failed', 'cancelled', 'unknown')",
            name='ck_ext_provider_invocation_status',
        ),
        sa.CheckConstraint('attempt_no >= 1', name='ck_ext_provider_invocation_attempt'),
        sa.CheckConstraint(
            'queue_position IS NULL OR queue_position >= 0',
            name='ck_ext_provider_invocation_queue_position',
        ),
        sa.CheckConstraint(
            'execution_duration_ms IS NULL OR execution_duration_ms >= 0',
            name='ck_ext_provider_invocation_execution_duration',
        ),
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_invocation_task',
        'ext_provider_invocation',
        ['task_id', 'created_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_invocation_provider_created',
        'ext_provider_invocation',
        ['provider', 'created_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_invocation_model_created',
        'ext_provider_invocation',
        ['provider_model_id', 'created_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_invocation_status_updated',
        'ext_provider_invocation',
        ['status', 'updated_at', 'id'],
        schema=schema,
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
        sa.Column('heartbeat_at', sa.BigInteger(), nullable=True),
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
    op.create_index(
        'ux_ext_provider_sync_run_running',
        'ext_provider_sync_run',
        ['provider'],
        unique=True,
        schema=schema,
        postgresql_where=sa.text("status = 'running'"),
        sqlite_where=sa.text("status = 'running'"),
    )

    op.create_table(
        'ext_provider_billing_event',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('provider_request_id', sa.String(128), nullable=False),
        sa.Column('provider_model_id', sa.String(256), nullable=False),
        sa.Column('event_timestamp', sa.String(64), nullable=False),
        sa.Column('event_at', sa.BigInteger(), nullable=False),
        sa.Column('api_key_id', sa.String(128), nullable=True),
        sa.Column('output_units', sa.String(64), nullable=True),
        sa.Column('unit_price', sa.String(64), nullable=True),
        sa.Column('percent_discount', sa.String(64), nullable=True),
        sa.Column('cost_subtotal', sa.String(64), nullable=False),
        sa.Column('cost_discount', sa.String(64), nullable=False),
        sa.Column('cost_total', sa.String(64), nullable=False),
        sa.Column('cost_nano_usd', sa.String(64), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('synced_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_request_id', name='uq_ext_provider_billing_event_request'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_billing_event_time',
        'ext_provider_billing_event',
        ['provider', 'event_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_billing_event_model_time',
        'ext_provider_billing_event',
        ['provider', 'provider_model_id', 'event_at', 'id'],
        schema=schema,
    )

    op.create_table(
        'ext_provider_request_record',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('provider_request_id', sa.String(128), nullable=False),
        sa.Column('provider_model_id', sa.String(256), nullable=False),
        sa.Column('sent_at', sa.BigInteger(), nullable=False),
        sa.Column('started_at', sa.BigInteger(), nullable=False),
        sa.Column('ended_at', sa.BigInteger(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.BigInteger(), nullable=True),
        sa.Column('synced_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_request_id', name='uq_ext_provider_request_record_request'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_request_record_ended',
        'ext_provider_request_record',
        ['provider', 'ended_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_request_record_model_ended',
        'ext_provider_request_record',
        ['provider', 'provider_model_id', 'ended_at', 'id'],
        schema=schema,
    )


def downgrade() -> None:
    schema = _current_schema()
    for index_name, table_name in (
        ('ix_ext_provider_request_record_model_ended', 'ext_provider_request_record'),
        ('ix_ext_provider_request_record_ended', 'ext_provider_request_record'),
        ('ix_ext_provider_billing_event_model_time', 'ext_provider_billing_event'),
        ('ix_ext_provider_billing_event_time', 'ext_provider_billing_event'),
        ('ux_ext_provider_sync_run_running', 'ext_provider_sync_run'),
        ('ix_ext_provider_sync_run_status_started', 'ext_provider_sync_run'),
        ('ix_ext_provider_sync_run_provider_started', 'ext_provider_sync_run'),
        ('ix_ext_provider_analytics_model_time', 'ext_provider_analytics_bucket'),
        ('ix_ext_provider_analytics_bucket_time', 'ext_provider_analytics_bucket'),
        ('ix_ext_provider_usage_model_time', 'ext_provider_usage_bucket'),
        ('ix_ext_provider_usage_bucket_time', 'ext_provider_usage_bucket'),
        ('ix_ext_provider_price_model_seen', 'ext_provider_price_snapshot'),
        ('ix_ext_provider_invocation_status_updated', 'ext_provider_invocation'),
        ('ix_ext_provider_invocation_model_created', 'ext_provider_invocation'),
        ('ix_ext_provider_invocation_provider_created', 'ext_provider_invocation'),
        ('ix_ext_provider_invocation_task', 'ext_provider_invocation'),
    ):
        op.drop_index(index_name, table_name=table_name, schema=schema)
    for table_name in (
        'ext_provider_request_record',
        'ext_provider_billing_event',
        'ext_provider_sync_run',
        'ext_provider_analytics_bucket',
        'ext_provider_usage_bucket',
        'ext_provider_price_snapshot',
        'ext_provider_invocation',
    ):
        op.drop_table(table_name, schema=schema)
