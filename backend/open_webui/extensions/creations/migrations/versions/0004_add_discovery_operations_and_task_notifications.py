"""Add discovery operations metadata and task notification state.

Revision ID: 0004_add_discovery_operations_and_task_notifications
Revises: 0003_create_image_generation_tasks
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0004_add_discovery_operations_and_task_notifications'
down_revision: str | None = '0003_create_image_generation_tasks'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('creation_schema')


def upgrade() -> None:
    schema = _current_schema()
    with op.batch_alter_table('ext_creation_post', schema=schema) as batch:
        batch.add_column(sa.Column('category', sa.String(32), server_default='other', nullable=False))
        batch.add_column(sa.Column('featured_at', sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column('featured_rank', sa.Integer(), server_default='1000', nullable=False))
        batch.create_check_constraint(
            'ck_ext_creation_post_category',
            "category IN ('portrait', 'product', 'poster', 'illustration', 'anime', 'landscape', 'other')",
        )
        batch.create_check_constraint('ck_ext_creation_post_featured_rank', 'featured_rank >= 0')
        batch.create_index(
            'ix_ext_creation_post_status_category',
            ['status', 'category', 'published_at', 'id'],
        )
        batch.create_index(
            'ix_ext_creation_post_status_featured',
            ['status', 'featured_rank', 'featured_at', 'id'],
        )

    with op.batch_alter_table('ext_image_generation_task', schema=schema) as batch:
        batch.add_column(sa.Column('notification_read_at', sa.BigInteger(), nullable=True))
        batch.create_index(
            'ix_ext_image_task_user_notification',
            ['user_id', 'notification_read_at', 'completed_at', 'id'],
        )

def downgrade() -> None:
    schema = _current_schema()
    with op.batch_alter_table('ext_image_generation_task', schema=schema) as batch:
        batch.drop_index('ix_ext_image_task_user_notification')
        batch.drop_column('notification_read_at')

    with op.batch_alter_table('ext_creation_post', schema=schema) as batch:
        batch.drop_index('ix_ext_creation_post_status_featured')
        batch.drop_index('ix_ext_creation_post_status_category')
        batch.drop_constraint('ck_ext_creation_post_featured_rank', type_='check')
        batch.drop_constraint('ck_ext_creation_post_category', type_='check')
        batch.drop_column('featured_rank')
        batch.drop_column('featured_at')
        batch.drop_column('category')
