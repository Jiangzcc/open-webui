import json

import pytest
from open_webui.extensions.fal_catalog import loader

from .test_loader import _example_models, _write_catalog


def test_json_reader_reports_missing_and_malformed_files(tmp_path) -> None:
    with pytest.raises(loader.FalCatalogError, match='missing'):
        loader._read_json(tmp_path / 'missing.json')
    malformed = tmp_path / 'malformed.json'
    malformed.write_text('{', encoding='utf-8')
    with pytest.raises(loader.FalCatalogError, match='valid JSON'):
        loader._read_json(malformed)


def test_image_catalog_rejects_duplicate_internal_ids_and_wrong_defaults(tmp_path) -> None:
    models = _example_models()
    models[1]['id'] = models[0]['id']
    with pytest.raises(loader.FalCatalogError, match='internal ids'):
        loader.load_image_catalog(_write_catalog(tmp_path, models))

    models = _example_models()
    root = _write_catalog(tmp_path, models)
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    manifest['defaults']['text-to-image'] = 'fal-ai/missing'
    (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(loader.FalCatalogError, match='not registered'):
        loader.load_image_catalog(root)


def test_video_catalog_rejects_invalid_manifest_model_and_defaults(tmp_path) -> None:
    (tmp_path / 'manifest.json').write_text('{}', encoding='utf-8')
    with pytest.raises(loader.FalCatalogError, match='manifest'):
        loader.load_video_catalog(tmp_path)

    manifest = {
        'schema_version': 1,
        'modality': 'video',
        'defaults': {
            'text-to-video': 'missing',
            'image-to-video': 'missing',
            'video-to-video': 'missing',
        },
        'files': ['models.json'],
    }
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    (tmp_path / 'models.json').write_text('[{}]', encoding='utf-8')
    with pytest.raises(loader.FalCatalogError, match='model file'):
        loader.load_video_catalog(tmp_path)

    (tmp_path / 'models.json').write_text('[]', encoding='utf-8')
    with pytest.raises(loader.FalCatalogError, match='not registered'):
        loader.load_video_catalog(tmp_path)
