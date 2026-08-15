"""model_ops 服务层测试。

覆盖 apply_model_operations、ensure_model_enabled、_operation_key、
list_model_operations、update_model_operation 以及 tags 去重/长度限制。

使用临时 SQLite 文件和真实 fal 目录数据，不依赖真实数据库连接。
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from open_webui.extensions.model_ops.models import ImageModelOperation
from open_webui.extensions.model_ops.schemas import ModelOperationUpdate
from open_webui.extensions.model_ops.service import (
    _operation_key,
    apply_model_operations,
    ensure_model_enabled,
    list_model_operations,
    update_model_operation,
)
from pydantic import ValidationError

from .conftest import make_user

# ---------------------------------------------------------------------------
# 真实目录中的模型 ID（来自 fal_catalog/catalog/image 和 catalog/video）
# ---------------------------------------------------------------------------

# 图片模型：内部 ID 与公开 ID
IMAGE_MODEL_INTERNAL = 'fal-ai/ideogram/v2'
IMAGE_MODEL_PUBLIC = 'ideogram-v2'
IMAGE_MODEL_TURBO_INTERNAL = 'fal-ai/ideogram/v2/turbo'
IMAGE_MODEL_TURBO_PUBLIC = 'ideogram-v2-turbo'

# 视频模型：内部 ID 与公开 ID
VIDEO_MODEL_INTERNAL = 'fal-ai/ltx-2.3/text-to-video'
VIDEO_MODEL_PUBLIC = 'ltx-2.3'


# ---------------------------------------------------------------------------
# _operation_key
# ---------------------------------------------------------------------------


class TestOperationKey:
    """验证 _operation_key 能正确区分图片和视频模型的存储键。"""

    def test_image_kind_returns_model_id_unchanged(self) -> None:
        # 图片模型不加前缀，直接使用内部 ID 作为存储键
        assert _operation_key('image', IMAGE_MODEL_INTERNAL) == IMAGE_MODEL_INTERNAL

    def test_video_kind_prefixes_with_video_colon(self) -> None:
        # 视频模型加 video: 前缀，避免与同名的图片模型存储键冲突
        assert _operation_key('video', VIDEO_MODEL_INTERNAL) == f'video:{VIDEO_MODEL_INTERNAL}'

    def test_image_and_video_with_same_model_id_do_not_collide(self) -> None:
        # 即使图片和视频模型碰巧有相同的内部 ID，存储键也不会冲突
        shared_id = 'fal-ai/shared/model'
        assert _operation_key('image', shared_id) != _operation_key('video', shared_id)
        assert _operation_key('video', shared_id) == f'video:{shared_id}'


# ---------------------------------------------------------------------------
# apply_model_operations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_model_operations_hides_invisible_models_for_non_admin(
    model_ops_sessions,
) -> None:
    """隐藏模型对非管理员用户不可见，对管理员可见且带 visible=False 标记。"""
    async with model_ops_sessions() as session:
        # 为 ideogram-v2 创建一条 visible=False 的操作记录
        session.add(
            ImageModelOperation(
                model_id=IMAGE_MODEL_INTERNAL,
                visible=False,
                enabled=True,
                recommended=False,
                sort_order=1000,
                tags_json=[],
                maintenance_message=None,
                updated_at=100,
            )
        )
        await session.commit()

    models = [
        {'id': IMAGE_MODEL_PUBLIC, 'name': 'Ideogram v2'},
        {'id': IMAGE_MODEL_TURBO_PUBLIC, 'name': 'Ideogram v2 Turbo'},
    ]

    # 非管理员：隐藏模型被过滤掉
    async with model_ops_sessions() as session:
        result = await apply_model_operations(session, models, admin=False)
    ids = [item['id'] for item in result]
    assert IMAGE_MODEL_PUBLIC not in ids
    assert IMAGE_MODEL_TURBO_PUBLIC in ids

    # 管理员：隐藏模型仍然可见，但 visible=False
    async with model_ops_sessions() as session:
        result = await apply_model_operations(session, models, admin=True)
    hidden = next(item for item in result if item['id'] == IMAGE_MODEL_PUBLIC)
    assert hidden['visible'] is False
    assert hidden['enabled'] is True


@pytest.mark.asyncio
async def test_apply_model_operations_recommended_sorts_before_non_recommended(
    model_ops_sessions,
) -> None:
    """recommended=True 的模型排在 recommended=False 的模型前面，即使 sort_order 更大。"""
    async with model_ops_sessions() as session:
        session.add(
            ImageModelOperation(
                model_id=IMAGE_MODEL_INTERNAL,
                visible=True,
                enabled=True,
                recommended=True,
                sort_order=100,
                tags_json=[],
                maintenance_message=None,
                updated_at=100,
            )
        )
        session.add(
            ImageModelOperation(
                model_id=IMAGE_MODEL_TURBO_INTERNAL,
                visible=True,
                enabled=True,
                recommended=False,
                sort_order=50,
                tags_json=[],
                maintenance_message=None,
                updated_at=100,
            )
        )
        await session.commit()

    models = [
        {'id': IMAGE_MODEL_TURBO_PUBLIC, 'name': 'Turbo'},
        {'id': IMAGE_MODEL_PUBLIC, 'name': 'v2'},
    ]

    async with model_ops_sessions() as session:
        result = await apply_model_operations(session, models, admin=False)

    # recommended=True 的 v2 应排在 recommended=False 的 Turbo 前面
    assert result[0]['id'] == IMAGE_MODEL_PUBLIC
    assert result[0]['recommended'] is True
    assert result[1]['id'] == IMAGE_MODEL_TURBO_PUBLIC
    assert result[1]['recommended'] is False


@pytest.mark.asyncio
async def test_apply_model_operations_decorates_with_operation_fields(model_ops_sessions) -> None:
    """操作记录中的字段被正确附加到模型字典上。"""
    async with model_ops_sessions() as session:
        session.add(
            ImageModelOperation(
                model_id=IMAGE_MODEL_INTERNAL,
                visible=True,
                enabled=False,
                recommended=True,
                sort_order=42,
                tags_json=['featured', 'new'],
                maintenance_message='维护中',
                updated_at=200,
            )
        )
        await session.commit()

    models = [{'id': IMAGE_MODEL_PUBLIC, 'name': 'Ideogram v2'}]

    async with model_ops_sessions() as session:
        result = await apply_model_operations(session, models, admin=False)

    item = result[0]
    assert item['visible'] is True
    assert item['enabled'] is False
    assert item['recommended'] is True
    assert item['sort_order'] == 42
    assert item['tags'] == ['featured', 'new']
    assert item['maintenance_message'] == '维护中'


@pytest.mark.asyncio
async def test_apply_model_operations_defaults_when_no_operation_exists(model_ops_sessions) -> None:
    """没有操作记录的模型使用默认值：visible=True, enabled=True, recommended=False, sort_order=1000。"""
    models = [{'id': IMAGE_MODEL_PUBLIC, 'name': 'Ideogram v2'}]

    async with model_ops_sessions() as session:
        result = await apply_model_operations(session, models, admin=False)

    item = result[0]
    assert item['visible'] is True
    assert item['enabled'] is True
    assert item['recommended'] is False
    assert item['sort_order'] == 1000
    assert item['tags'] == []
    assert item['maintenance_message'] is None


# ---------------------------------------------------------------------------
# ensure_model_enabled
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_model_enabled_raises_503_for_disabled_model(model_ops_sessions) -> None:
    """禁用模型触发 HTTPException(503)，detail 包含 code 和 maintenance_message。"""
    async with model_ops_sessions() as session:
        session.add(
            ImageModelOperation(
                model_id=IMAGE_MODEL_INTERNAL,
                visible=True,
                enabled=False,
                recommended=False,
                sort_order=1000,
                tags_json=[],
                maintenance_message='模型升级中，预计 2 小时后恢复',
                updated_at=100,
            )
        )
        await session.commit()

    async with model_ops_sessions() as session:
        with pytest.raises(HTTPException) as exc_info:
            await ensure_model_enabled(session, IMAGE_MODEL_PUBLIC, media_kind='image')

    assert exc_info.value.status_code == 503
    detail = exc_info.value.detail
    assert detail['code'] == 'image_model_unavailable'
    assert detail['message'] == '模型升级中，预计 2 小时后恢复'


@pytest.mark.asyncio
async def test_ensure_model_enabled_passes_when_model_enabled(model_ops_sessions) -> None:
    """启用状态的模型不触发错误。"""
    async with model_ops_sessions() as session:
        session.add(
            ImageModelOperation(
                model_id=IMAGE_MODEL_INTERNAL,
                visible=True,
                enabled=True,
                recommended=False,
                sort_order=1000,
                tags_json=[],
                maintenance_message=None,
                updated_at=100,
            )
        )
        await session.commit()

    async with model_ops_sessions() as session:
        # 不应抛出异常
        await ensure_model_enabled(session, IMAGE_MODEL_PUBLIC, media_kind='image')


@pytest.mark.asyncio
async def test_ensure_model_enabled_passes_when_no_operation_exists(model_ops_sessions) -> None:
    """没有操作记录的模型默认启用，不触发错误。"""
    async with model_ops_sessions() as session:
        await ensure_model_enabled(session, IMAGE_MODEL_PUBLIC, media_kind='image')


@pytest.mark.asyncio
async def test_ensure_model_enabled_passes_for_unknown_model_id(model_ops_sessions) -> None:
    """无法解析的模型 ID 视为无需检查，不触发错误。"""
    async with model_ops_sessions() as session:
        await ensure_model_enabled(session, 'nonexistent-model-id', media_kind='image')


@pytest.mark.asyncio
async def test_ensure_model_enabled_raises_503_for_disabled_video_model(model_ops_sessions) -> None:
    """禁用的视频模型触发 HTTPException(503)，detail code 使用 video 前缀。"""
    async with model_ops_sessions() as session:
        session.add(
            ImageModelOperation(
                model_id=f'video:{VIDEO_MODEL_INTERNAL}',
                visible=True,
                enabled=False,
                recommended=False,
                sort_order=1000,
                tags_json=[],
                maintenance_message='视频模型维护中',
                updated_at=100,
            )
        )
        await session.commit()

    async with model_ops_sessions() as session:
        with pytest.raises(HTTPException) as exc_info:
            await ensure_model_enabled(session, VIDEO_MODEL_PUBLIC, media_kind='video')

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail['code'] == 'video_model_unavailable'


# ---------------------------------------------------------------------------
# list_model_operations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_model_operations_returns_all_catalog_models_with_defaults(
    model_ops_sessions,
) -> None:
    """没有操作记录时，所有目录模型返回默认值。"""
    async with model_ops_sessions() as session:
        result = await list_model_operations(session)

    # 结果应包含图片和视频目录中的所有模型
    assert len(result.items) > 0

    # 验证至少包含我们知道的模型
    model_ids = {item.model_id for item in result.items}
    assert IMAGE_MODEL_INTERNAL in model_ids
    assert VIDEO_MODEL_INTERNAL in model_ids

    # 验证默认值
    ideogram = next(item for item in result.items if item.model_id == IMAGE_MODEL_INTERNAL)
    assert ideogram.visible is True
    assert ideogram.enabled is True
    assert ideogram.recommended is False
    assert ideogram.sort_order == 1000
    assert ideogram.tags == ()
    assert ideogram.maintenance_message is None
    assert ideogram.updated_at is None
    assert ideogram.media_kind == 'image'

    video_model = next(item for item in result.items if item.model_id == VIDEO_MODEL_INTERNAL)
    assert video_model.media_kind == 'video'


@pytest.mark.asyncio
async def test_list_model_operations_sorts_recommended_before_non_recommended(
    model_ops_sessions,
) -> None:
    """recommended=True 的模型排在 recommended=False 的前面，即使 sort_order 更大。"""
    async with model_ops_sessions() as session:
        session.add(
            ImageModelOperation(
                model_id=IMAGE_MODEL_INTERNAL,
                visible=True,
                enabled=True,
                recommended=True,
                sort_order=100,
                tags_json=[],
                maintenance_message=None,
                updated_at=100,
            )
        )
        session.add(
            ImageModelOperation(
                model_id=IMAGE_MODEL_TURBO_INTERNAL,
                visible=True,
                enabled=True,
                recommended=False,
                sort_order=50,
                tags_json=[],
                maintenance_message=None,
                updated_at=100,
            )
        )
        await session.commit()

    async with model_ops_sessions() as session:
        result = await list_model_operations(session)

    items = result.items
    ideogram_idx = next(i for i, item in enumerate(items) if item.model_id == IMAGE_MODEL_INTERNAL)
    turbo_idx = next(i for i, item in enumerate(items) if item.model_id == IMAGE_MODEL_TURBO_INTERNAL)

    # recommended=True (sort_order=100) 应排在 recommended=False (sort_order=50) 前面
    assert ideogram_idx < turbo_idx
    assert items[ideogram_idx].recommended is True
    assert items[turbo_idx].recommended is False


@pytest.mark.asyncio
async def test_list_model_operations_reflects_stored_operations(model_ops_sessions) -> None:
    """操作记录中的字段被正确反映到列表项中。"""
    async with model_ops_sessions() as session:
        session.add(
            ImageModelOperation(
                model_id=IMAGE_MODEL_INTERNAL,
                visible=False,
                enabled=False,
                recommended=True,
                sort_order=5,
                tags_json=['hot', 'recommended'],
                maintenance_message='维护说明',
                updated_at=999,
            )
        )
        await session.commit()

    async with model_ops_sessions() as session:
        result = await list_model_operations(session)

    item = next(i for i in result.items if i.model_id == IMAGE_MODEL_INTERNAL)
    assert item.visible is False
    assert item.enabled is False
    assert item.recommended is True
    assert item.sort_order == 5
    assert item.tags == ('hot', 'recommended')
    assert item.maintenance_message == '维护说明'
    assert item.updated_at == 999


# ---------------------------------------------------------------------------
# update_model_operation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_model_operation_partial_update_preserves_unset_fields(
    model_ops_sessions,
) -> None:
    """PATCH 部分更新：只修改传入的字段，未设置的字段保持不变。"""
    async with model_ops_sessions() as session:
        session.add(
            ImageModelOperation(
                model_id=IMAGE_MODEL_INTERNAL,
                visible=True,
                enabled=True,
                recommended=True,
                sort_order=10,
                tags_json=['original'],
                maintenance_message='原始消息',
                updated_at=100,
            )
        )
        await session.commit()

    operator = make_user(user_id='admin-1', name='管理员')

    # 只更新 visible=False，其他字段不动
    async with model_ops_sessions() as session:
        item = await update_model_operation(
            session,
            IMAGE_MODEL_PUBLIC,
            ModelOperationUpdate(visible=False),
            operator,
            media_kind='image',
        )

    assert item is not None
    assert item.visible is False
    # 未设置的字段保持原值
    assert item.enabled is True
    assert item.recommended is True
    assert item.sort_order == 10
    assert item.tags == ('original',)
    assert item.maintenance_message == '原始消息'

    # 验证数据库中的行也只更新了 visible
    async with model_ops_sessions() as session:
        row = await session.get(ImageModelOperation, IMAGE_MODEL_INTERNAL)
    assert row is not None
    assert row.visible is False
    assert row.enabled is True
    assert row.recommended is True
    assert row.sort_order == 10
    assert row.tags_json == ['original']
    assert row.maintenance_message == '原始消息'
    assert row.updated_by_id == 'admin-1'
    assert row.updated_by_name_snapshot == '管理员'
    assert row.updated_at > 100  # updated_at 被刷新


@pytest.mark.asyncio
async def test_update_model_operation_creates_row_when_not_exists(model_ops_sessions) -> None:
    """操作记录不存在时，update 会创建新行并应用传入的变更。"""
    operator = make_user()

    async with model_ops_sessions() as session:
        item = await update_model_operation(
            session,
            IMAGE_MODEL_PUBLIC,
            ModelOperationUpdate(visible=False, recommended=True, sort_order=5),
            operator,
            media_kind='image',
        )

    assert item is not None
    assert item.visible is False
    # enabled 未在 form 中设置，使用新建行的默认值 True
    assert item.enabled is True
    assert item.recommended is True
    assert item.sort_order == 5

    # 验证数据库中确实创建了行
    async with model_ops_sessions() as session:
        row = await session.get(ImageModelOperation, IMAGE_MODEL_INTERNAL)
    assert row is not None
    assert row.visible is False
    assert row.enabled is True
    assert row.recommended is True


@pytest.mark.asyncio
async def test_update_model_operation_returns_none_for_unknown_model(model_ops_sessions) -> None:
    """目录中不存在的模型 ID 返回 None。"""
    operator = make_user()

    async with model_ops_sessions() as session:
        item = await update_model_operation(
            session,
            'nonexistent-model-id',
            ModelOperationUpdate(visible=False),
            operator,
            media_kind='image',
        )

    assert item is None


@pytest.mark.asyncio
async def test_update_model_operation_supports_video_kind(model_ops_sessions) -> None:
    """media_kind='video' 时，操作记录使用 video: 前缀存储键。"""
    operator = make_user()

    async with model_ops_sessions() as session:
        item = await update_model_operation(
            session,
            VIDEO_MODEL_PUBLIC,
            ModelOperationUpdate(visible=False),
            operator,
            media_kind='video',
        )

    assert item is not None
    assert item.media_kind == 'video'
    assert item.visible is False
    assert item.model_id == VIDEO_MODEL_INTERNAL

    # 验证存储键使用了 video: 前缀
    async with model_ops_sessions() as session:
        row = await session.get(ImageModelOperation, f'video:{VIDEO_MODEL_INTERNAL}')
    assert row is not None
    assert row.visible is False


# ---------------------------------------------------------------------------
# tags 去重和长度限制（schema 层验证）
# ---------------------------------------------------------------------------


class TestTagsNormalization:
    """验证 ModelOperationUpdate 的 tags 字段验证器。"""

    def test_tags_deduplication_preserves_order(self) -> None:
        # 重复的标签按首次出现顺序去重
        form = ModelOperationUpdate(tags=('a', 'b', 'a', 'c', 'b'))
        assert form.tags == ('a', 'b', 'c')

    def test_tags_strips_whitespace(self) -> None:
        # 标签首尾空白被去除
        form = ModelOperationUpdate(tags=('  hello  ', 'world'))
        assert form.tags == ('hello', 'world')

    def test_tags_filters_empty_strings(self) -> None:
        # 去除空白后为空的标签被过滤掉
        form = ModelOperationUpdate(tags=('a', '', '  ', 'b'))
        assert form.tags == ('a', 'b')

    def test_tags_strips_and_deduplicates_combined(self) -> None:
        # 去空白和去重组合工作
        form = ModelOperationUpdate(tags=(' a ', 'a', ' b ', 'b'))
        assert form.tags == ('a', 'b')

    def test_tags_reject_more_than_twelve_entries(self) -> None:
        # 超过 12 个标签触发验证错误（max_length=12 在标准化前检查）
        with pytest.raises(ValidationError):
            ModelOperationUpdate(tags=tuple(f'tag-{i}' for i in range(13)))

    def test_tags_allows_exactly_twelve_entries(self) -> None:
        # 恰好 12 个标签通过验证
        form = ModelOperationUpdate(tags=tuple(f'tag-{i}' for i in range(12)))
        assert len(form.tags) == 12

    def test_tags_rejects_individual_tag_longer_than_32_chars(self) -> None:
        # 单个标签超过 32 字符触发验证错误
        with pytest.raises(ValidationError) as exc_info:
            ModelOperationUpdate(tags=('a' * 33,))
        assert 'too long' in str(exc_info.value)

    def test_tags_allows_individual_tag_of_exactly_32_chars(self) -> None:
        # 恰好 32 字符的标签通过验证
        form = ModelOperationUpdate(tags=('a' * 32,))
        assert form.tags == ('a' * 32,)

    def test_tags_none_leaves_field_unset(self) -> None:
        # tags=None 表示不更新该字段，但 require_change 验证器要求至少一个字段
        with pytest.raises(ValidationError):
            ModelOperationUpdate()

    def test_empty_update_rejected(self) -> None:
        # 至少需要设置一个字段
        with pytest.raises(ValidationError):
            ModelOperationUpdate()


# ---------------------------------------------------------------------------
# maintenance_message 标准化
# ---------------------------------------------------------------------------


class TestMaintenanceMessageNormalization:
    """验证 maintenance_message 字段的空白处理。"""

    def test_strips_whitespace(self) -> None:
        form = ModelOperationUpdate(maintenance_message='  维护中  ')
        assert form.maintenance_message == '维护中'

    def test_empty_string_becomes_none(self) -> None:
        # 空白字符串标准化为 None
        form = ModelOperationUpdate(maintenance_message='   ')
        assert form.maintenance_message is None

    def test_none_value_is_valid(self) -> None:
        form = ModelOperationUpdate(maintenance_message=None)
        assert form.maintenance_message is None


# ---------------------------------------------------------------------------
# sort_order 边界
# ---------------------------------------------------------------------------


class TestSortOrderValidation:
    """验证 sort_order 字段的范围约束。"""

    def test_rejects_negative_value(self) -> None:
        with pytest.raises(ValidationError):
            ModelOperationUpdate(sort_order=-1)

    def test_rejects_value_over_100000(self) -> None:
        with pytest.raises(ValidationError):
            ModelOperationUpdate(sort_order=100001)

    def test_allows_zero(self) -> None:
        form = ModelOperationUpdate(sort_order=0)
        assert form.sort_order == 0

    def test_allows_max_value(self) -> None:
        form = ModelOperationUpdate(sort_order=100000)
        assert form.sort_order == 100000
