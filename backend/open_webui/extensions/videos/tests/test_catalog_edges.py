from types import SimpleNamespace

import pytest
from open_webui.extensions.fal_catalog.tests.model_test_support import (
    video_definition as _definition,
)
from open_webui.extensions.fal_catalog.video_schemas import (
    VideoAssetInput,
    VideoBooleanField,
    VideoIntegerField,
    VideoJsonField,
    VideoNumberField,
    VideoOptionField,
    VideoTextField,
)
from open_webui.extensions.videos import catalog
from open_webui.extensions.videos.schemas import VideoAssetReference, VideoTaskSubmitForm


def test_public_duration_and_model_resolution_edges(monkeypatch) -> None:
    assert catalog._public_advanced_value('enabled', 'prompt_enhancement') == 'on'
    assert catalog._duration_pricing_is_proportional(None) is False
    assert catalog._duration_pricing_is_proportional({'dimensions': None}) is False
    enriched = catalog._enriched_video_model(
        {'id': 'model', 'task': 'text-to-video', 'durations': ['auto']},
        SimpleNamespace(public_to_internal={'model': 'internal'}),
        {},
        {('internal', 'text-to-video'): {'dimensions': [{'key': 'duration', 'kind': 'proportional'}]}},
    )
    assert enriched['durations'] == ['auto']

    monkeypatch.setattr(
        catalog,
        'load_video_catalog_cached',
        lambda: SimpleNamespace(public_to_internal={}, definitions=[]),
    )
    with pytest.raises(catalog.VideoInputError, match='unknown'):
        catalog.resolve_video_model('missing')


def test_primary_audio_and_freeform_duration_validation() -> None:
    payload = {}
    with pytest.raises(catalog.VideoInputError, match='unsupported'):
        catalog._set_supported_option(
            payload,
            {'duration': '5'},
            public_key='duration',
            field=None,
            options=None,
            default=None,
        )
    catalog._set_supported_option(
        payload,
        {},
        public_key='duration',
        field='duration',
        options=['5'],
        default=None,
    )
    with pytest.raises(catalog.VideoInputError, match='invalid'):
        catalog._set_supported_option(
            payload,
            {'duration': 5},
            public_key='duration',
            field='duration',
            options=['5'],
            default=None,
        )

    definition = _definition(duration_field='duration', duration_min=2, duration_max=4)
    with pytest.raises(catalog.VideoInputError, match='duration'):
        catalog._validate_freeform_duration(definition, {'duration': 'bad'})
    with pytest.raises(catalog.VideoInputError, match='duration'):
        catalog._validate_freeform_duration(definition, {'duration': 1})

    definition = _definition()
    catalog._apply_audio_mode(definition, {}, {}, {})
    with pytest.raises(catalog.VideoInputError, match='audio'):
        catalog._apply_audio_mode(definition, {'audio_mode': 'silent'}, {}, {})


def test_dynamic_field_validation_rejects_each_invalid_type() -> None:
    fields_and_values = (
        (VideoOptionField(field='choice', options=['a']), 'b'),
        (VideoBooleanField(field='flag'), 'true'),
        (VideoIntegerField(field='count', min=1), True),
        (VideoNumberField(field='scale'), float('inf')),
        (VideoTextField(field='text', max_length=1), 'too long'),
        (VideoJsonField(field='config'), 'invalid'),
        (VideoJsonField(field='config'), '1'),
    )
    for field, value in fields_and_values:
        with pytest.raises(catalog.VideoInputError):
            catalog._validated_dynamic_value(field, value, field.field)

    boolean = VideoBooleanField(field='prompt_expansion', source='prompt_expansion')
    with pytest.raises(catalog.VideoInputError):
        catalog._normalize_prompt_enhancement(
            boolean,
            'auto',
            'prompt_enhancement',
            'prompt_enhancement',
        )


def test_dynamic_and_asset_submission_conflicts() -> None:
    controlled = VideoBooleanField(field='safety_tolerance', default=False)
    with pytest.raises(catalog.VideoInputError, match='unsupported'):
        catalog._apply_dynamic_field(controlled, {'safety_tolerance': True}, {}, {})

    required_json = VideoJsonField(field='config', required=True)
    with pytest.raises(catalog.VideoInputError, match='missing'):
        catalog._apply_dynamic_field(required_json, {}, {}, {})

    asset = VideoAssetInput(
        role='start_image',
        field='image_url',
        required=True,
        mime_types=['image/png'],
        max_bytes=10,
    )
    definition = _definition(task='image-to-video', asset_inputs=[asset])
    with pytest.raises(catalog.VideoInputError, match='missing'):
        catalog._validate_submitted_assets(
            definition,
            VideoTaskSubmitForm(task='image-to-video', model='model'),
        )
    with pytest.raises(catalog.VideoInputError, match='unsupported'):
        catalog._validate_submitted_assets(
            definition,
            VideoTaskSubmitForm(
                task='image-to-video',
                model='model',
                assets=(VideoAssetReference(role='end_image', file_id='file'),),
            ),
        )


def test_payload_builder_rejects_task_prompt_and_unknown_parameter(monkeypatch) -> None:
    definition = _definition()
    monkeypatch.setattr(catalog, 'resolve_video_model', lambda _model: definition)
    with pytest.raises(catalog.VideoInputError, match='mismatch'):
        catalog.build_video_provider_payload(
            VideoTaskSubmitForm(task='image-to-video', model='model', prompt='prompt')
        )
    with pytest.raises(catalog.VideoInputError, match='prompt'):
        catalog.build_video_provider_payload(
            VideoTaskSubmitForm(task='text-to-video', model='model')
        )
    with pytest.raises(catalog.VideoInputError, match='unsupported'):
        catalog.build_video_provider_payload(
            VideoTaskSubmitForm(
                task='text-to-video',
                model='model',
                prompt='prompt',
                params={'unknown': True},
            )
        )
