import pytest
from open_webui.extensions.fal_catalog.schemas import (
    CatalogManifest,
    CustomSizeConstraints,
    FalImageModelDefinition,
    IntegerField,
    NumberField,
    OptionField,
)
from open_webui.extensions.fal_catalog.tests.model_test_support import (
    video_definition as _video,
)
from open_webui.extensions.fal_catalog.video_schemas import (
    VideoAssetInput,
    VideoAudioOption,
    VideoBooleanField,
    VideoCatalogManifest,
    VideoIntegerField,
    VideoJsonField,
    VideoNumberField,
    VideoOptionField,
    VideoTextField,
)
from pydantic import ValidationError


def _image(**changes):
    values = {
        'id': 'fal-ai/model',
        'public_id': 'model',
        'name': 'Model',
        'provider': 'fal',
        'task': 'text-to-image',
    }
    values.update(changes)
    return FalImageModelDefinition(**values)


def test_catalog_manifests_reject_duplicates_and_nested_paths() -> None:
    image_defaults = {'text-to-image': 'a', 'image-to-image': 'b'}
    video_defaults = {
        'text-to-video': 'a',
        'image-to-video': 'b',
        'video-to-video': 'c',
    }
    for model, modality, defaults in (
        (CatalogManifest, 'image', image_defaults),
        (VideoCatalogManifest, 'video', video_defaults),
    ):
        for files in (['a.json', 'a.json'], ['nested/a.json'], ['a.txt']):
            with pytest.raises(ValidationError):
                model(schema_version=1, modality=modality, defaults=defaults, files=files)


@pytest.mark.parametrize(
    ('factory', 'kwargs'),
    [
        (OptionField, {'field': 'Bad', 'options': ['a']}),
        (OptionField, {'field': 'valid', 'options': ['a'], 'default': 'b'}),
        (IntegerField, {'field': 'valid', 'min': 2, 'max': 1}),
        (NumberField, {'field': 'valid', 'min': 2, 'max': 1}),
        (CustomSizeConstraints, {'min_width': 2, 'max_width': 1}),
    ],
)
def test_image_component_schemas_reject_invalid_values(factory, kwargs) -> None:
    with pytest.raises(ValidationError):
        factory(**kwargs)


def test_image_model_rejects_route_provider_counts_and_capability_conflicts() -> None:
    invalid_models = (
        {'id': '../model'},
        {'provider': 'FAL'},
        {'image_counts': [1, 1]},
        {
            'option_fields': [
                {'field': 'same', 'options': ['a']},
                {'field': 'same', 'options': ['b']},
            ]
        },
        {'generation_model': 'fal-ai/other'},
        {'image_input_field': 'image_url'},
        {'default_aspect_ratio': 'wide', 'aspect_ratios': ['square']},
        {'custom_size': {'min_width': 1}},
    )
    for changes in invalid_models:
        with pytest.raises(ValidationError):
            _image(**changes)


def test_video_asset_and_dynamic_field_validation_edges() -> None:
    base_asset = {
        'role': 'start_image',
        'field': 'image_url',
        'mime_types': ['image/png'],
        'max_bytes': 10,
    }
    invalid_assets = (
        {**base_asset, 'field': 'Bad'},
        {**base_asset, 'mime_types': ['invalid']},
        {**base_asset, 'multiple': False, 'max_count': 2},
        {**base_asset, 'min_duration_seconds': 2, 'max_duration_seconds': 1},
    )
    for values in invalid_assets:
        with pytest.raises(ValidationError):
            VideoAssetInput(**values)

    invalid_fields = (
        (VideoAudioOption, {'mode': 'silent', 'values': {'Bad': True}}),
        (VideoOptionField, {'field': 'Bad', 'options': ['a']}),
        (VideoOptionField, {'field': 'valid', 'options': ['a', 'a']}),
        (VideoOptionField, {'field': 'valid', 'options': ['a'], 'default': 'b'}),
        (VideoBooleanField, {'field': 'Bad'}),
        (VideoIntegerField, {'field': 'valid', 'min': 2, 'max': 1}),
        (VideoIntegerField, {'field': 'valid', 'min': 1, 'default': 0}),
        (VideoNumberField, {'field': 'valid', 'max': 1, 'default': 2}),
        (VideoTextField, {'field': 'Bad'}),
        (VideoJsonField, {'field': 'valid', 'primary_input': True}),
    )
    for factory, values in invalid_fields:
        with pytest.raises(ValidationError):
            factory(**values)


def test_video_model_rejects_identifier_output_and_duration_conflicts() -> None:
    invalid_models = (
        {'id': '../model'},
        {'provider': 'FAL'},
        {'output_field': 'Bad'},
        {'fixed_fields': {'Bad': True}},
        {'output_mime_types': ['image/png']},
        {'durations': ['5'], 'duration_min': 1},
        {'durations': ['5', '5']},
        {'durations': ['5'], 'default_duration': '10'},
        {'duration_min': 1, 'default_duration': 'invalid'},
        {'duration_min': 2, 'default_duration': '1'},
        {'aspect_ratios': ['wide', 'wide']},
        {'aspect_ratios': ['wide'], 'default_aspect_ratio': 'square'},
    )
    for changes in invalid_models:
        with pytest.raises(ValidationError):
            _video(**changes)


def test_video_model_rejects_audio_asset_and_provider_field_conflicts() -> None:
    start_asset = {
        'role': 'start_image',
        'field': 'image_url',
        'required': True,
        'mime_types': ['image/png'],
        'max_bytes': 10,
    }
    invalid_models = (
        {
            'audio_options': [{'mode': 'silent'}, {'mode': 'silent'}],
        },
        {
            'audio_options': [{'mode': 'silent'}],
            'default_audio_mode': 'generate',
        },
        {
            'task': 'image-to-video',
        },
        {
            'task': 'image-to-video',
            'asset_inputs': [start_asset, start_asset],
        },
        {
            'asset_inputs': [start_asset],
            'fixed_fields': {'image_url': True},
        },
    )
    for changes in invalid_models:
        with pytest.raises(ValidationError):
            _video(**changes)

    primary_json = {
        'field': 'input_json',
        'required': True,
        'primary_input': True,
    }
    assert _video(task='image-to-video', json_fields=[primary_json]) is not None
