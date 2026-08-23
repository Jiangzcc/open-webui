from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from open_webui.extensions.fal_catalog.loader import (
    FalCatalogError,
    load_video_catalog,
    load_video_catalog_cached,
)

EXPECTED_PACKAGED_PROVIDERS = {
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

TARGET_DOC_PATTERNS = (
    'vidu/**/*.md',
    'minimax/hailuo-2/*.md',
    'minimax/hailuo-2.3/*.md',
    'google/veo3.1/*.md',
    'google/gemini-omni-flash/*.md',
    'pika/v2/*.md',
    'pika/v2.1/*.md',
    'pika/v2.2/*.md',
    'pixverse/c1/*.md',
    'pixverse/v6/*.md',
    'luma/ray-3.2/*.md',
)


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

    assert catalog.definitions
    assert catalog.defaults == {
        'text-to-video': 'bytedance/seedance-2.0/text-to-video',
        'image-to-video': 'bytedance/seedance-2.0/image-to-video',
        'video-to-video': 'fal-ai/wan/v2.7/edit-video',
    }
    providers = {definition.provider for definition in catalog.definitions}
    assert providers >= EXPECTED_PACKAGED_PROVIDERS
    assert {definition.task for definition in catalog.definitions} == {
        'text-to-video',
        'image-to-video',
        'video-to-video',
    }
    assert len(catalog.internal_to_public) == len(catalog.public_to_internal) == len(catalog.definitions)

    for provider in EXPECTED_PACKAGED_PROVIDERS:
        tasks = {definition.task for definition in catalog.definitions if definition.provider == provider}
        assert tasks & {'text-to-video', 'image-to-video'}, f'{provider} has no generation model'

    for definition in catalog.definitions:
        assert definition.output_field
        assert definition.output_mime_types
        assert all(mime_type.startswith('video/') for mime_type in definition.output_mime_types)


def test_packaged_video_models_require_their_primary_asset() -> None:
    catalog = load_video_catalog()

    for definition in catalog.definitions:
        required_roles = {asset.role for asset in definition.asset_inputs or () if asset.required}
        if definition.task == 'image-to-video':
            required_primary_json = any(
                field.required and field.primary_input for field in definition.json_fields or ()
            )
            assert 'start_image' in required_roles or required_primary_json
        elif definition.task == 'video-to-video':
            assert 'source_video' in required_roles


def test_packaged_video_catalog_covers_target_documented_endpoints() -> None:
    docs_root = Path(__file__).resolve().parents[5] / 'docs' / 'fal'
    documented_ids: set[str] = set()
    for pattern in TARGET_DOC_PATTERNS:
        for path in docs_root.glob(pattern):
            source = path.read_text(encoding='utf-8')
            category = re.search(r'\*\*Category\*\*: ([^\n]+)', source)
            model_id = re.search(r'\*\*Model ID\*\*: `([^`]+)`', source)
            if category and category.group(1).strip() in {'text-to-video', 'image-to-video', 'video-to-video'}:
                assert model_id is not None, f'{path} has no model id'
                documented_ids.add(model_id.group(1))

    packaged_ids = {definition.id for definition in load_video_catalog().definitions}
    assert documented_ids <= packaged_ids


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


def test_cached_loader_reuses_unchanged_catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """审查发现 #2：缓存命中时不得再次解析目录文件，任意 model_id 的 miss
    不能放大成全量磁盘解析。"""
    catalog_dir = _write_catalog(tmp_path, _example_models())

    parse_calls = 0
    real_loader = load_video_catalog

    def counting_loader(path: Path | None = None):  # type: ignore[no-untyped-def]
        nonlocal parse_calls
        parse_calls += 1
        return real_loader(path)

    monkeypatch.setattr('open_webui.extensions.fal_catalog.loader.load_video_catalog', counting_loader)

    first = load_video_catalog_cached(catalog_dir)
    second = load_video_catalog_cached(catalog_dir)

    assert first is second
    assert parse_calls == 1


def test_cached_loader_picks_up_hot_updates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """目录文件热更新后，下一次调用必须返回重载后的目录。"""
    catalog_dir = _write_catalog(tmp_path, _example_models())

    monkeypatch.setattr('open_webui.extensions.fal_catalog.loader.load_video_catalog', load_video_catalog)

    before = load_video_catalog_cached(catalog_dir)

    models = _example_models()
    models[0]['public_id'] = 'vendor-text-renamed'
    (catalog_dir / 'models.json').write_text(json.dumps(models), encoding='utf-8')

    after = load_video_catalog_cached(catalog_dir)

    assert after is not before
    assert after.public_to_internal['vendor-text-renamed'] == 'vendor/text-to-video'


def test_cached_loader_tolerates_file_removed_between_glob_and_stat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """回归（对抗性审查）：目录热更新（删除/原子替换文件）与请求并发时，
    glob 已列出、stat 时已消失的文件不能让签名计算抛 FileNotFoundError
    （未处理异常 → 500）；跳过该文件即可，未变化的目录仍复用缓存。"""
    catalog_dir = _write_catalog(tmp_path, _example_models())
    before = load_video_catalog_cached(catalog_dir)

    real_glob = Path.glob

    def glob_with_vanishing_file(path: Path, pattern: str):  # type: ignore[no-untyped-def]
        yield from real_glob(path, pattern)
        if pattern == '*.json':
            yield path / 'vanishing.json'

    monkeypatch.setattr(Path, 'glob', glob_with_vanishing_file)

    after = load_video_catalog_cached(catalog_dir)

    assert after is before
