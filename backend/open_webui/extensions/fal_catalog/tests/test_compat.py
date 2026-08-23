from __future__ import annotations

from pathlib import Path

from open_webui.extensions.fal_catalog.loader import load_image_catalog
from open_webui.extensions.fal_images import models as fal_models


def test_legacy_facade_projects_every_packaged_catalog_model() -> None:
    catalog = load_image_catalog()
    public = fal_models.public_fal_image_models(fal_models.FAL_DEFAULT_IMAGE_MODEL)
    public_ids = [model['id'] for model in public]

    assert public_ids == [definition.public_id for definition in catalog.definitions]
    assert [model['id'] for model in public if model['is_default']] == [
        catalog.internal_to_public[catalog.generation_default]
    ]
    assert all(
        related_id in public_ids
        for model in public
        for related_id in (model.get('generation_model'), model.get('edit_model'))
        if related_id is not None
    )


def test_legacy_facade_preserves_fail_closed_bidirectional_ids() -> None:
    assert fal_models.public_fal_image_model_id('fal-ai/z-image/turbo') == 'z-image-turbo'
    assert fal_models.public_fal_image_model_id('fal-ai/unknown') is None
    assert fal_models.normalize_fal_image_model_id('unknown') is None


def test_legacy_facade_contains_no_hard_coded_model_registry() -> None:
    source = Path(fal_models.__file__).read_text(encoding='utf-8')

    assert 'FAL_IMAGE_MODELS: list[dict[str, Any]] = _CATALOG.legacy_models()' in source
    assert 'fal-ai/z-image/turbo' not in source
    assert '_FAL_INTERNAL_TO_PUBLIC_ID = {' not in source


def test_safety_checker_defaults_to_false_across_catalog() -> None:
    """复盘 #18：enable_safety_checker 默认 false 是运营拍板决策（见
    schemas.py 留痕注释）——catalog 任何模型不得回潮为 default: true。"""
    catalog = load_image_catalog()

    offenders = [
        definition.id
        for definition in catalog.definitions
        for field in definition.boolean_fields or ()
        if field.field == 'enable_safety_checker' and field.default is True
    ]

    assert offenders == []
