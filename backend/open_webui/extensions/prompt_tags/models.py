from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from .db import JSONField, PromptTagBase


class PromptTagCategory(PromptTagBase):
    __tablename__ = 'ext_prompt_tag_category'
    __table_args__ = (
        UniqueConstraint('slug', name='uq_ext_prompt_tag_category_slug'),
        CheckConstraint('sort_order >= 0', name='ck_ext_prompt_tag_category_sort_order'),
        Index('ix_ext_prompt_tag_category_visibility_order', 'enabled', 'sort_order', 'id'),
    )

    id = Column(String(64), primary_key=True)
    slug = Column(String(64), nullable=False)
    name_zh = Column(String(128), nullable=False)
    name_en = Column(String(128), nullable=False)
    enabled = Column(Boolean, nullable=False, server_default='true')
    sort_order = Column(Integer, nullable=False, server_default='1000')
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    updated_by_id = Column(String(128), nullable=True)
    updated_by_name_snapshot = Column(String(256), nullable=True)


class PromptTag(PromptTagBase):
    __tablename__ = 'ext_prompt_tag'
    __table_args__ = (
        UniqueConstraint('slug', name='uq_ext_prompt_tag_slug'),
        CheckConstraint('sort_order >= 0', name='ck_ext_prompt_tag_sort_order'),
        Index('ix_ext_prompt_tag_category_enabled_order', 'category_id', 'enabled', 'sort_order', 'id'),
        Index('ix_ext_prompt_tag_enabled_order', 'enabled', 'sort_order', 'id'),
    )

    id = Column(String(64), primary_key=True)
    slug = Column(String(64), nullable=False)
    category_id = Column(
        String(64),
        ForeignKey('ext_prompt_tag_category.id', ondelete='CASCADE'),
        nullable=False,
    )
    label_zh = Column(String(128), nullable=False)
    label_en = Column(String(128), nullable=False)
    insert_text = Column(String(500), nullable=False)
    is_negative = Column(Boolean, nullable=False, server_default='false')
    media_kinds_json = Column(JSONField, nullable=False, server_default='[]')
    model_refs_json = Column(JSONField, nullable=False, server_default='[]')
    enabled = Column(Boolean, nullable=False, server_default='true')
    sort_order = Column(Integer, nullable=False, server_default='1000')
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    updated_by_id = Column(String(128), nullable=True)
    updated_by_name_snapshot = Column(String(256), nullable=True)


__all__ = ['PromptTag', 'PromptTagCategory']
