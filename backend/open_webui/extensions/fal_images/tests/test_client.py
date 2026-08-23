from __future__ import annotations

import asyncio
import re
import types
from types import SimpleNamespace

import pytest
from open_webui.extensions.fal_images.client import (
    FalImageError,
    FalImageSizeError,
    build_fal_image_payload,
    get_mock_fal_image_result,
    resume_fal_queue,
    run_fal_queue,
    validate_fal_image_size,
)


@pytest.mark.parametrize(
    ('form', 'expected_size'),
    [
        (SimpleNamespace(size='1280x720', resolution=None, aspect_ratio='1:1', n=1), (1280, 720)),
        (SimpleNamespace(size=None, resolution='640x960', aspect_ratio='1:1', n=1), (640, 960)),
        (SimpleNamespace(size=None, resolution=None, aspect_ratio='16:9', n=1), (1792, 1024)),
        (SimpleNamespace(size=None, resolution=None, aspect_ratio='9:16', n=1), (1024, 1792)),
        (SimpleNamespace(size=None, resolution='2K', aspect_ratio='4:3', n=1), (2048, 1536)),
        (SimpleNamespace(size=None, resolution='0.5K', aspect_ratio='9:16', n=1), (288, 512)),
        (SimpleNamespace(size=None, resolution=None, aspect_ratio='auto', n=1), (1024, 1024)),
    ],
)
def test_fal_mock_uses_requested_dimensions(form, expected_size) -> None:
    result = get_mock_fal_image_result('fal-ai/z-image/turbo', form)
    assert result is not None
    assert len(result['images']) == 1
    url = result['images'][0]['url']
    match = re.fullmatch(r'https://picsum\.photos/seed/[^/]+/(\d+)/(\d+)', url)
    assert match is not None
    assert tuple(map(int, match.groups())) == expected_size


def test_fal_mock_uses_requested_image_count_and_unique_seeds() -> None:
    form = SimpleNamespace(size='1024x1024', resolution=None, aspect_ratio='1:1', n=4)
    result = get_mock_fal_image_result('fal-ai/z-image/turbo', form)
    assert result is not None
    urls = [image['url'] for image in result['images']]
    assert len(urls) == 4
    assert len(set(urls)) == 4


def _form(**kw):
    base = dict(
        prompt='a cat',
        model='',
        size=None,
        n=1,
        steps=None,
        negative_prompt=None,
        aspect_ratio=None,
        resolution=None,
        output_format=None,
        system_prompt=None,
        seed=None,
        sync_mode=None,
        safety_tolerance=None,
        limit_generations=None,
        enable_web_search=None,
        thinking_level=None,
        enable_safety_checker=None,
        enable_prompt_expansion=None,
        acceleration=None,
        quality=None,
        background=None,
    )
    base.update(kw)
    return types.SimpleNamespace(**base)


def test_payload_qwen_image_sends_num_images_and_image_size_object():
    data = build_fal_image_payload(_form(n=2, size='1024x768'), 'fal-ai/qwen-image')
    assert data['prompt'] == 'a cat'
    assert data['num_images'] == 2
    assert data['image_size'] == {'width': 1024, 'height': 768}


def test_payload_wan_v26_uses_max_images_field():
    data = build_fal_image_payload(_form(n=3), 'wan/v2.6/text-to-image')
    assert data['max_images'] == 3
    assert 'num_images' not in data


def test_payload_wan_v22_does_not_send_count():
    data = build_fal_image_payload(_form(n=1), 'fal-ai/wan/v2.2-5b/text-to-image')
    assert 'num_images' not in data
    assert 'max_images' not in data


def test_payload_wan_v27_supports_five_images():
    data = build_fal_image_payload(_form(n=5), 'fal-ai/wan/v2.7/text-to-image')
    assert data['num_images'] == 5


def test_payload_qwen2_has_no_guidance_or_steps():
    data = build_fal_image_payload(_form(), 'fal-ai/qwen-image-2/text-to-image')
    assert 'guidance_scale' not in data
    assert 'num_inference_steps' not in data
    assert data['enable_safety_checker'] is False
    assert data['enable_prompt_expansion'] is True


def test_payload_z_image_turbo_edit_uses_single_image_contract():
    data = build_fal_image_payload(
        _form(n=2, size='1024x768', steps=8, output_format='webp'),
        'fal-ai/z-image/turbo/image-to-image',
        ['https://example.test/first.png', 'https://example.test/ignored.png'],
    )

    assert data['image_url'] == 'https://example.test/first.png'
    assert 'image_urls' not in data
    assert data['num_images'] == 2
    assert data['num_inference_steps'] == 8
    assert data['image_size'] == {'width': 1024, 'height': 768}
    assert data['output_format'] == 'webp'
    assert data['enable_safety_checker'] is False


def test_custom_size_validation_can_run_before_provider_payload_build(monkeypatch) -> None:
    import open_webui.extensions.fal_images.client as fal

    monkeypatch.setattr(
        fal,
        'FAL_IMAGE_MODELS',
        [
            {
                'id': 'fal-ai/custom-model',
                'custom_size_field': 'image_size',
                'custom_size': {
                    'min_width': 512,
                    'max_width': 2048,
                    'min_height': 512,
                    'max_height': 2048,
                    'multiple_of': 16,
                },
            }
        ],
    )

    validate_fal_image_size('fal-ai/custom-model', _form(size='1024x768'))
    with pytest.raises(FalImageSizeError):
        validate_fal_image_size('fal-ai/custom-model', _form(size='513x768'))
    with pytest.raises(FalImageSizeError):
        validate_fal_image_size('fal-ai/custom-model', _form(size='not-a-size'))


class _FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def json(self, content_type=None):
        return self.payload

    async def text(self):
        return str(self.payload)


class _FakeSession:
    def __init__(self):
        self.status_responses = [
            {'status': 'IN_QUEUE', 'queue_position': 2},
            {'status': 'COMPLETED', 'metrics': {'inference_time': 0.4}},
        ]

    def post(self, *_args, **_kwargs):
        return _FakeResponse(
            {
                'request_id': 'request-1',
                'gateway_request_id': 'gateway-1',
                'status_url': 'https://queue.test/status',
                'response_url': 'https://queue.test/result',
                'cancel_url': 'https://queue.test/cancel',
                'queue_position': 3,
            }
        )

    def get(self, url, **_kwargs):
        if url.endswith('/status'):
            return _FakeResponse(self.status_responses.pop(0))
        return _FakeResponse({'images': [{'url': 'https://example.test/result.png'}]})

    def put(self, *_args, **_kwargs):
        return _FakeResponse({})


class _RecordingObserver:
    def __init__(self):
        self.events = []

    async def submitted(self, payload):
        self.events.append(('submitted', payload))

    async def status(self, payload):
        self.events.append(('status', payload))

    async def succeeded(self):
        self.events.append(('succeeded', None))

    async def failed(self, error):
        self.events.append(('failed', error))


@pytest.mark.asyncio
async def test_fal_queue_reports_submission_status_and_completion(monkeypatch) -> None:
    import open_webui.extensions.fal_images.client as fal

    observer = _RecordingObserver()
    monkeypatch.setattr(fal, 'get_session', lambda: _async_value(_FakeSession()))
    monkeypatch.setattr(fal.asyncio, 'sleep', lambda _seconds: _async_value(None))

    result = await run_fal_queue(
        'fal-ai/example',
        {'prompt': 'test'},
        'secret',
        'https://queue.test',
        observer=observer,
    )

    assert result['images'][0]['url'] == 'https://example.test/result.png'
    assert [event[0] for event in observer.events] == ['submitted', 'status', 'status', 'succeeded']
    assert observer.events[0][1]['request_id'] == 'request-1'
    assert observer.events[2][1]['metrics']['inference_time'] == 0.4


@pytest.mark.asyncio
async def test_fal_queue_preserves_completed_state_when_result_fetch_fails(monkeypatch) -> None:
    import open_webui.extensions.fal_images.client as fal

    class Session(_FakeSession):
        def get(self, url, **_kwargs):
            if url.endswith('/status'):
                return _FakeResponse({'status': 'COMPLETED'})
            return _FakeResponse({'detail': 'temporary response failure'}, status=503)

    monkeypatch.setattr(fal, 'get_session', lambda: _async_value(Session()))

    with pytest.raises(FalImageError) as captured:
        await run_fal_queue(
            'fal-ai/example',
            {'prompt': 'test'},
            'secret',
            'https://queue.test',
        )

    assert captured.value.status_code == 503
    assert captured.value.provider_submitted is True
    assert captured.value.provider_completed is True


@pytest.mark.asyncio
async def test_fal_queue_cancels_remote_request_when_worker_is_cancelled(monkeypatch) -> None:
    import open_webui.extensions.fal_images.client as fal

    cancelled_urls: list[str] = []

    class Session(_FakeSession):
        def put(self, url, **_kwargs):
            cancelled_urls.append(url)
            return _FakeResponse({})

    async def cancel_during_poll(_seconds):
        raise asyncio.CancelledError

    observer = _RecordingObserver()
    monkeypatch.setattr(fal, 'get_session', lambda: _async_value(Session()))
    monkeypatch.setattr(fal.asyncio, 'sleep', cancel_during_poll)

    with pytest.raises(asyncio.CancelledError) as captured:
        await run_fal_queue(
            'fal-ai/example',
            {'prompt': 'test'},
            'secret',
            'https://queue.test',
            observer=observer,
        )

    assert cancelled_urls == ['https://queue.test/cancel']
    assert captured.value.provider_submitted is True
    assert captured.value.provider_completed is False
    assert [event[0] for event in observer.events] == ['submitted', 'status', 'failed']


@pytest.mark.asyncio
async def test_resume_fal_queue_only_polls_and_fetches_existing_response(monkeypatch) -> None:
    import open_webui.extensions.fal_images.client as fal

    class Session(_FakeSession):
        def post(self, *_args, **_kwargs):
            raise AssertionError('resume must not submit another request')

    observer = _RecordingObserver()
    monkeypatch.setattr(fal, 'get_session', lambda: _async_value(Session()))
    monkeypatch.setattr(fal.asyncio, 'sleep', lambda _seconds: _async_value(None))

    result = await resume_fal_queue(
        status_url='https://queue.test/status',
        response_url='https://queue.test/result',
        api_key='secret',
        observer=observer,
    )

    assert result['images'][0]['url'] == 'https://example.test/result.png'
    assert [event[0] for event in observer.events] == ['status', 'status', 'succeeded']


@pytest.mark.asyncio
async def test_resume_fal_queue_preserves_completed_state_on_response_failure(monkeypatch) -> None:
    import open_webui.extensions.fal_images.client as fal

    class Session(_FakeSession):
        def get(self, url, **_kwargs):
            if url.endswith('/status'):
                return _FakeResponse({'status': 'COMPLETED'})
            return _FakeResponse({'detail': 'temporary response failure'}, status=503)

    monkeypatch.setattr(fal, 'get_session', lambda: _async_value(Session()))

    with pytest.raises(FalImageError) as captured:
        await resume_fal_queue(
            status_url='https://queue.test/status',
            response_url='https://queue.test/result',
            api_key='secret',
        )

    assert captured.value.provider_submitted is True
    assert captured.value.provider_completed is True


async def _async_value(value):
    return value
