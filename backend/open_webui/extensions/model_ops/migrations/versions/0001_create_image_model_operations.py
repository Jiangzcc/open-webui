"""Create image model operations overlay.

Revision ID: 0001_create_image_model_operations
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from open_webui.internal.db import JSONField

revision: str = '0001_create_image_model_operations'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('model_ops_schema')


def upgrade() -> None:
    schema = _current_schema()
    op.create_table(
        'ext_image_model_operation',
        sa.Column('model_id', sa.String(256), nullable=False),
        sa.Column('visible', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('recommended', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default=sa.text('1000'), nullable=False),
        sa.Column('tags_json', JSONField(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('maintenance_message', sa.String(500), nullable=True),
        sa.Column('updated_by_id', sa.String(128), nullable=True),
        sa.Column('updated_by_name_snapshot', sa.String(256), nullable=True),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('model_id'),
        sa.CheckConstraint('sort_order >= 0', name='ck_ext_image_model_operation_sort_order'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_image_model_operation_visibility',
        'ext_image_model_operation',
        ['visible', 'enabled', 'sort_order', 'model_id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_image_model_operation_recommended',
        'ext_image_model_operation',
        ['recommended', 'sort_order', 'model_id'],
        schema=schema,
    )


def downgrade() -> None:
    schema = _current_schema()
    op.drop_index(
        'ix_ext_image_model_operation_recommended',
        table_name='ext_image_model_operation',
        schema=schema,
    )
    op.drop_index(
        'ix_ext_image_model_operation_visibility',
        table_name='ext_image_model_operation',
        schema=schema,
    )
    op.drop_table('ext_image_model_operation', schema=schema)
