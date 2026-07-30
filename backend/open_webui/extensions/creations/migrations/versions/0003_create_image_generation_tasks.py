"""Create persistent image generation task state.

Revision ID: 0003_create_image_generation_tasks
Revises: 0002_create_discovery_tables
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from open_webui.internal.db import JSONField

revision: str = '0003_create_image_generation_tasks'
down_revision: str | None = '0002_create_discovery_tables'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('creation_schema')


def upgrade() -> None:
    schema = _current_schema()
    op.create_table(
        'ext_image_generation_task',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('idempotency_key', sa.String(128), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('kind', sa.String(32), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('model_id', sa.String(256), nullable=True),
        sa.Column('params_json', JSONField(), nullable=True),
        sa.Column('expected_count', sa.Integer(), nullable=False),
        sa.Column('result_json', JSONField(), nullable=True),
        sa.Column('error_code', sa.String(64), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('started_at', sa.BigInteger(), nullable=True),
        sa.Column('completed_at', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'idempotency_key', name='uq_ext_image_task_user_key'),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name='ck_ext_image_task_status',
        ),
        sa.CheckConstraint(
            "kind IN ('text-to-image', 'image-to-image')",
            name='ck_ext_image_task_kind',
        ),
        sa.CheckConstraint('expected_count >= 1', name='ck_ext_image_task_expected_count'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_image_task_user_created',
        'ext_image_generation_task',
        ['user_id', 'created_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_image_task_status_updated',
        'ext_image_generation_task',
        ['status', 'updated_at', 'id'],
        schema=schema,
    )


def downgrade() -> None:
    schema = _current_schema()
    op.drop_index(
        'ix_ext_image_task_status_updated',
        table_name='ext_image_generation_task',
        schema=schema,
    )
    op.drop_index(
        'ix_ext_image_task_user_created',
        table_name='ext_image_generation_task',
        schema=schema,
    )
    op.drop_table('ext_image_generation_task', schema=schema)
