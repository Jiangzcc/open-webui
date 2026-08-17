from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.videos import router
from open_webui.extensions.videos.catalog import VideoInputError
from open_webui.extensions.videos.schemas import VideoTaskResponse, VideoTaskSubmitForm


def _submission() -> VideoTaskSubmitForm:
    return VideoTaskSubmitForm(
        task='text-to-video',
        model='kling-video-v3-pro',
        prompt='A paper boat',
        assets=(),
        params={'duration': '5'},
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
