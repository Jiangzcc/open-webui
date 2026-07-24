from __future__ import annotations

from open_webui.env import DATABASE_SCHEMA
from open_webui.internal.db import JSONField
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Index,
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


__all__ = ['CreationMediaItem']
