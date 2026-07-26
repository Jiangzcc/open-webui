from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from open_webui.extensions.fal_catalog.loader import FalCatalogError, load_image_catalog

EXPECTED_CATALOG_SHA256 = 'c61d2e7e7e62acfe64c1573f8061cdbcddc1041af36e32218a922e17a2a697c6'


def _write_catalog(tmp_path: Path, models: list[dict[str, object]]) -> Path:
    manifest = {
        'schema_version': 1,
        'modality': 'image',
        'defaults': {
            'text-to-image': 'fal-ai/example',
            'image-to-image': 'fal-ai/example/edit',
        },
        'files': ['models.json'],
    }
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    (tmp_path / 'models.json').write_text(json.dumps(models), encoding='utf-8')
    return tmp_path


def _example_models() -> list[dict[str, object]]:
    return [
        {
            'id': 'fal-ai/example',
            'public_id': 'example',
            'name': 'Example',
            'provider': 'example',
            'task': 'text-to-image',
            'edit_model': 'fal-ai/example/edit',
        },
        {
            'id': 'fal-ai/example/edit',
            'public_id': 'example/edit',
            'name': 'Example Edit',
            'provider': 'example',
            'task': 'image-to-image',
            'generation_model': 'fal-ai/example',
        },
    ]


def test_loads_packaged_image_catalog_with_stable_legacy_snapshot() -> None:
    catalog = load_image_catalog()
    payload = {
        'generation_default': catalog.generation_default,
        'edit_default': catalog.edit_default,
        'models': catalog.legacy_models(),
        'public_ids': dict(catalog.internal_to_public),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

    assert len(catalog.definitions) == 44
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_CATALOG_SHA256


def test_packaged_catalog_has_curated_primary_model_order() -> None:
    catalog = load_image_catalog()
    primary_by_provider: dict[str, list[str]] = {}
    for definition in catalog.definitions:
        if definition.task == 'text-to-image':
            primary_by_provider.setdefault(definition.provider, []).append(definition.public_id)

    assert primary_by_provider == {
        'alibaba': [
            'z-image-turbo',
            'z-image-base',
            'qwen-image-max',
            'qwen-image-2-pro',
            'qwen-image-2',
            'qwen-image-2512',
            'qwen-image',
            'wan-2.7-pro',
            'wan-2.7',
            'wan-2.6',
            'wan-2.5-preview',
            'wan-2.2-a14b',
            'wan-2.2-5b',
        ],
        'google': [
            'nano-banana-2',
            'nano-banana-2-lite',
            'nano-banana-pro',
            'nano-banana',
            'nano-banana-lite',
        ],
        'openai': ['gpt-image-2', 'gpt-image-1.5', 'gpt-image-1', 'gpt-image-1-mini'],
        'xai': ['grok-imagine-image-pro', 'grok-imagine-image'],
    }


def test_packaged_catalog_keeps_edit_siblings_next_to_generation_models() -> None:
    catalog = load_image_catalog()
    positions = {definition.id: index for index, definition in enumerate(catalog.definitions)}

    for definition in catalog.definitions:
        if definition.edit_model is not None:
            assert positions[definition.edit_model] == positions[definition.id] + 1


def test_rejects_duplicate_public_ids(tmp_path: Path) -> None:
    models = _example_models()
    models[1]['public_id'] = 'example'

    with pytest.raises(FalCatalogError, match='public ids must be unique'):
        load_image_catalog(_write_catalog(tmp_path, models))


def test_rejects_unknown_model_relation(tmp_path: Path) -> None:
    models = _example_models()
    models[0]['edit_model'] = 'fal-ai/missing/edit'

    with pytest.raises(FalCatalogError, match='references unknown edit_model'):
        load_image_catalog(_write_catalog(tmp_path, models))


def test_rejects_one_sided_model_relation(tmp_path: Path) -> None:
    models = _example_models()
    models[1].pop('generation_model')

    with pytest.raises(FalCatalogError, match='bidirectional model relation'):
        load_image_catalog(_write_catalog(tmp_path, models))


def test_rejects_unknown_model_fields(tmp_path: Path) -> None:
    models = _example_models()
    models[0]['unsafe_template'] = '{{ arbitrary }}'

    with pytest.raises(FalCatalogError, match='unsafe_template'):
        load_image_catalog(_write_catalog(tmp_path, models))


@pytest.mark.parametrize(
    ('field', 'value', 'message'),
    [
        ('id', 'https://fal.run/example', 'normalized route identifiers'),
        ('public_id', '../example', 'normalized route identifiers'),
        ('provider', '../vendor', 'lowercase slug'),
    ],
)
def test_rejects_unsafe_route_and_provider_values(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    models = _example_models()
    models[0][field] = value

    with pytest.raises(FalCatalogError, match=message):
        load_image_catalog(_write_catalog(tmp_path, models))


def test_rejects_duplicate_request_field_types(tmp_path: Path) -> None:
    models = _example_models()
    models[0]['boolean_fields'] = [{'field': 'sync_mode'}]
    models[0]['text_fields'] = [{'field': 'sync_mode'}]

    with pytest.raises(FalCatalogError, match='field names must be unique'):
        load_image_catalog(_write_catalog(tmp_path, models))
