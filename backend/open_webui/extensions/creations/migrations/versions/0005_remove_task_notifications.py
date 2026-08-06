"""Remove task notification state.

Revision ID: 0005_remove_task_notifications
Revises: 0004_add_discovery_operations_and_task_notifications
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0005_remove_task_notifications'
down_revision: str | None = '0004_add_discovery_operations_and_task_notifications'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('creation_schema')


def upgrade() -> None:
    schema = _current_schema()
    with op.batch_alter_table('ext_image_generation_task', schema=schema) as batch:
        batch.drop_index('ix_ext_image_task_user_notification')
        batch.drop_column('notification_read_at')


def downgrade() -> None:
    schema = _current_schema()
    with op.batch_alter_table('ext_image_generation_task', schema=schema) as batch:
        batch.add_column(sa.Column('notification_read_at', sa.BigInteger(), nullable=True))
        batch.create_index(
            'ix_ext_image_task_user_notification',
            ['user_id', 'notification_read_at', 'completed_at', 'id'],
        )
