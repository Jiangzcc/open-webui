from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MediaKind = Literal['image', 'video']


def _single_line(value: str) -> str:
    normalized = ' '.join(value.split())
    if not normalized:
        raise ValueError('value must not be empty')
    return normalized


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', from_attributes=True)


class PromptTagModelRef(StrictModel):
    media_kind: MediaKind
    model_id: str = Field(min_length=1, max_length=256)

    @field_validator('model_id')
    @classmethod
    def normalize_model_id(cls, value: str) -> str:
        return _single_line(value).strip('/')


class PromptTagCategoryCreate(StrictModel):
    slug: str = Field(min_length=1, max_length=64, pattern=r'^[a-z0-9][a-z0-9_-]*$')
    name_zh: str = Field(min_length=1, max_length=128)
    name_en: str = Field(min_length=1, max_length=128)
    enabled: bool = True
    sort_order: int = Field(default=1000, ge=0, le=100000)

    @field_validator('slug', mode='before')
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator('name_zh', 'name_en')
    @classmethod
    def normalize_names(cls, value: str) -> str:
        return _single_line(value)


class PromptTagCategoryUpdate(StrictModel):
    slug: str | None = Field(default=None, min_length=1, max_length=64, pattern=r'^[a-z0-9][a-z0-9_-]*$')
    name_zh: str | None = Field(default=None, min_length=1, max_length=128)
    name_en: str | None = Field(default=None, min_length=1, max_length=128)
    enabled: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=100000)

    @field_validator('slug', mode='before')
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator('name_zh', 'name_en')
    @classmethod
    def normalize_names(cls, value: str | None) -> str | None:
        return _single_line(value) if value is not None else None

    @model_validator(mode='after')
    def require_change(self) -> PromptTagCategoryUpdate:
        if not self.model_fields_set:
            raise ValueError('at least one category field is required')
        return self


class PromptTagCategoryItem(StrictModel):
    id: str
    slug: str
    name_zh: str
    name_en: str
    enabled: bool
    sort_order: int
    created_at: int
    updated_at: int


class PromptTagCreate(StrictModel):
    slug: str = Field(min_length=1, max_length=64, pattern=r'^[a-z0-9][a-z0-9_-]*$')
    category_id: str = Field(min_length=1, max_length=64)
    label_zh: str = Field(min_length=1, max_length=128)
    label_en: str = Field(min_length=1, max_length=128)
    insert_text: str = Field(min_length=1, max_length=500)
    is_negative: bool = False
    media_kinds: tuple[MediaKind, ...] = ('image', 'video')
    model_refs: tuple[PromptTagModelRef, ...] = ()
    enabled: bool = True
    sort_order: int = Field(default=1000, ge=0, le=100000)

    @field_validator('slug', mode='before')
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator('category_id')
    @classmethod
    def normalize_category_id(cls, value: str) -> str:
        return _single_line(value)

    @field_validator('label_zh', 'label_en', 'insert_text')
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return _single_line(value)

    @field_validator('media_kinds')
    @classmethod
    def normalize_media_kinds(cls, values: tuple[MediaKind, ...]) -> tuple[MediaKind, ...]:
        normalized = tuple(dict.fromkeys(values))
        if not normalized:
            raise ValueError('at least one media kind is required')
        return normalized

    @field_validator('model_refs')
    @classmethod
    def normalize_model_refs(cls, values: tuple[PromptTagModelRef, ...]) -> tuple[PromptTagModelRef, ...]:
        unique: dict[tuple[str, str], PromptTagModelRef] = {}
        for value in values:
            unique[(value.media_kind, value.model_id)] = value
        return tuple(unique.values())

    @model_validator(mode='after')
    def validate_model_ref_media(self) -> PromptTagCreate:
        allowed = set(self.media_kinds)
        if any(reference.media_kind not in allowed for reference in self.model_refs):
            raise ValueError('model reference media kind must be enabled on the tag')
        return self


class PromptTagUpdate(StrictModel):
    slug: str | None = Field(default=None, min_length=1, max_length=64, pattern=r'^[a-z0-9][a-z0-9_-]*$')
    category_id: str | None = Field(default=None, min_length=1, max_length=64)
    label_zh: str | None = Field(default=None, min_length=1, max_length=128)
    label_en: str | None = Field(default=None, min_length=1, max_length=128)
    insert_text: str | None = Field(default=None, min_length=1, max_length=500)
    is_negative: bool | None = None
    media_kinds: tuple[MediaKind, ...] | None = None
    model_refs: tuple[PromptTagModelRef, ...] | None = None
    enabled: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=100000)

    @field_validator('slug', mode='before')
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator('category_id', 'label_zh', 'label_en', 'insert_text')
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return _single_line(value) if value is not None else None

    @field_validator('media_kinds')
    @classmethod
    def normalize_media_kinds(cls, values: tuple[MediaKind, ...] | None) -> tuple[MediaKind, ...] | None:
        if values is None:
            return None
        normalized = tuple(dict.fromkeys(values))
        if not normalized:
            raise ValueError('at least one media kind is required')
        return normalized

    @field_validator('model_refs')
    @classmethod
    def normalize_model_refs(cls, values: tuple[PromptTagModelRef, ...] | None) -> tuple[PromptTagModelRef, ...] | None:
        if values is None:
            return None
        unique: dict[tuple[str, str], PromptTagModelRef] = {}
        for value in values:
            unique[(value.media_kind, value.model_id)] = value
        return tuple(unique.values())

    @model_validator(mode='after')
    def require_change(self) -> PromptTagUpdate:
        if not self.model_fields_set:
            raise ValueError('at least one tag field is required')
        if self.media_kinds is not None and self.model_refs is not None:
            allowed = set(self.media_kinds)
            if any(reference.media_kind not in allowed for reference in self.model_refs):
                raise ValueError('model reference media kind must be enabled on the tag')
        return self


class PromptTagItem(StrictModel):
    id: str
    slug: str
    category_id: str
    label_zh: str
    label_en: str
    insert_text: str
    is_negative: bool
    media_kinds: tuple[MediaKind, ...]
    model_refs: tuple[PromptTagModelRef, ...]
    enabled: bool
    sort_order: int
    created_at: int
    updated_at: int


class PromptTagPublicTag(StrictModel):
    """公开目录中的标签条目。

    insert_text 对终端用户公开（2026-08-22 决定放弃保密模型：标签内容
    是通用提示词，不是需要保护的资产）；前端点击标签时直接把 insert_text
    插入输入框，所见即所得。
    """

    id: str
    slug: str
    category_id: str
    label_zh: str
    label_en: str
    insert_text: str
    is_negative: bool
    media_kinds: tuple[MediaKind, ...]
    model_refs: tuple[PromptTagModelRef, ...]
    sort_order: int


class PromptTagPublicCategory(PromptTagCategoryItem):
    tags: tuple[PromptTagPublicTag, ...]


class PromptTagPublicCatalog(StrictModel):
    revision: int
    categories: tuple[PromptTagPublicCategory, ...]


class PromptTagAdminCatalog(StrictModel):
    categories: tuple[PromptTagCategoryItem, ...]
    tags: tuple[PromptTagItem, ...]


class PromptTagExportCategory(PromptTagCategoryCreate):
    pass


class PromptTagExportTag(StrictModel):
    slug: str = Field(min_length=1, max_length=64, pattern=r'^[a-z0-9][a-z0-9_-]*$')
    category_slug: str = Field(min_length=1, max_length=64, pattern=r'^[a-z0-9][a-z0-9_-]*$')
    label_zh: str = Field(min_length=1, max_length=128)
    label_en: str = Field(min_length=1, max_length=128)
    insert_text: str = Field(min_length=1, max_length=500)
    is_negative: bool = False
    media_kinds: tuple[MediaKind, ...] = ('image', 'video')
    model_refs: tuple[PromptTagModelRef, ...] = ()
    enabled: bool = True
    sort_order: int = Field(default=1000, ge=0, le=100000)

    @model_validator(mode='after')
    def validate_export_tag(self) -> PromptTagExportTag:
        PromptTagCreate(
            slug=self.slug,
            category_id=self.category_slug,
            label_zh=self.label_zh,
            label_en=self.label_en,
            insert_text=self.insert_text,
            is_negative=self.is_negative,
            media_kinds=self.media_kinds,
            model_refs=self.model_refs,
            enabled=self.enabled,
            sort_order=self.sort_order,
        )
        return self


class PromptTagExportDocument(StrictModel):
    schema_version: Literal[1] = 1
    exported_at: int
    categories: tuple[PromptTagExportCategory, ...]
    tags: tuple[PromptTagExportTag, ...]


class PromptTagImportRequest(StrictModel):
    schema_version: Literal[1] = 1
    categories: tuple[PromptTagExportCategory, ...] = Field(max_length=200)
    tags: tuple[PromptTagExportTag, ...] = Field(max_length=2000)
    dry_run: bool = False
    upsert: bool = False

    @model_validator(mode='after')
    def validate_unique_slugs_and_references(self) -> PromptTagImportRequest:
        category_slugs = [category.slug for category in self.categories]
        tag_slugs = [tag.slug for tag in self.tags]
        if len(category_slugs) != len(set(category_slugs)):
            raise ValueError('duplicate category slug in import')
        if len(tag_slugs) != len(set(tag_slugs)):
            raise ValueError('duplicate tag slug in import')
        known_categories = set(category_slugs)
        if any(tag.category_slug not in known_categories for tag in self.tags):
            raise ValueError('every imported tag must reference an imported category')
        return self


class PromptTagImportResult(StrictModel):
    dry_run: bool
    categories_created: int
    categories_updated: int
    tags_created: int
    tags_updated: int


__all__ = [
    'MediaKind',
    'PromptTagAdminCatalog',
    'PromptTagCategoryCreate',
    'PromptTagCategoryItem',
    'PromptTagCategoryUpdate',
    'PromptTagCreate',
    'PromptTagExportDocument',
    'PromptTagImportRequest',
    'PromptTagImportResult',
    'PromptTagItem',
    'PromptTagModelRef',
    'PromptTagPublicCatalog',
    'PromptTagUpdate',
]
