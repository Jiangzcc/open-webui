"""Create maintainable discovery category settings.

Revision ID: 0006_create_discovery_categories
Revises: 0005_remove_task_notifications
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0006_create_discovery_categories'
down_revision: str | None = '0005_remove_task_notifications'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('creation_schema')


def upgrade() -> None:
    schema = _current_schema()
    with op.batch_alter_table('ext_creation_post', schema=schema) as batch:
        batch.drop_constraint('ck_ext_creation_post_category', type_='check')
    table = op.create_table(
        'ext_creation_category',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('display_name', sa.String(64), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='1000', nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.CheckConstraint('sort_order >= 0', name='ck_ext_creation_category_sort_order'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_creation_category_enabled_order',
        'ext_creation_category',
        ['enabled', 'sort_order', 'id'],
        schema=schema,
    )
    op.bulk_insert(
        table,
        [
            {'id': 'portrait', 'display_name': 'Portrait', 'enabled': True, 'sort_order': 10, 'updated_at': 0},
            {'id': 'product', 'display_name': 'Product', 'enabled': True, 'sort_order': 20, 'updated_at': 0},
            {'id': 'poster', 'display_name': 'Poster', 'enabled': True, 'sort_order': 30, 'updated_at': 0},
            {'id': 'illustration', 'display_name': 'Illustration', 'enabled': True, 'sort_order': 40, 'updated_at': 0},
            {'id': 'anime', 'display_name': 'Anime', 'enabled': True, 'sort_order': 50, 'updated_at': 0},
            {'id': 'landscape', 'display_name': 'Landscape', 'enabled': True, 'sort_order': 60, 'updated_at': 0},
            {'id': 'other', 'display_name': 'Other', 'enabled': True, 'sort_order': 999, 'updated_at': 0},
        ],
    )


def downgrade() -> None:
    schema = _current_schema()
    op.drop_index(
        'ix_ext_creation_category_enabled_order',
        table_name='ext_creation_category',
        schema=schema,
    )
    op.drop_table('ext_creation_category', schema=schema)
    post = sa.table('ext_creation_post', sa.column('category', sa.String(32)))
    built_in_ids = ('portrait', 'product', 'poster', 'illustration', 'anime', 'landscape', 'other')
    op.execute(post.update().where(post.c.category.notin_(built_in_ids)).values(category='other'))
    with op.batch_alter_table('ext_creation_post', schema=schema) as batch:
        batch.create_check_constraint(
            'ck_ext_creation_post_category',
            "category IN ('portrait', 'product', 'poster', 'illustration', 'anime', 'landscape', 'other')",
        )
