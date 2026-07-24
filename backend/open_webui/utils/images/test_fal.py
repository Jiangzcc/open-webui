from __future__ import annotations

import re
from types import SimpleNamespace

import pytest
from open_webui.utils.images.fal import get_mock_fal_image_result


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
