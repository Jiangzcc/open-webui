from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.videos import router
from open_webui.extensions.videos.catalog import VideoInputError
from open_webui.extensions.videos.executor import VideoExecutionError
from open_webui.extensions.videos.schemas import VideoTaskResponse, VideoTaskSubmitForm
from open_webui.extensions.videos.service import build_video_provider_payload


def _submission() -> VideoTaskSubmitForm:
    return VideoTaskSubmitForm(
        task='text-to-video',
        model='kling-video-v3-pro',
        prompt='A paper boat',
        assets=(),
        params={'duration': '5'},
    )


def _submission_with_params() -> VideoTaskSubmitForm:
    # 带负向提示词参数的提交体：prompt 是用户输入的纯文本
    # （标签点击时已直接插入 insert_text）。
    return VideoTaskSubmitForm(
        task='text-to-video',
        model='kling-video-v3-pro',
        prompt='A paper boat, cinematic lighting',
        assets=(),
        params={'duration': '5', 'negative_prompt': 'black and white, blurry'},
    )


def _task() -> VideoTaskResponse:
    return VideoTaskResponse(
        id='task-1',
        status='running',
        task='text-to-video',
        prompt='A paper boat',
        model_id='kling-video-v3-pro',
        params={'duration': '5'},
        assets=(),
        result=None,
        error_code=None,
        created_at=1,
        updated_at=1,
    )


def test_video_router_has_no_user_cancel_endpoint() -> None:
    assert not any(route.path.endswith('/cancel') for route in router.router.routes)


def test_idempotent_retry_returns_existing_before_admission_checks(monkeypatch) -> None:
    async def scenario() -> None:
        existing = _task()

        async def ensure_enabled(*_args, **_kwargs) -> None:
            return None

        async def get_existing(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return existing

        monkeypatch.setattr(router, 'ensure_model_enabled', ensure_enabled)
        monkeypatch.setattr(router, 'get_video_task_by_idempotency_key', get_existing)
        monkeypatch.setattr(router, 'video_task_matches_submission', lambda *_args: True)
        monkeypatch.setattr(
            router,
            'enforce_video_generation_rate',
            lambda *_args: (_ for _ in ()).throw(AssertionError('rate limit should not run')),
        )

        result = await router.submit_video_task(
            SimpleNamespace(),
            _submission(),
            'same-key',
            SimpleNamespace(id='user-1'),
            object(),
            object(),
        )

        assert result is existing

    asyncio.run(scenario())


def test_idempotency_key_reuse_with_different_payload_returns_conflict(monkeypatch) -> None:
    async def scenario() -> None:
        async def ensure_enabled(*_args, **_kwargs) -> None:
            return None

        async def get_existing(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return _task()

        monkeypatch.setattr(router, 'ensure_model_enabled', ensure_enabled)
        monkeypatch.setattr(router, 'get_video_task_by_idempotency_key', get_existing)
        monkeypatch.setattr(router, 'video_task_matches_submission', lambda *_args: False)

        response = await router.submit_video_task(
            SimpleNamespace(),
            _submission(),
            'reused-key',
            SimpleNamespace(id='user-1'),
            object(),
            object(),
        )

        assert response.status_code == 409
        assert b'idempotency_key_conflict' in response.body

    asyncio.run(scenario())


def test_invalid_quote_input_maps_to_422_before_slot_acquisition(monkeypatch) -> None:
    async def scenario() -> None:
        async def ensure_enabled(*_args, **_kwargs) -> None:
            return None

        async def no_existing(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return None

        async def invalid_quote(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise VideoInputError('invalid_duration')

        async def unexpected_acquire(*_args, **_kwargs) -> None:
            raise AssertionError('slot should not be acquired')

        monkeypatch.setattr(router, 'ensure_model_enabled', ensure_enabled)
        monkeypatch.setattr(router, 'get_video_task_by_idempotency_key', no_existing)
        monkeypatch.setattr(router, 'enforce_video_generation_rate', lambda *_args: None)
        monkeypatch.setattr(router, 'quote_video_usage', invalid_quote)
        monkeypatch.setattr(router, 'acquire_video_generation_slot', unexpected_acquire)

        response = await router.submit_video_task(
            SimpleNamespace(),
            _submission(),
            'new-key',
            SimpleNamespace(id='user-1'),
            object(),
            object(),
        )

        assert response.status_code == 422
        assert b'invalid_duration' in response.body

    asyncio.run(scenario())


def test_insufficient_credits_returns_envelope_with_code(monkeypatch) -> None:
    """修复 5：CreditError 响应体从 {'detail': code, 'reason': context} 改为 to_envelope()
    （{'code', 'message', 'context'}），前端需要读取 code/message 而非 detail。"""

    async def scenario() -> None:
        async def ensure_enabled(*_args, **_kwargs) -> None:
            return None

        async def no_existing(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return None

        async def insufficient_quote(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise CreditError(code='insufficient_credits', context={'required': 100})

        monkeypatch.setattr(router, 'ensure_model_enabled', ensure_enabled)
        monkeypatch.setattr(router, 'get_video_task_by_idempotency_key', no_existing)
        monkeypatch.setattr(router, 'enforce_video_generation_rate', lambda *_args: None)
        monkeypatch.setattr(router, 'quote_video_usage', insufficient_quote)

        response = await router.submit_video_task(
            SimpleNamespace(),
            _submission(),
            'new-key',
            SimpleNamespace(id='user-1'),
            object(),
            object(),
        )

        assert response.status_code == 402
        body = json.loads(response.body)
        assert body['code'] == 'insufficient_credits'
        assert body['message'] == 'Insufficient credits'
        assert 'detail' not in body

    asyncio.run(scenario())


def test_plain_submission_reaches_executor_boundary(monkeypatch) -> None:
    """纯文本提交（含带负向提示词参数）能通过输入校验，到达 executor
    解析边界。"""

    async def scenario() -> None:
        async def ensure_enabled(*_args, **_kwargs) -> None:
            return None

        async def no_existing(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return None

        monkeypatch.setattr(router, 'ensure_model_enabled', ensure_enabled)
        monkeypatch.setattr(router, 'get_video_task_by_idempotency_key', no_existing)
        # 让后续步骤直接短路返回：到达此处即证明提交通过了输入校验。
        monkeypatch.setattr(
            router,
            'resolve_video_executor',
            lambda *_args, **_kwargs: (_ for _ in ()).throw(VideoExecutionError(code='video_executor_unavailable')),
        )

        response = await router.submit_video_task(
            SimpleNamespace(),
            _submission_with_params(),
            'new-key',
            SimpleNamespace(id='user-1'),
            object(),
            object(),
        )

        assert response.status_code == 503
        assert b'video_executor_unavailable' in response.body

    asyncio.run(scenario())


def test_tag_placeholder_retry_matches_token_stored_task(monkeypatch) -> None:
    """任务落库的是 token 形态（审查发现 #1 的现行保障形态）：重放比较
    token 对 token，含 token prompt 的同键重试不再需要展开即可命中，
    不会被误判为 409 idempotency_key_conflict。"""

    async def scenario() -> None:
        submission = _submission_with_params()
        # 落库形态：token 提示词 + token 形态的 safe params（含模型默认值）。
        _definition, _provider_payload, safe_params = build_video_provider_payload(submission)
        stored_task = VideoTaskResponse(
            id='task-1',
            status='running',
            task='text-to-video',
            prompt=submission.prompt,
            model_id='kling-video-v3-pro',
            params=safe_params,
            assets=(),
            result=None,
            error_code=None,
            created_at=1,
            updated_at=1,
        )

        async def ensure_enabled(*_args, **_kwargs) -> None:
            return None

        async def get_existing(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return stored_task

        monkeypatch.setattr(router, 'ensure_model_enabled', ensure_enabled)
        monkeypatch.setattr(router, 'get_video_task_by_idempotency_key', get_existing)
        # 不 stub video_task_matches_submission：使用真实比较函数，验证重放
        # 比较在 token 形态下直接命中（重放路径在解析之前，无需标签库）。

        result = await router.submit_video_task(
            SimpleNamespace(),
            submission,
            'same-key',
            SimpleNamespace(id='user-1'),
            object(),
            object(),
        )

        assert result is stored_task

    asyncio.run(scenario())


def test_tag_placeholder_retry_with_different_prompt_returns_conflict(monkeypatch) -> None:
    """同键重试但 token 提示词不同（换了标签或自由文本）必须按 409 冲突
    处理，而不是静默返回内容不同的旧任务。"""

    async def scenario() -> None:
        submission = _submission_with_params()
        _definition, _provider_payload, safe_params = build_video_provider_payload(submission)
        stored_task = VideoTaskResponse(
            id='task-1',
            status='running',
            task='text-to-video',
            prompt=submission.prompt,
            model_id='kling-video-v3-pro',
            params=safe_params,
            assets=(),
            result=None,
            error_code=None,
            created_at=1,
            updated_at=1,
        )

        async def ensure_enabled(*_args, **_kwargs) -> None:
            return None

        async def get_existing(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return stored_task

        monkeypatch.setattr(router, 'ensure_model_enabled', ensure_enabled)
        monkeypatch.setattr(router, 'get_video_task_by_idempotency_key', get_existing)

        changed = submission.model_copy(update={'prompt': 'A paper boat, soft diffused lighting'})
        response = await router.submit_video_task(
            SimpleNamespace(),
            changed,
            'same-key',
            SimpleNamespace(id='user-1'),
            object(),
            object(),
        )

        assert response.status_code == 409
        assert b'idempotency_key_conflict' in response.body

    asyncio.run(scenario())


def test_delete_video_task_rejects_active_task(monkeypatch) -> None:
    """复盘 #9：进行中/待恢复任务删除会让 worker 照常扣费并产生孤儿
    媒体记录，必须与图片端一样返回 409。"""

    async def scenario() -> None:
        async def get_running_task(*_args, **_kwargs):
            return _task()

        async def unexpected_delete(*_args, **_kwargs):
            raise AssertionError('active task must not be deleted')

        monkeypatch.setattr(router, 'get_video_task', get_running_task)
        monkeypatch.setattr(router, 'delete_video_task', unexpected_delete)

        with pytest.raises(HTTPException) as raised:
            await router.remove_video_task('task-1', SimpleNamespace(id='user-1'), object())

        assert raised.value.status_code == 409

    asyncio.run(scenario())


def test_delete_video_task_allows_terminal_task(monkeypatch) -> None:
    async def scenario() -> None:
        finished = _task().model_copy(update={'status': 'failed'})
        deleted: list[str] = []

        async def get_finished_task(*_args, **_kwargs):
            return finished

        async def do_delete(_session, _user_id, task_id) -> bool:
            deleted.append(task_id)
            return True

        monkeypatch.setattr(router, 'get_video_task', get_finished_task)
        monkeypatch.setattr(router, 'delete_video_task', do_delete)

        await router.remove_video_task('task-1', SimpleNamespace(id='user-1'), object())

        assert deleted == ['task-1']

    asyncio.run(scenario())
