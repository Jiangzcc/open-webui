from __future__ import annotations

from time import time
from typing import Any
from uuid import uuid4

from open_webui.extensions.fal_catalog.loader import load_video_catalog_cached
from open_webui.extensions.fal_images.models import normalize_fal_image_model_id
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import PromptTag, PromptTagCategory
from .schemas import (
    MediaKind,
    PromptTagAdminCatalog,
    PromptTagCategoryCreate,
    PromptTagCategoryItem,
    PromptTagCategoryUpdate,
    PromptTagCreate,
    PromptTagExportCategory,
    PromptTagExportDocument,
    PromptTagExportTag,
    PromptTagImportRequest,
    PromptTagImportResult,
    PromptTagItem,
    PromptTagModelRef,
    PromptTagPublicCatalog,
    PromptTagPublicCategory,
    PromptTagPublicTag,
    PromptTagUpdate,
)


class PromptTagNotFoundError(LookupError):
    pass


class PromptTagConflictError(ValueError):
    pass


class PromptTagCategoryNotEmptyError(ValueError):
    pass


def _now() -> int:
    return int(time())


def _operator_snapshot(operator: object) -> tuple[str | None, str | None]:
    return getattr(operator, 'id', None), getattr(operator, 'name', None)


def canonical_model_id(media_kind: MediaKind, model_id: str) -> str:
    # 复盘 #18：此处曾有 @lru_cache——但缓存键不含目录版本，目录 JSON 热更新
    # 后旧映射会永久驻留（与 load_video_catalog_cached 的 stat 失效机制矛盾）。
    # 去掉缓存是安全的：load_video_catalog_cached 本身已按 stat 签名缓存，
    # miss 只发生目录 stat + dict 查找，不触发全量解析。
    candidate = model_id.strip().strip('/')
    if media_kind == 'image':
        return normalize_fal_image_model_id(candidate) or candidate
    catalog = load_video_catalog_cached()
    if candidate in catalog.internal_to_public:
        return candidate
    return catalog.public_to_internal.get(candidate, candidate)


def _media_kinds(row: PromptTag) -> tuple[MediaKind, ...]:
    raw = row.media_kinds_json
    if not isinstance(raw, list):
        return ()
    return tuple(value for value in raw if value in {'image', 'video'})


def _model_refs(row: PromptTag) -> tuple[PromptTagModelRef, ...]:
    raw = row.model_refs_json
    if not isinstance(raw, list):
        return ()
    references: list[PromptTagModelRef] = []
    for value in raw:
        try:
            references.append(PromptTagModelRef.model_validate(value))
        except ValueError:
            continue
    return tuple(references)


def _canonical_refs(references: tuple[PromptTagModelRef, ...]) -> list[dict[str, str]]:
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for reference in references:
        canonical = canonical_model_id(reference.media_kind, reference.model_id)
        unique[(reference.media_kind, canonical)] = {
            'media_kind': reference.media_kind,
            'model_id': canonical,
        }
    return list(unique.values())


def _category_item(row: PromptTagCategory) -> PromptTagCategoryItem:
    return PromptTagCategoryItem.model_validate(row)


def _tag_item(row: PromptTag) -> PromptTagItem:
    return PromptTagItem(
        id=row.id,
        slug=row.slug,
        category_id=row.category_id,
        label_zh=row.label_zh,
        label_en=row.label_en,
        insert_text=row.insert_text,
        is_negative=bool(row.is_negative),
        media_kinds=_media_kinds(row),
        model_refs=_model_refs(row),
        enabled=bool(row.enabled),
        sort_order=row.sort_order,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _public_tag_item(row: PromptTag) -> PromptTagPublicTag:
    """公开目录条目：insert_text 直接下发（前端点击标签时插入输入框）。"""
    return PromptTagPublicTag(
        id=row.id,
        slug=row.slug,
        category_id=row.category_id,
        label_zh=row.label_zh,
        label_en=row.label_en,
        insert_text=row.insert_text,
        is_negative=bool(row.is_negative),
        media_kinds=_media_kinds(row),
        model_refs=_model_refs(row),
        sort_order=row.sort_order,
    )


def _tag_applies(row: PromptTag, media_kind: MediaKind | None, model_id: str | None) -> bool:
    if media_kind is None:
        return not _model_refs(row)
    if media_kind not in _media_kinds(row):
        return False
    references = tuple(reference for reference in _model_refs(row) if reference.media_kind == media_kind)
    if not references:
        return True
    if not model_id:
        return False
    canonical = canonical_model_id(media_kind, model_id)
    return any(reference.model_id == canonical for reference in references)


async def get_public_catalog(
    session: AsyncSession,
    *,
    media_kind: MediaKind | None = None,
    model_id: str | None = None,
) -> PromptTagPublicCatalog:
    categories = (
        await session.scalars(
            select(PromptTagCategory)
            .where(PromptTagCategory.enabled.is_(True))
            .order_by(PromptTagCategory.sort_order, PromptTagCategory.id)
        )
    ).all()
    tags = (
        await session.scalars(
            select(PromptTag)
            .where(PromptTag.enabled.is_(True))
            .order_by(PromptTag.category_id, PromptTag.sort_order, PromptTag.id)
        )
    ).all()
    tags_by_category: dict[str, list[PromptTagPublicTag]] = {}
    revision = max((category.updated_at for category in categories), default=0)
    for row in tags:
        revision = max(revision, row.updated_at)
        if _tag_applies(row, media_kind, model_id):
            tags_by_category.setdefault(row.category_id, []).append(_public_tag_item(row))
    return PromptTagPublicCatalog(
        revision=revision,
        categories=tuple(
            PromptTagPublicCategory(
                **_category_item(category).model_dump(),
                tags=tuple(tags_by_category.get(category.id, ())),
            )
            for category in categories
            if tags_by_category.get(category.id)
        ),
    )


async def get_admin_catalog(session: AsyncSession) -> PromptTagAdminCatalog:
    categories = (
        await session.scalars(select(PromptTagCategory).order_by(PromptTagCategory.sort_order, PromptTagCategory.id))
    ).all()
    tags = (
        await session.scalars(select(PromptTag).order_by(PromptTag.category_id, PromptTag.sort_order, PromptTag.id))
    ).all()
    return PromptTagAdminCatalog(
        categories=tuple(_category_item(category) for category in categories),
        tags=tuple(_tag_item(tag) for tag in tags),
    )


async def _category_by_slug(session: AsyncSession, slug: str) -> PromptTagCategory | None:
    return await session.scalar(select(PromptTagCategory).where(PromptTagCategory.slug == slug))


async def _tag_by_slug(session: AsyncSession, slug: str) -> PromptTag | None:
    return await session.scalar(select(PromptTag).where(PromptTag.slug == slug))


async def create_category(
    session: AsyncSession,
    form: PromptTagCategoryCreate,
    operator: object,
) -> PromptTagCategoryItem:
    if await _category_by_slug(session, form.slug) is not None:
        raise PromptTagConflictError('prompt_tag_category_slug_conflict')
    now = _now()
    operator_id, operator_name = _operator_snapshot(operator)
    row = PromptTagCategory(
        id=uuid4().hex,
        **form.model_dump(),
        created_at=now,
        updated_at=now,
        updated_by_id=operator_id,
        updated_by_name_snapshot=operator_name,
    )
    session.add(row)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise PromptTagConflictError('prompt_tag_category_slug_conflict') from error
    return _category_item(row)


async def update_category(
    session: AsyncSession,
    category_id: str,
    form: PromptTagCategoryUpdate,
    operator: object,
) -> PromptTagCategoryItem:
    row = await session.get(PromptTagCategory, category_id)
    if row is None:
        raise PromptTagNotFoundError('prompt_tag_category_not_found')
    changes = {k: v for k, v in form.model_dump(exclude_unset=True).items() if v is not None}
    if 'slug' in changes:
        existing = await _category_by_slug(session, changes['slug'])
        if existing is not None and existing.id != row.id:
            raise PromptTagConflictError('prompt_tag_category_slug_conflict')
    for field, value in changes.items():
        setattr(row, field, value)
    row.updated_at = _now()
    row.updated_by_id, row.updated_by_name_snapshot = _operator_snapshot(operator)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise PromptTagConflictError('prompt_tag_category_slug_conflict') from error
    return _category_item(row)


async def delete_category(session: AsyncSession, category_id: str, *, cascade: bool) -> None:
    row = await session.get(PromptTagCategory, category_id)
    if row is None:
        raise PromptTagNotFoundError('prompt_tag_category_not_found')
    tag = await session.scalar(select(PromptTag.id).where(PromptTag.category_id == category_id).limit(1))
    if tag is not None and not cascade:
        raise PromptTagCategoryNotEmptyError('prompt_tag_category_not_empty')
    if cascade:
        await session.execute(delete(PromptTag).where(PromptTag.category_id == category_id))
    await session.delete(row)
    await session.commit()


def _validated_tag_data(form: PromptTagCreate) -> dict[str, Any]:
    return {
        'slug': form.slug,
        'category_id': form.category_id,
        'label_zh': form.label_zh,
        'label_en': form.label_en,
        'insert_text': form.insert_text,
        'is_negative': form.is_negative,
        'media_kinds_json': list(form.media_kinds),
        'model_refs_json': _canonical_refs(form.model_refs),
        'enabled': form.enabled,
        'sort_order': form.sort_order,
    }


async def create_tag(
    session: AsyncSession,
    form: PromptTagCreate,
    operator: object,
) -> PromptTagItem:
    if await _tag_by_slug(session, form.slug) is not None:
        raise PromptTagConflictError('prompt_tag_slug_conflict')
    if await session.get(PromptTagCategory, form.category_id) is None:
        raise PromptTagNotFoundError('prompt_tag_category_not_found')
    now = _now()
    operator_id, operator_name = _operator_snapshot(operator)
    row = PromptTag(
        id=uuid4().hex,
        **_validated_tag_data(form),
        created_at=now,
        updated_at=now,
        updated_by_id=operator_id,
        updated_by_name_snapshot=operator_name,
    )
    session.add(row)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise PromptTagConflictError('prompt_tag_slug_conflict') from error
    return _tag_item(row)


async def update_tag(
    session: AsyncSession,
    tag_id: str,
    form: PromptTagUpdate,
    operator: object,
) -> PromptTagItem:
    row = await session.get(PromptTag, tag_id)
    if row is None:
        raise PromptTagNotFoundError('prompt_tag_not_found')
    changes = {k: v for k, v in form.model_dump(exclude_unset=True).items() if v is not None}
    if 'slug' in changes:
        existing = await _tag_by_slug(session, changes['slug'])
        if existing is not None and existing.id != row.id:
            raise PromptTagConflictError('prompt_tag_slug_conflict')
    category_id = changes.get('category_id', row.category_id)
    if await session.get(PromptTagCategory, category_id) is None:
        raise PromptTagNotFoundError('prompt_tag_category_not_found')
    validated = PromptTagCreate(
        slug=changes.get('slug', row.slug),
        category_id=category_id,
        label_zh=changes.get('label_zh', row.label_zh),
        label_en=changes.get('label_en', row.label_en),
        insert_text=changes.get('insert_text', row.insert_text),
        is_negative=changes.get('is_negative', row.is_negative),
        media_kinds=changes.get('media_kinds', _media_kinds(row)),
        model_refs=changes.get('model_refs', _model_refs(row)),
        enabled=changes.get('enabled', row.enabled),
        sort_order=changes.get('sort_order', row.sort_order),
    )
    for field, value in _validated_tag_data(validated).items():
        setattr(row, field, value)
    row.updated_at = _now()
    row.updated_by_id, row.updated_by_name_snapshot = _operator_snapshot(operator)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise PromptTagConflictError('prompt_tag_slug_conflict') from error
    return _tag_item(row)


async def delete_tag(session: AsyncSession, tag_id: str) -> None:
    row = await session.get(PromptTag, tag_id)
    if row is None:
        raise PromptTagNotFoundError('prompt_tag_not_found')
    await session.delete(row)
    await session.commit()


async def export_catalog(session: AsyncSession) -> PromptTagExportDocument:
    catalog = await get_admin_catalog(session)
    category_slugs = {category.id: category.slug for category in catalog.categories}
    return PromptTagExportDocument(
        exported_at=_now(),
        categories=tuple(
            PromptTagExportCategory(
                slug=category.slug,
                name_zh=category.name_zh,
                name_en=category.name_en,
                enabled=category.enabled,
                sort_order=category.sort_order,
            )
            for category in catalog.categories
        ),
        tags=tuple(
            PromptTagExportTag(
                slug=tag.slug,
                category_slug=category_slugs[tag.category_id],
                label_zh=tag.label_zh,
                label_en=tag.label_en,
                insert_text=tag.insert_text,
                is_negative=tag.is_negative,
                media_kinds=tag.media_kinds,
                model_refs=tag.model_refs,
                enabled=tag.enabled,
                sort_order=tag.sort_order,
            )
            for tag in catalog.tags
        ),
    )


def _upsert_import_category(
    session: AsyncSession,
    item: PromptTagExportCategory,
    existing: dict[str, PromptTagCategory],
    *,
    now: int,
    operator_id: str | None,
    operator_name: str | None,
) -> bool:
    row = existing.get(item.slug)
    if row is None:
        row = PromptTagCategory(
            id=uuid4().hex,
            slug=item.slug,
            created_at=now,
        )
        session.add(row)
        existing[item.slug] = row
        created = True
    else:
        created = False
    row.name_zh = item.name_zh
    row.name_en = item.name_en
    row.enabled = item.enabled
    row.sort_order = item.sort_order
    row.updated_at = now
    row.updated_by_id = operator_id
    row.updated_by_name_snapshot = operator_name
    return created


def _upsert_import_tag(
    session: AsyncSession,
    item: PromptTagExportTag,
    categories: dict[str, PromptTagCategory],
    existing: dict[str, PromptTag],
    *,
    now: int,
    operator_id: str | None,
    operator_name: str | None,
) -> bool:
    validated = PromptTagCreate(
        slug=item.slug,
        category_id=categories[item.category_slug].id,
        label_zh=item.label_zh,
        label_en=item.label_en,
        insert_text=item.insert_text,
        is_negative=item.is_negative,
        media_kinds=item.media_kinds,
        model_refs=item.model_refs,
        enabled=item.enabled,
        sort_order=item.sort_order,
    )
    row = existing.get(item.slug)
    if row is None:
        row = PromptTag(id=uuid4().hex, created_at=now)
        session.add(row)
        existing[item.slug] = row
        created = True
    else:
        created = False
    for field, value in _validated_tag_data(validated).items():
        setattr(row, field, value)
    row.updated_at = now
    row.updated_by_id = operator_id
    row.updated_by_name_snapshot = operator_name
    return created


async def _finish_catalog_import(session: AsyncSession, *, dry_run: bool) -> None:
    try:
        await session.flush()
        if dry_run:
            await session.rollback()
        else:
            await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise PromptTagConflictError('prompt_tag_import_conflict') from error
    except BaseException:
        await session.rollback()
        raise


async def import_catalog(
    session: AsyncSession,
    form: PromptTagImportRequest,
    operator: object,
) -> PromptTagImportResult:
    existing_categories = {row.slug: row for row in (await session.scalars(select(PromptTagCategory))).all()}
    existing_tags = {row.slug: row for row in (await session.scalars(select(PromptTag))).all()}
    category_conflicts = set(existing_categories) & {category.slug for category in form.categories}
    tag_conflicts = set(existing_tags) & {tag.slug for tag in form.tags}
    if not form.upsert and (category_conflicts or tag_conflicts):
        raise PromptTagConflictError('prompt_tag_import_conflict')

    now = _now()
    operator_id, operator_name = _operator_snapshot(operator)
    category_results = [
        _upsert_import_category(
            session,
            item,
            existing_categories,
            now=now,
            operator_id=operator_id,
            operator_name=operator_name,
        )
        for item in form.categories
    ]
    tag_results = [
        _upsert_import_tag(
            session,
            item,
            existing_categories,
            existing_tags,
            now=now,
            operator_id=operator_id,
            operator_name=operator_name,
        )
        for item in form.tags
    ]
    await _finish_catalog_import(session, dry_run=form.dry_run)

    return PromptTagImportResult(
        dry_run=form.dry_run,
        categories_created=sum(category_results),
        categories_updated=len(category_results) - sum(category_results),
        tags_created=sum(tag_results),
        tags_updated=len(tag_results) - sum(tag_results),
    )


__all__ = [
    'PromptTagCategoryNotEmptyError',
    'PromptTagConflictError',
    'PromptTagNotFoundError',
    'canonical_model_id',
    'create_category',
    'create_tag',
    'delete_category',
    'delete_tag',
    'export_catalog',
    'get_admin_catalog',
    'get_public_catalog',
    'import_catalog',
    'update_category',
    'update_tag',
]
