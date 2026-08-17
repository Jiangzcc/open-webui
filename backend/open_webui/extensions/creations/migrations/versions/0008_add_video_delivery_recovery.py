"""Persist FAL video provider and delivery recovery state.

Revision ID: 0008_add_video_delivery_recovery
Revises: 0007_add_video_creations_and_tasks
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0008_add_video_delivery_recovery'
down_revision: str | None = '0007_add_video_creations_and_tasks'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('creation_schema')


def upgrade() -> None:
    schema = _current_schema()
    with op.batch_alter_table('ext_video_generation_task', schema=schema) as batch:
        batch.add_column(sa.Column('execution_mode', sa.String(16), nullable=True))
        batch.add_column(sa.Column('provider_request_id', sa.String(128), nullable=True))
        batch.add_column(sa.Column('provider_status_url', sa.Text(), nullable=True))
        batch.add_column(sa.Column('provider_response_url', sa.Text(), nullable=True))
        batch.add_column(sa.Column('provider_result_url', sa.Text(), nullable=True))
        batch.add_column(sa.Column('delivery_attempts', sa.Integer(), nullable=False, server_default='0'))
        batch.create_check_constraint(
            'ck_ext_video_task_execution_mode',
            "execution_mode IS NULL OR execution_mode IN ('mock', 'fal')",
        )
        batch.create_check_constraint(
            'ck_ext_video_task_delivery_attempts',
            'delivery_attempts >= 0',
        )


def downgrade() -> None:
    schema = _current_schema()
    with op.batch_alter_table('ext_video_generation_task', schema=schema) as batch:
        batch.drop_constraint('ck_ext_video_task_delivery_attempts', type_='check')
        batch.drop_constraint('ck_ext_video_task_execution_mode', type_='check')
        batch.drop_column('delivery_attempts')
        batch.drop_column('provider_result_url')
        batch.drop_column('provider_response_url')
        batch.drop_column('provider_status_url')
        batch.drop_column('provider_request_id')
        batch.drop_column('execution_mode')
