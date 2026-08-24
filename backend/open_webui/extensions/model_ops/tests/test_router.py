"""model_ops 路由层测试。

覆盖 admin 端点鉴权、GET /admin/models 数据返回、PATCH 更新操作。

使用 FastAPI TestClient + 依赖覆盖，不依赖真实数据库连接。
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from open_webui.extensions.model_ops.models import ImageModelOperation
from open_webui.extensions.model_ops.router import router as model_ops_router
from open_webui.internal.db import get_async_session
from open_webui.utils.auth import get_admin_user
from sqlalchemy.ext.asyncio import AsyncSession

from .conftest import make_user

# 真实目录中的模型 ID
IMAGE_MODEL_INTERNAL = 'fal-ai/ideogram/v2'
IMAGE_MODEL_PUBLIC = 'ideogram-v2'
VIDEO_MODEL_INTERNAL = 'fal-ai/ltx-2.3/text-to-video'
VIDEO_MODEL_PUBLIC = 'ltx-2.3'


def _build_app(router_database, *, admin_user=None) -> tuple[FastAPI, TestClient]:
    """构建带依赖覆盖的 FastAPI 应用和 TestClient。

    参数:
        router_database: 异步会话工厂（async_sessionmaker）
        admin_user: 传入则覆盖 get_admin_user 返回该用户；
                    传 None 则不覆盖（模拟未认证请求）。
    """
    app = FastAPI()
    app.include_router(model_ops_router)

    async def _session_override() -> AsyncIterator[AsyncSession]:
        async with router_database() as session:
            yield session

    app.dependency_overrides[get_async_session] = _session_override

    if admin_user is not None:
        app.dependency_overrides[get_admin_user] = lambda: admin_user

    return app, TestClient(app)


def _seed_operation(
    router_database,
    *,
    model_id: str,
    visible: bool = True,
    enabled: bool = True,
    recommended: bool = False,
    sort_order: int = 1000,
    tags_json: list[str] | None = None,
    maintenance_message: str | None = None,
    updated_at: int = 100,
) -> None:
    """向测试数据库插入一条 ImageModelOperation 记录。"""

    async def _go():
        async with router_database() as session, session.begin():
            session.add(
                ImageModelOperation(
                    model_id=model_id,
                    visible=visible,
                    enabled=enabled,
                    recommended=recommended,
                    sort_order=sort_order,
                    tags_json=tags_json or [],
                    maintenance_message=maintenance_message,
                    updated_at=updated_at,
                )
            )

    asyncio.run(_go())


# ---------------------------------------------------------------------------
# 鉴权测试
# ---------------------------------------------------------------------------


class TestAdminAuth:
    """验证 admin 端点要求管理员鉴权。"""

    def test_non_admin_get_models_returns_401(self, router_database) -> None:
        # 覆盖 get_admin_user 使其抛出 401，模拟非管理员访问
        app = FastAPI()
        app.include_router(model_ops_router)

        async def _session_override() -> AsyncIterator[AsyncSession]:
            async with router_database() as session:
                yield session

        def _reject():
            raise HTTPException(status_code=401, detail='Access prohibited')

        app.dependency_overrides[get_async_session] = _session_override
        app.dependency_overrides[get_admin_user] = _reject

        response = TestClient(app).get('/api/v1/media-model-ops/admin/models')
        assert response.status_code == 401

    def test_non_admin_patch_model_returns_401(self, router_database) -> None:
        app = FastAPI()
        app.include_router(model_ops_router)

        async def _session_override() -> AsyncIterator[AsyncSession]:
            async with router_database() as session:
                yield session

        def _reject():
            raise HTTPException(status_code=401, detail='Access prohibited')

        app.dependency_overrides[get_async_session] = _session_override
        app.dependency_overrides[get_admin_user] = _reject

        response = TestClient(app).patch(
            f'/api/v1/media-model-ops/admin/models/{IMAGE_MODEL_PUBLIC}',
            json={'visible': False},
        )
        assert response.status_code == 401

    def test_admin_user_can_access_models(self, router_database) -> None:
        # 管理员可以正常访问
        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.get('/api/v1/media-model-ops/admin/models')
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /admin/models
# ---------------------------------------------------------------------------


class TestGetAdminModels:
    """验证 GET /admin/models 返回正确的模型操作数据。"""

    def test_returns_all_catalog_models_with_defaults(self, router_database) -> None:
        # 没有操作记录时，所有目录模型返回默认值
        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.get('/api/v1/media-model-ops/admin/models')
        assert response.status_code == 200

        data = response.json()
        assert 'items' in data
        assert len(data['items']) > 0

        # 应包含图片和视频模型
        media_kinds = {item['media_kind'] for item in data['items']}
        assert 'image' in media_kinds
        assert 'video' in media_kinds

    def test_reflects_stored_operation_fields(self, router_database) -> None:
        # 操作记录中的字段被正确反映到返回数据中
        _seed_operation(
            router_database,
            model_id=IMAGE_MODEL_INTERNAL,
            visible=False,
            enabled=False,
            recommended=True,
            sort_order=5,
            tags_json=['hot', 'new'],
            maintenance_message='维护说明',
            updated_at=999,
        )

        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.get('/api/v1/media-model-ops/admin/models')
        assert response.status_code == 200

        items = response.json()['items']
        item = next(i for i in items if i['model_id'] == IMAGE_MODEL_INTERNAL)

        assert item['visible'] is False
        assert item['enabled'] is False
        assert item['recommended'] is True
        assert item['sort_order'] == 5
        assert item['tags'] == ['hot', 'new']
        assert item['maintenance_message'] == '维护说明'
        assert item['updated_at'] == 999
        assert item['media_kind'] == 'image'
        assert item['public_id'] == IMAGE_MODEL_PUBLIC

    def test_items_are_sorted_by_recommended_then_sort_order(self, router_database) -> None:
        # recommended=True 排在前面，然后按 sort_order 排序
        _seed_operation(
            router_database,
            model_id=IMAGE_MODEL_INTERNAL,
            recommended=True,
            sort_order=100,
        )
        _seed_operation(
            router_database,
            model_id='fal-ai/ideogram/v2/turbo',
            recommended=False,
            sort_order=50,
        )

        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.get('/api/v1/media-model-ops/admin/models')
        assert response.status_code == 200

        items = response.json()['items']
        ideogram_idx = next(
            i for i, item in enumerate(items) if item['model_id'] == IMAGE_MODEL_INTERNAL
        )
        turbo_idx = next(
            i for i, item in enumerate(items) if item['model_id'] == 'fal-ai/ideogram/v2/turbo'
        )

        # recommended=True (sort_order=100) 应排在 recommended=False (sort_order=50) 前面
        assert ideogram_idx < turbo_idx


# ---------------------------------------------------------------------------
# PATCH /admin/models/{model_id}
# ---------------------------------------------------------------------------


class TestPatchAdminModel:
    """验证 PATCH /admin/models/{model_id} 更新模型操作。"""

    def test_patch_creates_operation_and_returns_item(self, router_database) -> None:
        # 操作记录不存在时，PATCH 创建新行并返回
        admin = make_user(user_id='admin-1', name='管理员', role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.patch(
            f'/api/v1/media-model-ops/admin/models/{IMAGE_MODEL_PUBLIC}',
            json={'visible': False, 'recommended': True, 'sort_order': 5},
        )

        assert response.status_code == 200
        item = response.json()
        assert item['model_id'] == IMAGE_MODEL_INTERNAL
        assert item['visible'] is False
        assert item['recommended'] is True
        assert item['sort_order'] == 5
        # enabled 未在请求中设置，使用默认值 True
        assert item['enabled'] is True

        # 验证数据库中确实创建了行
        async def _check():
            async with router_database() as session:
                row = await session.get(ImageModelOperation, IMAGE_MODEL_INTERNAL)
            return row

        row = asyncio.run(_check())
        assert row is not None
        assert row.visible is False
        assert row.recommended is True
        assert row.sort_order == 5
        assert row.updated_by_id == 'admin-1'
        assert row.updated_by_name_snapshot == '管理员'

    def test_patch_partial_update_preserves_unset_fields(self, router_database) -> None:
        # 先创建一条操作记录
        _seed_operation(
            router_database,
            model_id=IMAGE_MODEL_INTERNAL,
            visible=True,
            enabled=True,
            recommended=True,
            sort_order=10,
            tags_json=['original'],
            maintenance_message='原始消息',
            updated_at=100,
        )

        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        # 只更新 visible，其他字段不动
        response = client.patch(
            f'/api/v1/media-model-ops/admin/models/{IMAGE_MODEL_PUBLIC}',
            json={'visible': False},
        )

        assert response.status_code == 200
        item = response.json()
        assert item['visible'] is False
        assert item['enabled'] is True
        assert item['recommended'] is True
        assert item['sort_order'] == 10
        assert item['tags'] == ['original']
        assert item['maintenance_message'] == '原始消息'

    def test_patch_updates_tags(self, router_database) -> None:
        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.patch(
            f'/api/v1/media-model-ops/admin/models/{IMAGE_MODEL_PUBLIC}',
            json={'tags': ['featured', 'new', 'featured']},
        )

        assert response.status_code == 200
        item = response.json()
        # 去重后的标签
        assert item['tags'] == ['featured', 'new']

    def test_patch_unknown_model_returns_404(self, router_database) -> None:
        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.patch(
            '/api/v1/media-model-ops/admin/models/nonexistent-model-id',
            json={'visible': False},
        )

        assert response.status_code == 404
        assert response.json()['detail'] == 'image model not found'

    def test_patch_empty_body_returns_422(self, router_database) -> None:
        # 至少需要一个字段
        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.patch(
            f'/api/v1/media-model-ops/admin/models/{IMAGE_MODEL_PUBLIC}',
            json={},
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /admin/media-models/{media_kind}/{model_id}
# ---------------------------------------------------------------------------


class TestPatchMediaModel:
    """验证 PATCH /admin/media-models/{media_kind}/{model_id} 端点。"""

    def test_patch_video_model(self, router_database) -> None:
        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.patch(
            f'/api/v1/media-model-ops/admin/media-models/video/{VIDEO_MODEL_PUBLIC}',
            json={'visible': False},
        )

        assert response.status_code == 200
        item = response.json()
        assert item['media_kind'] == 'video'
        assert item['model_id'] == VIDEO_MODEL_INTERNAL
        assert item['visible'] is False

        # 验证存储键使用了 video: 前缀
        async def _check():
            async with router_database() as session:
                row = await session.get(
                    ImageModelOperation, f'video:{VIDEO_MODEL_INTERNAL}'
                )
            return row

        row = asyncio.run(_check())
        assert row is not None
        assert row.visible is False

    def test_patch_image_model_via_media_endpoint(self, router_database) -> None:
        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.patch(
            f'/api/v1/media-model-ops/admin/media-models/image/{IMAGE_MODEL_PUBLIC}',
            json={'enabled': False, 'maintenance_message': '维护中'},
        )

        assert response.status_code == 200
        item = response.json()
        assert item['media_kind'] == 'image'
        assert item['enabled'] is False
        assert item['maintenance_message'] == '维护中'

    def test_patch_unknown_video_model_returns_404(self, router_database) -> None:
        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.patch(
            '/api/v1/media-model-ops/admin/media-models/video/nonexistent-model',
            json={'visible': False},
        )

        assert response.status_code == 404
        assert response.json()['detail'] == 'video model not found'

    def test_patch_invalid_media_kind_returns_422(self, router_database) -> None:
        admin = make_user(role='admin')
        _, client = _build_app(router_database, admin_user=admin)

        response = client.patch(
            '/api/v1/media-model-ops/admin/media-models/audio/some-model',
            json={'visible': False},
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 路由注册验证
# ---------------------------------------------------------------------------


def test_router_exposes_expected_routes() -> None:
    """验证路由注册了预期的端点。"""
    routes = {
        (route.path, next(iter(route.methods - {'HEAD'})))
        for route in model_ops_router.routes
    }

    assert routes == {
        ('/api/v1/media-model-ops/admin/models', 'GET'),
        ('/api/v1/media-model-ops/admin/models/{model_id:path}', 'PATCH'),
        ('/api/v1/media-model-ops/admin/media-models/{media_kind}/{model_id:path}', 'PATCH'),
    }
