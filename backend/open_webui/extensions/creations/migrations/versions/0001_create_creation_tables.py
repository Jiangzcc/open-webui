"""Create all creation-extension tables in one revision.

Revision ID: 0001_create_creation_tables
Revises:

开发阶段 squash（复盘 #13）：原 0001–0008 增量迁移合并为单一基线，净效果
与按序应用全部旧版本一致——

- ext_creation_media_item：媒体条目（0001）+ 视频扩展列与终态约束（0007）
- ext_creation_post / post_media / post_reaction：发现页（0002）
  + 分类与精选运营列（0004；0006 移除的类别 CHECK 不再创建）
- ext_creation_category：内置分类种子（0006）
- ext_image_generation_task：图片任务（0003；0004 加、0005 删的通知列净为零）
  + 完整请求摘要（2026-08-24，避免含参考图的幂等键错误复用）
- ext_video_generation_task：视频任务（0007）+ FAL 交付恢复列（0008）
  （2026-08-23 复盘 P0-1：其 params/assets/result_json 三列由 sa.JSON 修正为
  JSONField——ORM 按此 TEXT 打底类型读写，原生 JSON 列在 PostgreSQL 上读取即
  TypeError；开发阶段直接改基线，存量库见下方处置说明）
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from open_webui.internal.db import JSONField

revision: str = '0001_create_creation_tables'
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
        sa.Column('poster_file_id', sa.String(128), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_id', name='uq_ext_creation_media_file'),
        sa.CheckConstraint("kind IN ('image', 'video')", name='ck_ext_creation_media_kind'),
        sa.CheckConstraint(
            "task IN ('text-to-image', 'image-to-image', 'text-to-video', 'image-to-video', 'video-to-video')",
            name='ck_ext_creation_media_task',
        ),
        sa.CheckConstraint(
            "source IN ('web', 'api', 'chat', 'tool')",
            name='ck_ext_creation_media_source',
        ),
        sa.CheckConstraint(
            "(kind = 'image' AND duration_seconds IS NULL) OR "
            "(kind = 'video' AND duration_seconds IS NOT NULL AND duration_seconds > 0)",
            name='ck_ext_creation_media_duration',
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
        sa.Column('category', sa.String(32), server_default='other', nullable=False),
        sa.Column('featured_at', sa.BigInteger(), nullable=True),
        sa.Column('featured_rank', sa.Integer(), server_default='1000', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status IN ('published', 'withdrawn', 'hidden')",
            name='ck_ext_creation_post_status',
        ),
        sa.CheckConstraint('like_count >= 0', name='ck_ext_creation_post_like_count'),
        sa.CheckConstraint('favorite_count >= 0', name='ck_ext_creation_post_favorite_count'),
        sa.CheckConstraint('featured_rank >= 0', name='ck_ext_creation_post_featured_rank'),
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
    op.create_index(
        'ix_ext_creation_post_status_category',
        'ext_creation_post',
        ['status', 'category', 'published_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_creation_post_status_featured',
        'ext_creation_post',
        ['status', 'featured_rank', 'featured_at', 'id'],
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
        sa.CheckConstraint("kind IN ('like', 'favorite')", name='ck_ext_creation_post_reaction_kind'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_creation_post_reaction_user_kind',
        'ext_creation_post_reaction',
        ['user_id', 'kind', 'created_at', 'post_id'],
        schema=schema,
    )

    category_table = op.create_table(
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
        category_table,
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

    op.create_table(
        'ext_image_generation_task',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('idempotency_key', sa.String(128), nullable=False),
        sa.Column('payload_sha256', sa.String(64), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('kind', sa.String(32), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('model_id', sa.String(256), nullable=True),
        sa.Column('params_json', JSONField(), nullable=True),
        sa.Column('expected_count', sa.Integer(), nullable=False),
        sa.Column('result_json', JSONField(), nullable=True),
        sa.Column('error_code', sa.String(64), nullable=True),
        sa.Column('execution_mode', sa.String(16), nullable=True),
        sa.Column('delivery_attempts', sa.Integer(), nullable=False, server_default='0'),
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
        sa.CheckConstraint(
            "execution_mode IS NULL OR execution_mode IN ('mock', 'fal')",
            name='ck_ext_image_task_execution_mode',
        ),
        sa.CheckConstraint('delivery_attempts >= 0', name='ck_ext_image_task_delivery_attempts'),
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

    op.create_table(
        'ext_video_generation_task',
        sa.Column('id', sa.String(128), primary_key=True),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('idempotency_key', sa.String(128), nullable=False),
        sa.Column('payload_sha256', sa.String(64), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('task', sa.String(32), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('model_id', sa.String(256), nullable=False),
        sa.Column('params_json', JSONField(), nullable=True),
        sa.Column('assets_json', JSONField(), nullable=True),
        sa.Column('provider_definition_json', JSONField(), nullable=False),
        sa.Column('provider_payload_json', JSONField(), nullable=False),
        sa.Column('result_json', JSONField(), nullable=True),
        sa.Column('error_code', sa.String(64), nullable=True),
        sa.Column('usage_id', sa.String(128), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('started_at', sa.BigInteger(), nullable=True),
        sa.Column('completed_at', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.Column('execution_mode', sa.String(16), nullable=True),
        sa.Column('provider_request_id', sa.String(128), nullable=True),
        sa.Column('provider_status_url', sa.Text(), nullable=True),
        sa.Column('provider_response_url', sa.Text(), nullable=True),
        sa.Column('provider_result_url', sa.Text(), nullable=True),
        sa.Column('delivery_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.UniqueConstraint('user_id', 'idempotency_key', name='uq_ext_video_task_user_key'),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name='ck_ext_video_task_status',
        ),
        sa.CheckConstraint(
            "task IN ('text-to-video', 'image-to-video', 'video-to-video')",
            name='ck_ext_video_task_kind',
        ),
        sa.CheckConstraint(
            "execution_mode IS NULL OR execution_mode IN ('mock', 'fal')",
            name='ck_ext_video_task_execution_mode',
        ),
        sa.CheckConstraint(
            'delivery_attempts >= 0',
            name='ck_ext_video_task_delivery_attempts',
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
    for index_name, table_name in (
        ('ix_ext_video_task_status_updated', 'ext_video_generation_task'),
        ('ix_ext_video_task_user_created', 'ext_video_generation_task'),
        ('ix_ext_image_task_status_updated', 'ext_image_generation_task'),
        ('ix_ext_image_task_user_created', 'ext_image_generation_task'),
        ('ix_ext_creation_category_enabled_order', 'ext_creation_category'),
        ('ix_ext_creation_post_reaction_user_kind', 'ext_creation_post_reaction'),
        ('ix_ext_creation_post_media_creation', 'ext_creation_post_media'),
        ('ix_ext_creation_post_status_featured', 'ext_creation_post'),
        ('ix_ext_creation_post_status_category', 'ext_creation_post'),
        ('ix_ext_creation_post_user_status', 'ext_creation_post'),
        ('ix_ext_creation_post_status_popular', 'ext_creation_post'),
        ('ix_ext_creation_post_status_published', 'ext_creation_post'),
        ('ix_ext_creation_media_batch', 'ext_creation_media_item'),
        ('ix_ext_creation_media_visible_created', 'ext_creation_media_item'),
        ('ix_ext_creation_media_user_visible_created', 'ext_creation_media_item'),
    ):
        op.drop_index(index_name, table_name=table_name, schema=schema)
    for table_name in (
        'ext_video_generation_task',
        'ext_image_generation_task',
        'ext_creation_category',
        'ext_creation_post_reaction',
        'ext_creation_post_media',
        'ext_creation_post',
        'ext_creation_media_item',
    ):
        op.drop_table(table_name, schema=schema)
