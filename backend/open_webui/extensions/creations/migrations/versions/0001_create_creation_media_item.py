"""Create the independent creation media item table.

Revision ID: 0001_create_creation_media_item
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from open_webui.internal.db import JSONField

revision: str = '0001_create_creation_media_item'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('creation_schema')


def upgrade() -> None:
    schema = _current_schema()
    op.create_table(
        'ext_creation_media_item',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('kind', sa.String(16), nullable=False),
        sa.Column('file_id', sa.String(128), nullable=False),
        sa.Column('caption', sa.String(1000), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('negative_prompt', sa.Text(), nullable=True),
        sa.Column('model_id', sa.String(256), nullable=True),
        sa.Column('model_name_snapshot', sa.String(256), nullable=True),
        sa.Column('task', sa.String(32), nullable=False),
        sa.Column('params_json', JSONField(), nullable=True),
        sa.Column('reference_file_ids_json', JSONField(), nullable=True),
        sa.Column('source', sa.String(16), nullable=False),
        sa.Column('batch_id', sa.String(128), nullable=False),
        sa.Column('soft_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_id', name='uq_ext_creation_media_file'),
        sa.CheckConstraint("kind IN ('image')", name='ck_ext_creation_media_kind'),
        sa.CheckConstraint(
            "task IN ('text-to-image', 'image-to-image')",
            name='ck_ext_creation_media_task',
        ),
        sa.CheckConstraint(
            "source IN ('web', 'api', 'chat', 'tool')",
            name='ck_ext_creation_media_source',
        ),
        schema=schema,
    )
    op.create_index(
        'ix_ext_creation_media_user_visible_created',
        'ext_creation_media_item',
        ['user_id', 'soft_deleted', 'created_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_creation_media_visible_created',
        'ext_creation_media_item',
        ['soft_deleted', 'created_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_creation_media_batch',
        'ext_creation_media_item',
        ['batch_id'],
        schema=schema,
    )


def downgrade() -> None:
    schema = _current_schema()
    op.drop_index('ix_ext_creation_media_batch', table_name='ext_creation_media_item', schema=schema)
    op.drop_index(
        'ix_ext_creation_media_visible_created',
        table_name='ext_creation_media_item',
        schema=schema,
    )
    op.drop_index(
        'ix_ext_creation_media_user_visible_created',
        table_name='ext_creation_media_item',
        schema=schema,
    )
    op.drop_table('ext_creation_media_item', schema=schema)
