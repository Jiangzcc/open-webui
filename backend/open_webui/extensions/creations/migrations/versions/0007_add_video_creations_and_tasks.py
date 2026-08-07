"""Add video creations and asynchronous video generation tasks.

Revision ID: 0007_add_video_creations_and_tasks
Revises: 0006_create_discovery_categories
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0007_add_video_creations_and_tasks'
down_revision: str | None = '0006_create_discovery_categories'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('creation_schema')


def upgrade() -> None:
    schema = _current_schema()
    with op.batch_alter_table('ext_creation_media_item', schema=schema) as batch:
        batch.drop_constraint('ck_ext_creation_media_kind', type_='check')
        batch.drop_constraint('ck_ext_creation_media_task', type_='check')
        batch.add_column(sa.Column('poster_file_id', sa.String(128), nullable=True))
        batch.add_column(sa.Column('duration_seconds', sa.Integer(), nullable=True))
        batch.create_check_constraint('ck_ext_creation_media_kind', "kind IN ('image', 'video')")
        batch.create_check_constraint(
            'ck_ext_creation_media_task',
            "task IN ('text-to-image', 'image-to-image', 'text-to-video', 'image-to-video', 'video-to-video')",
        )
        batch.create_check_constraint(
            'ck_ext_creation_media_duration',
            "(kind = 'image' AND duration_seconds IS NULL) OR "
            "(kind = 'video' AND duration_seconds IS NOT NULL AND duration_seconds > 0)",
        )

    op.create_table(
        'ext_video_generation_task',
        sa.Column('id', sa.String(128), primary_key=True),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('idempotency_key', sa.String(128), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('task', sa.String(32), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('model_id', sa.String(256), nullable=False),
        sa.Column('params_json', sa.JSON(), nullable=True),
        sa.Column('assets_json', sa.JSON(), nullable=True),
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('error_code', sa.String(64), nullable=True),
        sa.Column('usage_id', sa.String(128), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('started_at', sa.BigInteger(), nullable=True),
        sa.Column('completed_at', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.UniqueConstraint('user_id', 'idempotency_key', name='uq_ext_video_task_user_key'),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name='ck_ext_video_task_status',
        ),
        sa.CheckConstraint(
            "task IN ('text-to-video', 'image-to-video', 'video-to-video')",
            name='ck_ext_video_task_kind',
        ),
        schema=schema,
    )
    op.create_index(
        'ix_ext_video_task_user_created',
        'ext_video_generation_task',
        ['user_id', 'created_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_video_task_status_updated',
        'ext_video_generation_task',
        ['status', 'updated_at', 'id'],
        schema=schema,
    )


def downgrade() -> None:
    schema = _current_schema()
    op.drop_index(
        'ix_ext_video_task_status_updated',
        table_name='ext_video_generation_task',
        schema=schema,
    )
    op.drop_index(
        'ix_ext_video_task_user_created',
        table_name='ext_video_generation_task',
        schema=schema,
    )
    op.drop_table('ext_video_generation_task', schema=schema)

    with op.batch_alter_table('ext_creation_media_item', schema=schema) as batch:
        batch.drop_constraint('ck_ext_creation_media_duration', type_='check')
        batch.drop_constraint('ck_ext_creation_media_task', type_='check')
        batch.drop_constraint('ck_ext_creation_media_kind', type_='check')
        batch.drop_column('duration_seconds')
        batch.drop_column('poster_file_id')
        batch.create_check_constraint('ck_ext_creation_media_kind', "kind IN ('image')")
        batch.create_check_constraint(
            'ck_ext_creation_media_task',
            "task IN ('text-to-image', 'image-to-image')",
        )
