from __future__ import annotations

import json
from pathlib import Path

import pytest
from open_webui.extensions.fal_catalog.loader import FalCatalogError, load_image_catalog


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


def test_loads_packaged_image_catalog_with_consistent_legacy_projection() -> None:
    catalog = load_image_catalog()
    by_id = {definition.id: definition for definition in catalog.definitions}
    legacy_models = catalog.legacy_models()

    assert catalog.definitions
    assert by_id[catalog.generation_default].task == 'text-to-image'
    assert by_id[catalog.edit_default].task == 'image-to-image'
    assert [model['id'] for model in legacy_models] == [definition.id for definition in catalog.definitions]
    assert dict(catalog.internal_to_public) == {
        definition.id: definition.public_id for definition in catalog.definitions
    }
    assert dict(catalog.public_to_internal) == {
        definition.public_id: definition.id for definition in catalog.definitions
    }


def test_every_packaged_provider_has_a_generation_model() -> None:
    catalog = load_image_catalog()
    primary_by_provider: dict[str, list[str]] = {}
    for definition in catalog.definitions:
        if definition.task == 'text-to-image':
            primary_by_provider.setdefault(definition.provider, []).append(definition.public_id)

    providers = {definition.provider for definition in catalog.definitions}

    assert set(primary_by_provider) == providers
    assert all(public_ids for public_ids in primary_by_provider.values())
    assert all(len(public_ids) == len(set(public_ids)) for public_ids in primary_by_provider.values())


def test_packaged_catalog_keeps_edit_sibling_relations_bidirectional() -> None:
    catalog = load_image_catalog()
    by_id = {definition.id: definition for definition in catalog.definitions}

    for definition in catalog.definitions:
        if definition.edit_model is not None:
            sibling = by_id[definition.edit_model]
            assert sibling.task == 'image-to-image'
            assert sibling.generation_model == definition.id
            assert sibling.provider == definition.provider


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
