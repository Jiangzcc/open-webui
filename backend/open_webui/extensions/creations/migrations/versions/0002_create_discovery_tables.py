"""Create discovery posts, media links, and reactions.

Revision ID: 0002_create_discovery_tables
Revises: 0001_create_creation_media_item
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0002_create_discovery_tables'
down_revision: str | None = '0001_create_creation_media_item'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('creation_schema')


def upgrade() -> None:
    schema = _current_schema()
    op.create_table(
        'ext_creation_post',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('show_prompt', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('like_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('favorite_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('published_at', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status IN ('published', 'withdrawn', 'hidden')",
            name='ck_ext_creation_post_status',
        ),
        sa.CheckConstraint('like_count >= 0', name='ck_ext_creation_post_like_count'),
        sa.CheckConstraint('favorite_count >= 0', name='ck_ext_creation_post_favorite_count'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_creation_post_status_published',
        'ext_creation_post',
        ['status', 'published_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_creation_post_status_popular',
        'ext_creation_post',
        ['status', 'favorite_count', 'like_count', 'published_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_creation_post_user_status',
        'ext_creation_post',
        ['user_id', 'status', 'updated_at', 'id'],
        schema=schema,
    )

    op.create_table(
        'ext_creation_post_media',
        sa.Column('post_id', sa.String(128), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('creation_id', sa.String(128), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('post_id', 'position'),
        sa.UniqueConstraint('creation_id', name='uq_ext_creation_post_media_creation'),
        sa.UniqueConstraint('post_id', 'position', name='uq_ext_creation_post_media_position'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_creation_post_media_creation',
        'ext_creation_post_media',
        ['creation_id'],
        schema=schema,
    )

    op.create_table(
        'ext_creation_post_reaction',
        sa.Column('post_id', sa.String(128), nullable=False),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('kind', sa.String(16), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('post_id', 'user_id', 'kind'),
        sa.UniqueConstraint(
            'post_id',
            'user_id',
            'kind',
            name='uq_ext_creation_post_reaction_actor_kind',
        ),
        sa.CheckConstraint("kind IN ('like', 'favorite')", name='ck_ext_creation_post_reaction_kind'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_creation_post_reaction_user_kind',
        'ext_creation_post_reaction',
        ['user_id', 'kind', 'created_at', 'post_id'],
        schema=schema,
    )


def downgrade() -> None:
    schema = _current_schema()
    op.drop_index(
        'ix_ext_creation_post_reaction_user_kind',
        table_name='ext_creation_post_reaction',
        schema=schema,
    )
    op.drop_table('ext_creation_post_reaction', schema=schema)
    op.drop_index(
        'ix_ext_creation_post_media_creation',
        table_name='ext_creation_post_media',
        schema=schema,
    )
    op.drop_table('ext_creation_post_media', schema=schema)
    op.drop_index('ix_ext_creation_post_user_status', table_name='ext_creation_post', schema=schema)
    op.drop_index('ix_ext_creation_post_status_popular', table_name='ext_creation_post', schema=schema)
    op.drop_index('ix_ext_creation_post_status_published', table_name='ext_creation_post', schema=schema)
    op.drop_table('ext_creation_post', schema=schema)
