from __future__ import annotations

from types import SimpleNamespace

import pytest
from open_webui.extensions.fal_catalog.loader import load_video_catalog
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


class _PriceSession:
    """Fake async session that returns CreditPrice rows for the price query.

    apply_model_operations is monkeypatched to a passthrough so the only
    behavior under test is the catalog's own enrichment/filtering.
    """

    def __init__(self, prices):
        self._prices = prices

    async def scalars(self, statement):
        return _ScalarResult(self._prices)


@pytest.mark.asyncio
async def test_public_catalog_hides_auto_duration_for_proportional_pricing(monkeypatch) -> None:
    """按秒（proportional）计费的视频模型无法解析 'auto' 时长：proportional 规则
    用 unit_size 缩放，pricing._resolve_proportional 经 _positive_decimal 解析，
    'auto' 非数值→None→compute_price 抛 price_rule_incomplete→报价 configured=False。
    目录层必须隐藏 'auto' 并把 default_duration 重置为具体秒数，否则用户默认进入
    即看到"积分未配置"，而模型名后却显示有价——前后矛盾。"""
    catalog = load_video_catalog()
    internal_id = next(definition.id for definition in catalog.definitions if definition.public_id == 'seedance-2.0')
    proportional_rules = {
        'schema_version': 1,
        'dimensions': [{'key': 'duration', 'kind': 'proportional', 'unit_size': '1'}],
    }
    prices = [
        SimpleNamespace(
            service_type='video',
            resource_id=internal_id,
            action='text-to-video',
            base_price='16.8',
            rules=proportional_rules,
            enabled=True,
        )
    ]

    async def passthrough(_session, models, *, admin, media_kind):
        return [dict(model) for model in models]

    monkeypatch.setattr('open_webui.extensions.videos.catalog.apply_model_operations', passthrough)
    payload = await public_video_catalog_for_user(_PriceSession(prices))

    seedance = next(model for model in payload['models'] if model['id'] == 'seedance-2.0')
    assert seedance['base_price'] == '16.8'
    assert 'auto' not in seedance['durations']
    assert seedance['default_duration'] == '4'


@pytest.mark.asyncio
async def test_public_catalog_keeps_auto_duration_when_not_proportional(monkeypatch) -> None:
    """非按秒计费（如 unit_blocks 或无 duration 维度）的模型仍应保留 'auto'，
    过滤只针对 proportional。"""
    catalog = load_video_catalog()
    internal_id = next(definition.id for definition in catalog.definitions if definition.public_id == 'seedance-2.0')
    unit_blocks_rules = {
        'schema_version': 1,
        'dimensions': [{'key': 'duration', 'kind': 'unit_blocks', 'block_size': '5', 'multiplier_per_block': '1'}],
    }
    prices = [
        SimpleNamespace(
            service_type='video',
            resource_id=internal_id,
            action='text-to-video',
            base_price='600',
            rules=unit_blocks_rules,
            enabled=True,
        )
    ]

    async def passthrough(_session, models, *, admin, media_kind):
        return [dict(model) for model in models]

    monkeypatch.setattr('open_webui.extensions.videos.catalog.apply_model_operations', passthrough)
    payload = await public_video_catalog_for_user(_PriceSession(prices))

    seedance = next(model for model in payload['models'] if model['id'] == 'seedance-2.0')
    assert 'auto' in seedance['durations']
    assert seedance['default_duration'] == 'auto'


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
    assert all(
        field['key'] not in {'safety_tolerance', 'auto_fix'}
        for model in models
        for field in model.get('advanced_fields', [])
    )
    assert all(
        key not in model
        for model in models
        for key in (
            'option_fields',
            'boolean_fields',
            'integer_fields',
            'number_fields',
            'text_fields',
            'json_fields',
        )
    )
    assert all(model['id'] != 'pixverse/c1/reference-to-video' for model in models)

    wan = next(model for model in models if model['id'] == 'wan-2.7-video')
    assert wan['advanced_fields'] == [
        {'key': 'seed', 'kind': 'integer'},
        {'key': 'negative_prompt', 'kind': 'text', 'max_length': 2500},
        {'key': 'prompt_enhancement', 'kind': 'option', 'options': ['on', 'off'], 'default': 'on'},
    ]


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
        'guidance_scale': 0.5,
    }


def test_maps_canonical_advanced_parameters_to_provider_fields() -> None:
    submission = VideoTaskSubmitForm(
        task='text-to-video',
        model='wan-2.7-video',
        prompt='A quiet lake at dawn',
        params={
            'seed': 0,
            'negative_prompt': 'flicker',
            'prompt_enhancement': 'off',
        },
    )

    _definition, provider_payload, safe_params = build_video_provider_payload(submission)

    assert provider_payload['seed'] == 0
    assert provider_payload['negative_prompt'] == 'flicker'
    assert provider_payload['enable_prompt_expansion'] is False
    assert safe_params['prompt_enhancement'] == 'off'


def test_rejects_conflicting_canonical_and_legacy_advanced_parameters() -> None:
    submission = VideoTaskSubmitForm(
        task='text-to-video',
        model='wan-2.7-video',
        prompt='A quiet lake at dawn',
        params={'prompt_enhancement': 'off', 'enable_prompt_expansion': True},
    )

    with pytest.raises(VideoInputError, match='conflicting_video_parameter:prompt_enhancement'):
        build_video_provider_payload(submission)


def test_keeps_video_safety_and_auto_fix_server_controlled() -> None:
    submission = VideoTaskSubmitForm(
        task='text-to-video',
        model='veo3.1',
        prompt='A lighthouse in a storm',
        params={'safety_tolerance': '6'},
    )

    with pytest.raises(VideoInputError, match='unsupported_video_parameter:safety_tolerance'):
        build_video_provider_payload(submission)

    default_submission = submission.model_copy(update={'params': {}})
    _definition, provider_payload, safe_params = build_video_provider_payload(default_submission)
    assert provider_payload['safety_tolerance'] == '4'
    # veo3.1 文本生成视频的 auto_fix 目录默认值为 True（与所有 text-to-video 模型一致），
    # 服务端仍完全控制该字段——用户无法通过 params 传入，只能使用目录默认值。
    assert provider_payload['auto_fix'] is True
    assert 'safety_tolerance' not in safe_params
    assert 'auto_fix' not in safe_params


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
