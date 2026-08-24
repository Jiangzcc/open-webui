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
from open_webui.extensions.tests.http_test_support import AsyncJsonResponse as _FakeResponse


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


def test_payload_ratio_models_map_aspect_ratio_to_image_size():
    data = build_fal_image_payload(_form(n=1, aspect_ratio='4:3'), 'fal-ai/z-image/turbo')
    assert data['image_size'] == {'width': 1024, 'height': 768}


def test_payload_seedream_scales_resolution_tier_over_baseline():
    base = 'bytedance/seedream/v5/pro/text-to-image'
    data_1k = build_fal_image_payload(_form(aspect_ratio='4:3', resolution='1K'), base)
    data_2k = build_fal_image_payload(_form(aspect_ratio='4:3', resolution='2K'), base)
    data_4k = build_fal_image_payload(_form(aspect_ratio='16:9', resolution='4K'), base)
    assert data_1k['image_size'] == {'width': 1024, 'height': 768}
    assert data_2k['image_size'] == {'width': 2048, 'height': 1536}
    assert data_4k['image_size'] == {'width': 5120, 'height': 2880}


def test_payload_wxh_resolution_takes_precedence_over_explicit_size():
    """'WxH' 形态的 resolution 是最显式的尺寸声明，优先于显式 size（与计价、resolution_field 同源）。"""
    base = 'bytedance/seedream/v5/pro/text-to-image'
    data = build_fal_image_payload(
        _form(size='512x512', resolution='1024x1024', aspect_ratio='1:1'), base
    )
    assert data['image_size'] == {'width': 1024, 'height': 1024}


def test_payload_resolution_tier_does_not_scale_explicit_size():
    """档位只放大比例基线，不覆盖显式 size：自定义尺寸始终按原值生效。"""
    base = 'bytedance/seedream/v5/pro/text-to-image'
    data = build_fal_image_payload(
        _form(size='1024x1024', resolution='4K', aspect_ratio='1:1'), base
    )
    assert data['image_size'] == {'width': 1024, 'height': 1024}


def test_validate_fal_image_size_accepts_resolution_tier_without_explicit_size():
    """direct API 只传档位（无 size）不再被误判为非法尺寸（复盘 P0-2 的 422 拒绝缺陷）。"""
    base = 'bytedance/seedream/v5/pro/text-to-image'
    validate_fal_image_size(base, _form(resolution='2K', aspect_ratio='4:3'))
    validate_fal_image_size(base, _form(resolution='4K'))


def test_validate_fal_image_size_checks_tier_scaled_final_size(monkeypatch) -> None:
    """档位请求校验的是折算后的最终尺寸（基线 × 乘数），而非基线本身。"""
    import open_webui.extensions.fal_images.client as fal

    monkeypatch.setattr(
        fal,
        'FAL_IMAGE_MODELS',
        [
            {
                'id': 'fal-ai/tier-model',
                'custom_size_field': 'image_size',
                'aspect_ratio_sizes': {'1:1': '1024x1024'},
                'resolution_multipliers': {'4K': 4},
                'custom_size': {'max_pixels': 4_000_000},
            }
        ],
    )

    fal.validate_fal_image_size('fal-ai/tier-model', _form(resolution='2K', aspect_ratio='1:1'))
    with pytest.raises(FalImageSizeError):
        fal.validate_fal_image_size('fal-ai/tier-model', _form(resolution='4K', aspect_ratio='1:1'))


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


class _CompletedThenFailingSession(_FakeSession):
    def get(self, url, **_kwargs):
        if url.endswith('/status'):
            return _FakeResponse({'status': 'COMPLETED'})
        return _FakeResponse({'detail': 'temporary response failure'}, status=503)


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
    import open_webui.extensions.fal_images.queue_client as fal

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
    import open_webui.extensions.fal_images.queue_client as fal

    monkeypatch.setattr(fal, 'get_session', lambda: _async_value(_CompletedThenFailingSession()))

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
async def test_fal_queue_never_sends_key_to_cross_origin_response_url(monkeypatch) -> None:
    import open_webui.extensions.fal_images.queue_client as fal

    requested: list[str] = []

    class Session(_FakeSession):
        def post(self, *_args, **_kwargs):
            return _FakeResponse(
                {
                    'request_id': 'request-1',
                    'response_url': 'https://attacker.example/result',
                }
            )

        def get(self, url, **_kwargs):
            requested.append(url)
            raise AssertionError('cross-origin URL must be rejected before GET')

    monkeypatch.setattr(fal, 'get_session', lambda: _async_value(Session()))

    with pytest.raises(FalImageError, match='invalid queue URL') as captured:
        await run_fal_queue('fal-ai/example', {'prompt': 'test'}, 'secret', 'https://queue.test')

    assert requested == []
    assert captured.value.provider_submitted is True


@pytest.mark.asyncio
async def test_resume_fal_queue_rejects_cross_origin_urls_before_session_lookup(monkeypatch) -> None:
    import open_webui.extensions.fal_images.queue_client as fal

    async def forbidden_session():
        raise AssertionError('invalid recovery URL must fail before session lookup')

    monkeypatch.setattr(fal, 'get_session', forbidden_session)
    with pytest.raises(FalImageError, match='invalid queue URL'):
        await resume_fal_queue(
            status_url=None,
            response_url='https://attacker.example/result',
            api_key='secret',
            base_url='https://queue.test',
        )


@pytest.mark.asyncio
async def test_fal_queue_cancels_remote_request_when_worker_is_cancelled(monkeypatch) -> None:
    import open_webui.extensions.fal_images.queue_client as fal

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
    import open_webui.extensions.fal_images.queue_client as fal

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
        base_url='https://queue.test',
        observer=observer,
    )

    assert result['images'][0]['url'] == 'https://example.test/result.png'
    assert [event[0] for event in observer.events] == ['status', 'status', 'succeeded']


@pytest.mark.asyncio
async def test_resume_fal_queue_preserves_completed_state_on_response_failure(monkeypatch) -> None:
    import open_webui.extensions.fal_images.queue_client as fal

    monkeypatch.setattr(fal, 'get_session', lambda: _async_value(_CompletedThenFailingSession()))

    with pytest.raises(FalImageError) as captured:
        await resume_fal_queue(
            status_url='https://queue.test/status',
            response_url='https://queue.test/result',
            api_key='secret',
            base_url='https://queue.test',
        )

    assert captured.value.provider_submitted is True
    assert captured.value.provider_completed is True


async def _async_value(value):
    return value


@pytest.mark.asyncio
async def test_resume_fal_queue_notifies_observer_failed_on_cancel(monkeypatch) -> None:
    """复盘 P1：恢复路径取消也要通知 observer failed（与 run_fal_queue
    对齐），否则关停取消时 provider_invocation 行停留无终态。"""
    import open_webui.extensions.fal_images.queue_client as fal

    async def cancel_during_poll(_seconds):
        raise asyncio.CancelledError

    observer = _RecordingObserver()
    monkeypatch.setattr(fal, 'get_session', lambda: _async_value(_FakeSession()))
    monkeypatch.setattr(fal.asyncio, 'sleep', cancel_during_poll)

    with pytest.raises(asyncio.CancelledError):
        await resume_fal_queue(
            status_url='https://queue.test/status',
            response_url='https://queue.test/result',
            api_key='secret',
            base_url='https://queue.test',
            observer=observer,
        )

    assert [event[0] for event in observer.events] == ['status', 'failed']


def test_payload_helper_edges_cover_invalid_and_optional_values() -> None:
    import open_webui.extensions.fal_images.client as client

    assert client._get_fal_model_info(None) is None
    assert client._get_fal_model_info('missing') is None
    assert client._safe_option('bad', ['good'], 'good') == 'good'
    assert client._safe_option('value', None, None) == 'value'
    assert client._safe_count(0, None) is None
    assert client._safe_count(2, [1]) is None
    assert client._parse_pixel_size(123) is None
    assert client._parse_pixel_size('bad') is None
    assert client._validate_custom_size(0, 1, None) is not None
    assert client._validate_custom_size(10, 10, None) is None

    data = {}
    client._set_option(data, None, 'value', None, None)
    client._set_option(data, 'max_image_size', '2', ['2'], None)
    assert data == {'max_image_size': 2}
    client._set_image_input(data, 'image_url', [], None)
    client._set_image_input(data, 'image_url', ['one', 'two'], 1)
    client._set_image_input(data, 'image_urls', ['one', 'two'], 1)
    assert data['image_url'] == 'one'
    assert data['image_urls'] == ['one']

    form = _form(flag=None, steps=99, scale=True, note='  text  ')
    client._set_option_fields(data, form, [{'field': None}, {'field': 'quality', 'default': 'high'}])
    client._set_boolean_fields(data, form, [{'field': None}, {'field': 'flag', 'default': True}])
    client._set_integer_fields(data, form, [{'field': None}, {'field': 'steps', 'max': 10}])
    client._set_number_fields(data, form, [{'field': None}, {'field': 'scale'}])
    client._set_text_fields(data, form, [{'field': None}, {'field': 'note'}])
    assert data['flag'] is True
    assert data['note'] == 'text'


def test_mock_sizes_unknown_payloads_and_result_url_shapes(monkeypatch) -> None:
    import open_webui.extensions.fal_images.client as client

    assert client._mock_named_resolution_size(None, None) is None
    assert client._mock_named_resolution_size('bad', None) is None
    assert client._mock_named_resolution_size('2K', None) == (2048, 2048)
    assert client._mock_named_resolution_size('2K', '16:9') == (2048, 1152)
    assert client._mock_named_resolution_size('2K', '9:16') == (1152, 2048)
    assert client._mock_image_size(_form(size='640x480')) == (640, 480)
    assert client._mock_image_size(_form(size='0x0', aspect_ratio='16:9')) == client.FAL_MOCK_ASPECT_RATIO_SIZES['16:9']

    monkeypatch.setattr(client.random, 'getrandbits', lambda _bits: 7)
    result = client.get_mock_fal_image_result('model', _form(size='640x480', n=2))
    assert len(result['images']) == 2
    assert result['seed'] == '7-0'

    unknown = SimpleNamespace(
        prompt='Prompt',
        n=2,
        aspect_ratio='1:1',
        resolution='1K',
        output_format=None,
        system_prompt='System',
    )
    payload = client.build_fal_image_payload(unknown, 'unknown', ['one'])
    assert payload['image_urls'] == ['one']
    assert payload['output_format'] == 'png'

    assert client.extract_fal_image_urls({'data': {'image': {'url': 'one'}, 'url': 'two'}}) == ['one', 'two']
    assert client.extract_fal_image_urls(['one', {'url': 'two'}, {'bad': True}, 3]) == ['one', 'two']
    assert client.extract_fal_image_urls(None) == []
