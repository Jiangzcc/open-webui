"""Router 层契约测试：直接调用端点函数（不经 TestClient——app 拉起会连
上游迁移链，环境不稳），覆盖 HTTP 状态码映射（404/409/201/204）与
service 错误到 HTTPException 的翻译。行为级覆盖见 test_service.py。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from open_webui.extensions.prompt_tags import router as router_module
from open_webui.extensions.prompt_tags.router import (
    create_admin_prompt_tag,
    create_admin_prompt_tag_category,
    delete_admin_prompt_tag,
    delete_admin_prompt_tag_category,
    export_admin_prompt_tags,
    get_admin_prompt_tag_catalog,
    get_prompt_tag_catalog,
    import_admin_prompt_tags,
    update_admin_prompt_tag,
    update_admin_prompt_tag_category,
)
from open_webui.extensions.prompt_tags.schemas import (
    PromptTagCategoryCreate,
    PromptTagCategoryUpdate,
    PromptTagCreate,
    PromptTagExportDocument,
    PromptTagImportRequest,
    PromptTagUpdate,
)
from open_webui.extensions.prompt_tags.service import (
    create_category,
    create_tag,
)


def _user() -> SimpleNamespace:
    return SimpleNamespace(id='admin-1', name='Admin', role='admin')


async def _seeded_category(prompt_tag_sessions) -> str:
    async with prompt_tag_sessions() as session:
        category = await create_category(
            session,
            PromptTagCategoryCreate(slug='lighting', name_zh='光影', name_en='Lighting'),
            _user(),
        )
        return category.id


@pytest.mark.asyncio
async def test_public_and_admin_catalog_endpoints(prompt_tag_sessions) -> None:
    category_id = await _seeded_category(prompt_tag_sessions)
    async with prompt_tag_sessions() as session:
        await create_tag(
            session,
            PromptTagCreate(
                slug='golden-hour',
                category_id=category_id,
                label_zh='黄金时刻',
                label_en='Golden hour',
                insert_text='golden hour light',
            ),
            _user(),
        )
    async with prompt_tag_sessions() as session:
        public = await get_prompt_tag_catalog(None, None, _user(), session)
        admin = await get_admin_prompt_tag_catalog(_user(), session)
    # 公开目录按分类分组内嵌标签；管理目录是分类/标签两个平铺列表。
    assert [c.slug for c in public.categories] == ['lighting']
    assert [t.slug for c in public.categories for t in c.tags] == ['golden-hour']
    assert [c.slug for c in admin.categories] == ['lighting']
    assert [t.slug for t in admin.tags] == ['golden-hour']


@pytest.mark.asyncio
async def test_category_create_and_slug_conflict_maps_to_409(prompt_tag_sessions) -> None:
    form = PromptTagCategoryCreate(slug='style', name_zh='风格', name_en='Style')
    async with prompt_tag_sessions() as session:
        created = await create_admin_prompt_tag_category(form, _user(), session)
    assert created.slug == 'style'

    async with prompt_tag_sessions() as session:
        with pytest.raises(HTTPException) as raised:
            await create_admin_prompt_tag_category(form, _user(), session)
    assert raised.value.status_code == 409


@pytest.mark.asyncio
async def test_category_update_not_found_maps_to_404(prompt_tag_sessions) -> None:
    form = PromptTagCategoryUpdate(name_zh='新名')
    async with prompt_tag_sessions() as session:
        with pytest.raises(HTTPException) as raised:
            await update_admin_prompt_tag_category('missing', form, _user(), session)
    assert raised.value.status_code == 404


@pytest.mark.asyncio
async def test_category_delete_not_empty_maps_to_409_and_cascade_succeeds(prompt_tag_sessions) -> None:
    category_id = await _seeded_category(prompt_tag_sessions)
    async with prompt_tag_sessions() as session:
        await create_tag(
            session,
            PromptTagCreate(
                slug='soft-light',
                category_id=category_id,
                label_zh='柔光',
                label_en='Soft light',
                insert_text='soft light',
            ),
            _user(),
        )
    async with prompt_tag_sessions() as session:
        with pytest.raises(HTTPException) as raised:
            await delete_admin_prompt_tag_category(category_id, False, _user(), session)
    assert raised.value.status_code == 409

    response = await delete_admin_prompt_tag_category(category_id, True, _user(), session)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_tag_create_unknown_category_maps_to_404(prompt_tag_sessions) -> None:
    form = PromptTagCreate(
        slug='tag-1',
        category_id='missing-category',
        label_zh='标签',
        label_en='Tag',
        insert_text='text',
    )
    async with prompt_tag_sessions() as session:
        with pytest.raises(HTTPException) as raised:
            await create_admin_prompt_tag(form, _user(), session)
    assert raised.value.status_code == 404


@pytest.mark.asyncio
async def test_tag_update_delete_and_conflict_mapping(prompt_tag_sessions) -> None:
    category_id = await _seeded_category(prompt_tag_sessions)
    async with prompt_tag_sessions() as session:
        first = await create_tag(
            session,
            PromptTagCreate(
                slug='first',
                category_id=category_id,
                label_zh='一',
                label_en='First',
                insert_text='one',
            ),
            _user(),
        )
        await create_tag(
            session,
            PromptTagCreate(
                slug='second',
                category_id=category_id,
                label_zh='二',
                label_en='Second',
                insert_text='two',
            ),
            _user(),
        )

    async with prompt_tag_sessions() as session:
        updated = await update_admin_prompt_tag(
            first.id,
            PromptTagUpdate(insert_text='one updated'),
            _user(),
            session,
        )
    assert updated.insert_text == 'one updated'

    async with prompt_tag_sessions() as session:
        with pytest.raises(HTTPException) as raised:
            await update_admin_prompt_tag(first.id, PromptTagUpdate(slug='second'), _user(), session)
    assert raised.value.status_code == 409

    async with prompt_tag_sessions() as session:
        response = await delete_admin_prompt_tag(first.id, _user(), session)
    assert response.status_code == 204

    async with prompt_tag_sessions() as session:
        with pytest.raises(HTTPException) as raised:
            await delete_admin_prompt_tag(first.id, _user(), session)
    assert raised.value.status_code == 404


@pytest.mark.asyncio
async def test_export_import_roundtrip_through_endpoints(prompt_tag_sessions, tmp_path) -> None:
    category_id = await _seeded_category(prompt_tag_sessions)
    async with prompt_tag_sessions() as session:
        await create_tag(
            session,
            PromptTagCreate(
                slug='exported',
                category_id=category_id,
                label_zh='导出',
                label_en='Exported',
                insert_text='exported text',
            ),
            _user(),
        )
        document = await export_admin_prompt_tags(_user(), session)
    assert isinstance(document, PromptTagExportDocument)
    assert document.categories and document.tags

    # 导入目标是独立空库（fixture 工厂指向导出源库，直接导入必然 slug 冲突）。
    from open_webui.extensions.prompt_tags.db import PromptTagBase
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "import-target.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(PromptTagBase.metadata.create_all)
    import_sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with import_sessions() as session:
            result = await import_admin_prompt_tags(
                PromptTagImportRequest(categories=document.categories, tags=document.tags),
                _user(),
                session,
            )
        assert result.tags_created >= 1

        async with import_sessions() as session:
            with pytest.raises(HTTPException) as raised:
                await import_admin_prompt_tags(
                    PromptTagImportRequest(categories=document.categories, tags=document.tags),
                    _user(),
                    session,
                )
        assert raised.value.status_code == 409
    finally:
        await engine.dispose()


def test_router_prefix_and_no_public_writes() -> None:
    """公开目录只读：非 admin 写端点不得出现在 router 上。"""
    routes = {route.path for route in router_module.router.routes}
    assert '/api/v1/prompt-tags' in routes
    for path in routes:
        assert 'admin' in path or path == '/api/v1/prompt-tags', path
