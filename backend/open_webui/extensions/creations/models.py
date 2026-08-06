from __future__ import annotations

from open_webui.env import DATABASE_SCHEMA
from open_webui.internal.db import JSONField
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from .db import CreationBase


def _creation_table(name: str) -> str:
    return f'{DATABASE_SCHEMA}.{name}' if DATABASE_SCHEMA else name


class CreationMediaItem(CreationBase):
    __tablename__ = 'ext_creation_media_item'
    __table_args__ = (
        UniqueConstraint('file_id', name='uq_ext_creation_media_file'),
        CheckConstraint("kind IN ('image')", name='ck_ext_creation_media_kind'),
        CheckConstraint(
            "task IN ('text-to-image', 'image-to-image')",
            name='ck_ext_creation_media_task',
        ),
        CheckConstraint(
            "source IN ('web', 'api', 'chat', 'tool')",
            name='ck_ext_creation_media_source',
        ),
        Index(
            'ix_ext_creation_media_user_visible_created',
            'user_id',
            'soft_deleted',
            'created_at',
            'id',
        ),
        Index(
            'ix_ext_creation_media_visible_created',
            'soft_deleted',
            'created_at',
            'id',
        ),
        Index('ix_ext_creation_media_batch', 'batch_id'),
    )

    id = Column(String(128), primary_key=True)
    user_id = Column(String(128), nullable=False)
    kind = Column(String(16), nullable=False)
    file_id = Column(String(128), nullable=False)
    caption = Column(String(1000), nullable=True)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    model_id = Column(String(256), nullable=True)
    model_name_snapshot = Column(String(256), nullable=True)
    task = Column(String(32), nullable=False)
    params_json = Column(JSONField, nullable=True)
    reference_file_ids_json = Column(JSONField, nullable=True)
    source = Column(String(16), nullable=False)
    batch_id = Column(String(128), nullable=False)
    soft_deleted = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class CreationPost(CreationBase):
    __tablename__ = 'ext_creation_post'
    __table_args__ = (
        CheckConstraint(
            "status IN ('published', 'withdrawn', 'hidden')",
            name='ck_ext_creation_post_status',
        ),
        CheckConstraint('like_count >= 0', name='ck_ext_creation_post_like_count'),
        CheckConstraint('favorite_count >= 0', name='ck_ext_creation_post_favorite_count'),
        CheckConstraint('featured_rank >= 0', name='ck_ext_creation_post_featured_rank'),
        Index(
            'ix_ext_creation_post_status_published',
            'status',
            'published_at',
            'id',
        ),
        Index(
            'ix_ext_creation_post_status_popular',
            'status',
            'favorite_count',
            'like_count',
            'published_at',
            'id',
        ),
        Index('ix_ext_creation_post_user_status', 'user_id', 'status', 'updated_at', 'id'),
        Index('ix_ext_creation_post_status_category', 'status', 'category', 'published_at', 'id'),
        Index(
            'ix_ext_creation_post_status_featured',
            'status',
            'featured_rank',
            'featured_at',
            'id',
        ),
    )

    id = Column(String(128), primary_key=True)
    user_id = Column(String(128), nullable=False)
    status = Column(String(16), nullable=False)
    title = Column(String(200), nullable=True)
    description = Column(String(1000), nullable=True)
    show_prompt = Column(Boolean, nullable=False, server_default='true')
    category = Column(String(32), nullable=False, server_default='other')
    featured_at = Column(BigInteger, nullable=True)
    featured_rank = Column(Integer, nullable=False, server_default='1000')
    like_count = Column(Integer, nullable=False, server_default='0')
    favorite_count = Column(Integer, nullable=False, server_default='0')
    published_at = Column(BigInteger, nullable=False)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class DiscoveryCategorySetting(CreationBase):
    __tablename__ = 'ext_creation_category'
    __table_args__ = (
        CheckConstraint('sort_order >= 0', name='ck_ext_creation_category_sort_order'),
        Index('ix_ext_creation_category_enabled_order', 'enabled', 'sort_order', 'id'),
    )

    id = Column(String(32), primary_key=True)
    display_name = Column(String(64), nullable=False)
    enabled = Column(Boolean, nullable=False, server_default='true')
    sort_order = Column(Integer, nullable=False, server_default='1000')
    updated_at = Column(BigInteger, nullable=False)


class CreationPostMedia(CreationBase):
    __tablename__ = 'ext_creation_post_media'
    __table_args__ = (
        UniqueConstraint('creation_id', name='uq_ext_creation_post_media_creation'),
        UniqueConstraint('post_id', 'position', name='uq_ext_creation_post_media_position'),
        Index('ix_ext_creation_post_media_creation', 'creation_id'),
    )

    post_id = Column(String(128), primary_key=True)
    position = Column(Integer, primary_key=True)
    creation_id = Column(String(128), nullable=False)
    created_at = Column(BigInteger, nullable=False)


class CreationPostReaction(CreationBase):
    __tablename__ = 'ext_creation_post_reaction'
    __table_args__ = (
        CheckConstraint("kind IN ('like', 'favorite')", name='ck_ext_creation_post_reaction_kind'),
        UniqueConstraint(
            'post_id',
            'user_id',
            'kind',
            name='uq_ext_creation_post_reaction_actor_kind',
        ),
        Index('ix_ext_creation_post_reaction_user_kind', 'user_id', 'kind', 'created_at', 'post_id'),
    )

    post_id = Column(String(128), primary_key=True)
    user_id = Column(String(128), primary_key=True)
    kind = Column(String(16), primary_key=True)
    created_at = Column(BigInteger, nullable=False)


class ImageGenerationTask(CreationBase):
    __tablename__ = 'ext_image_generation_task'
    __table_args__ = (
        UniqueConstraint('user_id', 'idempotency_key', name='uq_ext_image_task_user_key'),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name='ck_ext_image_task_status',
        ),
        CheckConstraint(
            "kind IN ('text-to-image', 'image-to-image')",
            name='ck_ext_image_task_kind',
        ),
        CheckConstraint('expected_count >= 1', name='ck_ext_image_task_expected_count'),
        Index('ix_ext_image_task_user_created', 'user_id', 'created_at', 'id'),
        Index('ix_ext_image_task_status_updated', 'status', 'updated_at', 'id'),
    )

    id = Column(String(128), primary_key=True)
    user_id = Column(String(128), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    status = Column(String(16), nullable=False)
    kind = Column(String(32), nullable=False)
    prompt = Column(Text, nullable=False)
    model_id = Column(String(256), nullable=True)
    params_json = Column(JSONField, nullable=True)
    expected_count = Column(Integer, nullable=False)
    result_json = Column(JSONField, nullable=True)
    error_code = Column(String(64), nullable=True)
    created_at = Column(BigInteger, nullable=False)
    started_at = Column(BigInteger, nullable=True)
    completed_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=False)


__all__ = [
    'CreationMediaItem',
    'CreationPost',
    'CreationPostMedia',
    'CreationPostReaction',
    'DiscoveryCategorySetting',
    'ImageGenerationTask',
]
