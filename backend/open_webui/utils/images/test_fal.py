from __future__ import annotations

import re
import types
from types import SimpleNamespace

import pytest
from open_webui.utils.images.fal import (
    FalImageSizeError,
    build_fal_image_payload,
    get_mock_fal_image_result,
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
    import open_webui.utils.images.fal as fal

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
