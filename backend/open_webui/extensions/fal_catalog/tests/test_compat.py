from __future__ import annotations

import hashlib
import json
from pathlib import Path

from open_webui.utils.images import fal_models

EXPECTED_PUBLIC_CATALOG_SHA256 = 'bc43422f0297812c8b4e33fb3036d484e44f8b61eb25b316d93fb2fd3d78594c'


def test_legacy_facade_preserves_public_catalog_snapshot() -> None:
    public = fal_models.public_fal_image_models(fal_models.FAL_DEFAULT_IMAGE_MODEL)
    raw = json.dumps(public, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

    assert len(public) == 44
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_PUBLIC_CATALOG_SHA256


def test_legacy_facade_preserves_fail_closed_bidirectional_ids() -> None:
    assert fal_models.public_fal_image_model_id('fal-ai/z-image/turbo') == 'z-image-turbo'
    assert fal_models.internal_fal_image_model_id('z-image-turbo') == 'fal-ai/z-image/turbo'
    assert fal_models.public_fal_image_model_id('fal-ai/unknown') is None
    assert fal_models.internal_fal_image_model_id('unknown') is None
    assert fal_models.normalize_fal_image_model_id('unknown') is None


def test_legacy_facade_contains_no_hard_coded_model_registry() -> None:
    source = Path(fal_models.__file__).read_text(encoding='utf-8')

    assert 'FAL_IMAGE_MODELS: list[dict[str, Any]] = _CATALOG.legacy_models()' in source
    assert 'fal-ai/z-image/turbo' not in source
    assert '_FAL_INTERNAL_TO_PUBLIC_ID = {' not in source
