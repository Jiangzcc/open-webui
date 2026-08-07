from __future__ import annotations

import json
from pathlib import Path

import pytest
from open_webui.extensions.fal_catalog.loader import FalCatalogError, load_video_catalog


def _example_models() -> list[dict[str, object]]:
    return [
        {
            'id': 'vendor/text-to-video',
            'public_id': 'vendor-text',
            'name': 'Vendor Text',
            'provider': 'vendor',
            'task': 'text-to-video',
            'durations': ['5', '10'],
            'default_duration': '5',
        },
        {
            'id': 'vendor/image-to-video',
            'public_id': 'vendor-image',
            'name': 'Vendor Image',
            'provider': 'vendor',
            'task': 'image-to-video',
            'asset_inputs': [
                {
                    'role': 'start_image',
                    'field': 'image_url',
                    'required': True,
                    'mime_types': ['image/jpeg', 'image/png'],
                    'max_bytes': 10485760,
                }
            ],
        },
        {
            'id': 'vendor/video-to-video',
            'public_id': 'vendor-video',
            'name': 'Vendor Video',
            'provider': 'vendor',
            'task': 'video-to-video',
            'asset_inputs': [
                {
                    'role': 'source_video',
                    'field': 'video_url',
                    'required': True,
                    'mime_types': ['video/mp4'],
                    'max_bytes': 104857600,
                }
            ],
        },
    ]


def _write_catalog(tmp_path: Path, models: list[dict[str, object]]) -> Path:
    manifest = {
        'schema_version': 1,
        'modality': 'video',
        'defaults': {
            'text-to-video': 'vendor/text-to-video',
            'image-to-video': 'vendor/image-to-video',
            'video-to-video': 'vendor/video-to-video',
        },
        'files': ['models.json'],
    }
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    (tmp_path / 'models.json').write_text(json.dumps(models), encoding='utf-8')
    return tmp_path


def test_loads_packaged_video_catalog() -> None:
    catalog = load_video_catalog()

    assert len(catalog.definitions) == 23
    assert catalog.defaults == {
        'text-to-video': 'bytedance/seedance-2.0/text-to-video',
        'image-to-video': 'bytedance/seedance-2.0/image-to-video',
        'video-to-video': 'fal-ai/wan/v2.7/edit-video',
    }
    assert {definition.provider for definition in catalog.definitions} == {
        'alibaba',
        'bytedance',
        'kling',
        'ltx',
    }
    assert {definition.task for definition in catalog.definitions} == {
        'text-to-video',
        'image-to-video',
        'video-to-video',
    }
    assert len(catalog.internal_to_public) == len(catalog.public_to_internal) == 23


def test_packaged_video_models_require_their_primary_asset() -> None:
    catalog = load_video_catalog()

    for definition in catalog.definitions:
        required_roles = {
            asset.role for asset in definition.asset_inputs or () if asset.required
        }
        if definition.task == 'image-to-video':
            assert 'start_image' in required_roles
        elif definition.task == 'video-to-video':
            assert 'source_video' in required_roles


def test_packaged_video_models_keep_safety_server_controlled() -> None:
    catalog = load_video_catalog()

    for definition in catalog.definitions:
        dynamic_fields = {
            field.field
            for group in (
                definition.option_fields,
                definition.boolean_fields,
                definition.integer_fields,
                definition.number_fields,
                definition.text_fields,
            )
            for field in group or ()
        }
        assert 'enable_safety_checker' not in dynamic_fields
        if 'enable_safety_checker' in definition.fixed_fields:
            assert definition.fixed_fields['enable_safety_checker'] is True


def test_rejects_duplicate_video_public_ids(tmp_path: Path) -> None:
    models = _example_models()
    models[1]['public_id'] = 'vendor-text'

    with pytest.raises(FalCatalogError, match='public ids must be unique'):
        load_video_catalog(_write_catalog(tmp_path, models))


def test_rejects_wrong_default_video_task(tmp_path: Path) -> None:
    models = _example_models()
    models[0]['task'] = 'image-to-video'
    models[0]['asset_inputs'] = models[1]['asset_inputs']

    with pytest.raises(FalCatalogError, match='default text-to-video video model has the wrong task'):
        load_video_catalog(_write_catalog(tmp_path, models))


def test_rejects_missing_primary_video_asset(tmp_path: Path) -> None:
    models = _example_models()
    models[1]['asset_inputs'] = []

    with pytest.raises(FalCatalogError, match='must require start_image'):
        load_video_catalog(_write_catalog(tmp_path, models))


def test_rejects_overlapping_duration_modes(tmp_path: Path) -> None:
    models = _example_models()
    models[0]['duration_min'] = 3
    models[0]['duration_max'] = 15

    with pytest.raises(FalCatalogError, match='either options or numeric range'):
        load_video_catalog(_write_catalog(tmp_path, models))


def test_rejects_duplicate_provider_request_fields(tmp_path: Path) -> None:
    models = _example_models()
    models[0]['option_fields'] = [
        {'field': 'mode', 'options': ['standard', 'pro']},
    ]
    models[0]['fixed_fields'] = {'mode': 'standard'}

    with pytest.raises(FalCatalogError, match='provider request fields must be unique'):
        load_video_catalog(_write_catalog(tmp_path, models))


def test_rejects_unknown_video_model_fields(tmp_path: Path) -> None:
    models = _example_models()
    models[0]['provider_template'] = '{{ unsafe }}'

    with pytest.raises(FalCatalogError, match='provider_template'):
        load_video_catalog(_write_catalog(tmp_path, models))
