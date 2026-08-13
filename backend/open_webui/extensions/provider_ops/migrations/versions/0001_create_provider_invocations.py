"""Create provider invocation observability table.

Revision ID: 0001_create_provider_invocations
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from open_webui.internal.db import JSONField

revision: str = '0001_create_provider_invocations'
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


def downgrade() -> None:
    schema = _current_schema()
    for name in (
        'ix_ext_provider_invocation_status_updated',
        'ix_ext_provider_invocation_model_created',
        'ix_ext_provider_invocation_provider_created',
        'ix_ext_provider_invocation_task',
    ):
        op.drop_index(name, table_name='ext_provider_invocation', schema=schema)
    op.drop_table('ext_provider_invocation', schema=schema)
