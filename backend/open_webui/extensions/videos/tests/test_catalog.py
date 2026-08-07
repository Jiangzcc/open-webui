from __future__ import annotations

import pytest
from open_webui.extensions.videos.catalog import (
    VideoInputError,
    build_video_provider_payload,
    public_video_catalog,
    public_video_catalog_for_user,
)
from open_webui.extensions.videos.schemas import VideoTaskSubmitForm


class _ScalarResult:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class _CatalogSession:
    async def scalars(self, _statement):
        return _ScalarResult([])


def test_public_catalog_hides_internal_provider_controls() -> None:
    catalog = public_video_catalog()

    assert catalog['defaults'] == {
        'text-to-video': 'seedance-2.0',
        'image-to-video': 'seedance-2.0/image',
        'video-to-video': 'wan-2.7-video/edit',
    }
    models = catalog['models']
    assert models
    assert {model['provider'] for model in models} >= {
        'alibaba',
        'bytedance',
        'google',
        'kling',
        'ltx',
        'luma',
        'minimax',
        'pika',
        'pixverse',
        'vidu',
    }
    assert all('fixed_fields' not in model and not model['id'].startswith('fal-ai/') for model in models)


@pytest.mark.asyncio
async def test_public_catalog_applies_video_model_operations(monkeypatch) -> None:
    async def decorate(_session, models, *, admin, media_kind):
        assert admin is False
        assert media_kind == 'video'
        return [{**model, 'recommended': index == 0} for index, model in enumerate(models)]

    monkeypatch.setattr('open_webui.extensions.videos.catalog.apply_model_operations', decorate)
    payload = await public_video_catalog_for_user(_CatalogSession())

    assert payload['models'][0]['recommended'] is True


def test_builds_normalized_kling_payload_with_defaults() -> None:
    submission = VideoTaskSubmitForm(
        task='text-to-video',
        model='kling-video-v3-pro',
        prompt='A paper boat crossing a rain puddle',
        params={},
    )

    definition, provider_payload, safe_params = build_video_provider_payload(submission)

    assert definition.id == 'fal-ai/kling-video/v3/pro/text-to-video'
    assert provider_payload == {
        'prompt': submission.prompt,
        'duration': '5',
        'aspect_ratio': '16:9',
        'generate_audio': True,
        'shot_type': 'customize',
        'cfg_scale': 0.5,
    }
    assert safe_params == {
        'duration': '5',
        'aspect_ratio': '16:9',
        'audio_mode': 'generate',
        'shot_type': 'customize',
        'cfg_scale': 0.5,
    }


def test_requires_primary_image_for_image_to_video() -> None:
    submission = VideoTaskSubmitForm(
        task='image-to-video',
        model='seedance-2.0/image',
        prompt='Slow camera orbit',
    )

    with pytest.raises(VideoInputError, match='missing_video_asset:start_image'):
        build_video_provider_payload(submission)


def test_rejects_parameter_not_supported_by_selected_model() -> None:
    submission = VideoTaskSubmitForm(
        task='video-to-video',
        model='kling-video-o3-pro/edit',
        prompt='Add soft snow',
        assets=({'role': 'source_video', 'file_id': 'file-1'},),
        params={'resolution': '1080p'},
    )

    with pytest.raises(VideoInputError, match='unsupported_resolution'):
        build_video_provider_payload(submission)


def test_validates_numeric_duration_range() -> None:
    submission = VideoTaskSubmitForm(
        task='video-to-video',
        model='ltx-2.3/retake',
        prompt='Replace the sky',
        assets=({'role': 'source_video', 'file_id': 'file-1'},),
        params={'duration': '21'},
    )

    with pytest.raises(VideoInputError, match='invalid_duration'):
        build_video_provider_payload(submission)


def test_allows_multiple_reference_images_only_when_catalog_allows_it() -> None:
    submission = VideoTaskSubmitForm(
        task='video-to-video',
        model='kling-video-o3-pro/edit',
        prompt='Use the reference characters',
        assets=(
            {'role': 'source_video', 'file_id': 'source'},
            {'role': 'reference_image', 'file_id': 'ref-1'},
            {'role': 'reference_image', 'file_id': 'ref-2'},
        ),
    )

    definition, _provider_payload, _safe_params = build_video_provider_payload(submission)

    assert definition.task == 'video-to-video'


def test_parses_structured_advanced_parameters_as_json() -> None:
    submission = VideoTaskSubmitForm(
        task='text-to-video',
        model='kling-video-v3-pro',
        params={'multi_prompt': '[{"prompt": "Orbit left", "duration": 3}]'},
    )

    _definition, provider_payload, safe_params = build_video_provider_payload(submission)

    assert provider_payload['multi_prompt'] == [{'prompt': 'Orbit left', 'duration': 3}]
    assert safe_params['multi_prompt'] == provider_payload['multi_prompt']


def test_rejects_malformed_structured_advanced_parameters() -> None:
    submission = VideoTaskSubmitForm(
        task='text-to-video',
        model='kling-video-v3-pro',
        params={'multi_prompt': '[invalid]'},
    )

    with pytest.raises(VideoInputError, match='invalid_multi_prompt'):
        build_video_provider_payload(submission)
