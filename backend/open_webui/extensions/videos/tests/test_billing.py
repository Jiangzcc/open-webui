from __future__ import annotations

import pytest
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.videos.billing import (
    video_billing_context,
    video_quote_dimensions,
)
from open_webui.extensions.videos.catalog import VideoInputError
from open_webui.extensions.videos.schemas import VideoTaskResponse


def _task(prompt: str = 'A paper boat crosses a rain puddle') -> VideoTaskResponse:
    return VideoTaskResponse(
        id='task-1',
        status='queued',
        task='text-to-video',
        prompt=prompt,
        model_id='kling-video-v3-pro',
        params={
            'duration': '5',
            'resolution': '1080p',
            'aspect_ratio': '16:9',
            'audio_mode': 'generate',
        },
        assets=(),
        result=None,
        error_code=None,
        created_at=1,
        updated_at=1,
    )


def test_video_billing_context_uses_internal_model_and_normalized_dimensions() -> None:
    context = video_billing_context(_task())

    assert context.service_type == 'video'
    assert context.resource_id == 'fal-ai/kling-video/v3/pro/text-to-video'
    assert context.action == 'text-to-video'
    assert context.channel == 'web'
    assert dict(context.dimensions) == {
        'duration': 5,
        'resolution': '1080p',
        'aspect_ratio': '16:9',
        'audio_mode': 'generate',
    }


def test_video_billing_request_hash_is_stable_and_input_sensitive() -> None:
    first = video_billing_context(_task()).request_hash
    repeated = video_billing_context(_task()).request_hash
    changed = video_billing_context(_task('A paper plane takes off')).request_hash

    assert first == repeated
    assert first != changed
    assert len(first) == 64


def test_video_billing_keeps_auto_duration_as_a_pricing_dimension() -> None:
    task = _task().model_copy(update={'params': {'duration': 'auto'}})

    assert video_billing_context(task).dimensions['duration'] == 'auto'

    match_source_task = _task().model_copy(update={'params': {'duration': '0'}})
    assert video_billing_context(match_source_task).dimensions['duration'] == '0'

    numeric_match_source_task = _task().model_copy(update={'params': {'duration': 0}})
    assert video_billing_context(numeric_match_source_task).dimensions['duration'] == '0'


def test_video_billing_includes_output_dimensions_when_selected() -> None:
    task = _task().model_copy(update={'params': {**_task().params, 'fps': '50', 'output_quality': 'high'}})

    assert dict(video_billing_context(task).dimensions) == {
        'duration': 5,
        'resolution': '1080p',
        'aspect_ratio': '16:9',
        'audio_mode': 'generate',
        'fps': '50',
        'output_quality': 'high',
    }


def test_video_quote_dimensions_matches_billing_context() -> None:
    # 提交前报价预检与运行期计费必须使用同一套维度归一化逻辑，
    # 否则前端报价与实际扣费会产生偏差。
    task = _task().model_copy(update={'params': {**_task().params, 'fps': '50'}})
    assert video_quote_dimensions(task) == dict(video_billing_context(task).dimensions)


def test_mark_video_usage_failed_retries_transient_storage_failure(monkeypatch) -> None:
    from open_webui.extensions.videos import billing

    async def scenario() -> None:
        attempts = 0

        async def fail_then_succeed(*_args, **_kwargs) -> int:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise RuntimeError('database temporarily unavailable')
            return 1

        async def no_wait(_seconds: float) -> None:
            return None

        monkeypatch.setattr(billing, 'mark_usage_failed', fail_then_succeed)
        monkeypatch.setattr(billing.asyncio, 'sleep', no_wait)

        await billing.mark_video_usage_failed('usage-1', 'video_generation_failed')
        assert attempts == 3

    import asyncio

    asyncio.run(scenario())


def test_quote_video_usage_raises_on_unknown_model() -> None:
    from open_webui.extensions.videos.billing import quote_video_usage
    from open_webui.extensions.videos.schemas import VideoTaskSubmitForm

    submission = VideoTaskSubmitForm(
        task='text-to-video',
        model='fal-ai/does-not-exist',
        prompt='x',
        assets=(),
        params={'duration': '5', 'resolution': '1080p', 'aspect_ratio': '16:9', 'audio_mode': 'generate'},
    )

    class _FakeUser:
        id = 'user-1'
        name = 'tester'
        email = 't@example.com'

    with pytest.raises(CreditError) as raised:
        import asyncio

        asyncio.run(quote_video_usage(_FakeUser(), submission))
    assert raised.value.code == 'price_rule_incomplete'


def test_quote_video_usage_rejects_invalid_duration_before_database_access() -> None:
    from open_webui.extensions.videos.billing import quote_video_usage
    from open_webui.extensions.videos.schemas import VideoTaskSubmitForm

    submission = VideoTaskSubmitForm(
        task='text-to-video',
        model='kling-video-v3-pro',
        prompt='x',
        assets=(),
        params={'duration': 'not-a-duration'},
    )

    class _FakeUser:
        id = 'user-1'
        name = 'tester'
        email = 't@example.com'

    with pytest.raises(VideoInputError) as raised:
        import asyncio

        asyncio.run(quote_video_usage(_FakeUser(), submission))
    assert str(raised.value) == 'invalid_duration'
