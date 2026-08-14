"""视频执行体 TDD 骨架。

本轮只落测试桩与接口签名；实现待评审通过后单独立项（见
``docs/superpowers/specs/2026-08-14-video-executor-design.md``）。

覆盖范围：
- asset file_id → provider *_url 桥接（image-to-video / video-to-video）。
- 真实执行体落地 ``ProviderInvocation(task_id=task.id)``，闭合 #3 对账缺口。
- fal 视频结果 URL 提取（output_field）。
- 开关与默认 mock（未配置 fal key 时 fail-safe 走 mock，避免误扣费）。
- 错误兜底（VideoExecutionError → mark_video_usage_failed 退费；取消透传）。
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason='video executor design only; implementation is not part of this change')


# ---------------------------------------------------------------------------
# asset → provider URL 桥接
# ---------------------------------------------------------------------------


def test_asset_url_built_from_file_id_via_url_path_for() -> None:
    """asset.file_id 经 url_path_for('get_file_content_by_id') 转成内部 URL。"""
    raise NotImplementedError('video executor not implemented this round')


def test_payload_injects_start_and_end_image_urls_for_image_to_video() -> None:
    """image-to-video：start_image/end_image 的 file_id 注入 definition 声明的字段。"""
    raise NotImplementedError('video executor not implemented this round')


def test_payload_injects_source_video_url_for_video_to_video() -> None:
    """video-to-video：source_video 的 file_id 注入 video_url 字段。"""
    raise NotImplementedError('video executor not implemented this round')


# ---------------------------------------------------------------------------
# provider invocation 落地（对账缺口闭合）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_real_executor_writes_provider_invocation_with_task_id() -> None:
    """真实执行体调用前 try_start_provider_invocation(task_id=task.id) → 对账 task↔invocation 跳闭合。

    这是 #3 视频对账链路的前置依赖：落地前 run_video_task 走 mock，不写 invocation，
    视频对账无从做起。
    """
    raise NotImplementedError('video executor not implemented this round')


# ---------------------------------------------------------------------------
# 视频结果提取
# ---------------------------------------------------------------------------


def test_extract_fal_video_url_from_nested_video_object() -> None:
    """{'video': {'url': '...'}} → 取到 mp4 URL（output_field='video'）。"""
    raise NotImplementedError('video executor not implemented this round')


def test_extract_fal_video_url_falls_back_to_top_level_url() -> None:
    """无 video 键时回退 {'url': '...'}。"""
    raise NotImplementedError('video executor not implemented this round')


def test_extract_fal_video_url_returns_none_on_empty_result() -> None:
    """结果无 URL → None（调用方兜底走 video_generation_failed 退费）。"""
    raise NotImplementedError('video executor not implemented this round')


# ---------------------------------------------------------------------------
# 开关与默认 mock
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_executor_defaults_to_mock_without_fal_key() -> None:
    """未配置 fal key → resolve_video_executor 返回 mock executor（fail-safe，避免误扣费）。"""
    raise NotImplementedError('video executor not implemented this round')


@pytest.mark.asyncio
async def test_resolve_executor_returns_real_when_engine_enabled() -> None:
    """显式开启 real 引擎 + fal key 存在 → 返回 real executor。"""
    raise NotImplementedError('video executor not implemented this round')


# ---------------------------------------------------------------------------
# 错误兜底
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_real_executor_failure_raises_video_execution_error_with_code() -> None:
    """真实调用失败 → 抛 VideoExecutionError(code)，run_video_task 走 mark_video_usage_failed 退费。"""
    raise NotImplementedError('video executor not implemented this round')


@pytest.mark.asyncio
async def test_cancel_propagates_to_fal_queue_run() -> None:
    """服务关停取消 worker → CancelledError 透传到 run_fal_queue，observer 记 failed。"""
    raise NotImplementedError('video executor not implemented this round')
