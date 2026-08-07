from __future__ import annotations

from open_webui.extensions.videos.billing import video_billing_context
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
