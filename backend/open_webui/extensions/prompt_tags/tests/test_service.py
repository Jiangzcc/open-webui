from __future__ import annotations

from types import SimpleNamespace

import pytest
from open_webui.extensions.prompt_tags.schemas import (
    PromptTagCategoryCreate,
    PromptTagCategoryUpdate,
    PromptTagCreate,
    PromptTagUpdate,
)
from open_webui.extensions.prompt_tags.service import (
    create_category,
    create_tag,
    get_public_catalog,
    update_category,
    update_tag,
)


def _user() -> SimpleNamespace:
    return SimpleNamespace(id='admin-1', name='Admin', role='admin')


@pytest.mark.asyncio
async def test_update_category_ignores_null_fields(prompt_tag_sessions) -> None:
    """Sending null for optional fields must not crash or change existing values."""
    async with prompt_tag_sessions() as session:
        user = _user()
        category = await create_category(
            session,
            PromptTagCategoryCreate(
                slug='lighting',
                name_zh='光影',
                name_en='Lighting',
                enabled=True,
                sort_order=100,
            ),
            user,
        )

        updated = await update_category(
            session,
            category.id,
            PromptTagCategoryUpdate(
                slug=None,
                name_zh=None,
                name_en=None,
                enabled=None,
                sort_order=None,
            ),
            user,
        )

        assert updated.slug == 'lighting'
        assert updated.name_zh == '光影'
        assert updated.name_en == 'Lighting'
        assert updated.enabled is True
        assert updated.sort_order == 100


@pytest.mark.asyncio
async def test_update_tag_ignores_null_fields(prompt_tag_sessions) -> None:
    """Sending null for optional fields must not crash or change existing values."""
    async with prompt_tag_sessions() as session:
        user = _user()
        category = await create_category(
            session,
            PromptTagCategoryCreate(slug='lighting', name_zh='光影', name_en='Lighting'),
            user,
        )
        tag = await create_tag(
            session,
            PromptTagCreate(
                slug='cinematic',
                category_id=category.id,
                label_zh='电影感',
                label_en='Cinematic',
                insert_text='cinematic lighting',
                is_negative=False,
                media_kinds=('image', 'video'),
                enabled=True,
                sort_order=500,
            ),
            user,
        )

        updated = await update_tag(
            session,
            tag.id,
            PromptTagUpdate(
                slug=None,
                category_id=None,
                label_zh=None,
                label_en=None,
                insert_text=None,
                is_negative=None,
                media_kinds=None,
                model_refs=None,
                enabled=None,
                sort_order=None,
            ),
            user,
        )

        assert updated.slug == 'cinematic'
        assert updated.category_id == category.id
        assert updated.label_zh == '电影感'
        assert updated.label_en == 'Cinematic'
        assert updated.insert_text == 'cinematic lighting'
        assert updated.is_negative is False
        assert updated.media_kinds == ('image', 'video')
        assert updated.model_refs == ()
        assert updated.enabled is True
        assert updated.sort_order == 500


@pytest.mark.asyncio
async def test_update_tag_applies_real_changes_alongside_nulls(prompt_tag_sessions) -> None:
    """Non-null values in an update must still be applied; nulls must be ignored."""
    async with prompt_tag_sessions() as session:
        user = _user()
        category = await create_category(
            session,
            PromptTagCategoryCreate(slug='lighting', name_zh='光影', name_en='Lighting'),
            user,
        )
        tag = await create_tag(
            session,
            PromptTagCreate(
                slug='cinematic',
                category_id=category.id,
                label_zh='电影感',
                label_en='Cinematic',
                insert_text='cinematic lighting',
                is_negative=False,
                media_kinds=('image', 'video'),
                enabled=True,
                sort_order=500,
            ),
            user,
        )

        updated = await update_tag(
            session,
            tag.id,
            PromptTagUpdate(
                label_zh='电影光效',
                media_kinds=None,  # null — should keep existing
                is_negative=True,
            ),
            user,
        )

        assert updated.label_zh == '电影光效'
        assert updated.is_negative is True
        assert updated.media_kinds == ('image', 'video')  # unchanged by null
        assert updated.slug == 'cinematic'  # unchanged


@pytest.mark.asyncio
async def test_public_catalog_exposes_insert_text(prompt_tag_sessions) -> None:
    """公开目录携带 insert_text：标签是快捷提示词片段，前端点击标签
    直接把实际文本插入输入框（2026-08-22 放弃服务端保密模型）。"""
    async with prompt_tag_sessions() as session:
        user = _user()
        category = await create_category(
            session,
            PromptTagCategoryCreate(slug='styles', name_zh='风格', name_en='Styles'),
            user,
        )
        await create_tag(
            session,
            PromptTagCreate(
                slug='cinematic',
                category_id=category.id,
                label_zh='电影感光效',
                label_en='Cinematic lighting',
                insert_text='cinematic lighting, dramatic shadows',
            ),
            user,
        )

        catalog = await get_public_catalog(session, media_kind='image', model_id='fal-ai/flux')
        tag = catalog.categories[0].tags[0]
        assert tag.label_zh == '电影感光效'
        assert tag.insert_text == 'cinematic lighting, dramatic shadows'
