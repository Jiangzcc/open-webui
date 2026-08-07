from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from open_webui.extensions.fal_catalog.schemas import CatalogManifest, FalImageModelDefinition
from open_webui.extensions.fal_catalog.video_schemas import (
    FalVideoModelDefinition,
    VideoCatalogManifest,
)
from pydantic import TypeAdapter, ValidationError

_DEFAULT_IMAGE_CATALOG_DIR = Path(__file__).resolve().parent / 'catalog' / 'image'
_DEFAULT_VIDEO_CATALOG_DIR = Path(__file__).resolve().parent / 'catalog' / 'video'
_MODEL_LIST_ADAPTER = TypeAdapter(list[FalImageModelDefinition])
_VIDEO_MODEL_LIST_ADAPTER = TypeAdapter(list[FalVideoModelDefinition])


class FalCatalogError(ValueError):
    """Raised when a declarative fal catalog is malformed or internally inconsistent."""


@dataclass(frozen=True)
class FalCatalog:
    generation_default: str
    edit_default: str
    definitions: tuple[FalImageModelDefinition, ...]
    internal_to_public: Mapping[str, str]
    public_to_internal: Mapping[str, str]

    def legacy_models(self) -> list[dict[str, object]]:
        return [definition.to_legacy_dict() for definition in self.definitions]


@dataclass(frozen=True)
class FalVideoCatalog:
    defaults: Mapping[str, str]
    definitions: tuple[FalVideoModelDefinition, ...]
    internal_to_public: Mapping[str, str]
    public_to_internal: Mapping[str, str]


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as error:
        raise FalCatalogError(f'fal catalog file is missing: {path}') from error
    except json.JSONDecodeError as error:
        raise FalCatalogError(f'fal catalog file is not valid JSON: {path}: {error}') from error


def _validate_relation(
    definition: FalImageModelDefinition,
    field_name: str,
    related_id: str,
    expected_task: str,
    by_id: Mapping[str, FalImageModelDefinition],
) -> None:
    related = by_id.get(related_id)
    if related is None:
        raise FalCatalogError(f'{definition.id} references unknown {field_name}: {related_id}')
    if related.task != expected_task:
        raise FalCatalogError(f'{definition.id} references {field_name} with task {related.task}')
    reverse_field = 'edit_model' if field_name == 'generation_model' else 'generation_model'
    if getattr(related, reverse_field) != definition.id:
        raise FalCatalogError(f'{definition.id} and {related_id} must declare a bidirectional model relation')


def _validate_relations(manifest: CatalogManifest, definitions: list[FalImageModelDefinition]) -> None:
    by_id = {definition.id: definition for definition in definitions}
    if manifest.defaults.text_to_image not in by_id:
        raise FalCatalogError('default text-to-image model is not registered')
    if manifest.defaults.image_to_image not in by_id:
        raise FalCatalogError('default image-to-image model is not registered')
    if by_id[manifest.defaults.text_to_image].task != 'text-to-image':
        raise FalCatalogError('default text-to-image model has the wrong task')
    if by_id[manifest.defaults.image_to_image].task != 'image-to-image':
        raise FalCatalogError('default image-to-image model has the wrong task')

    for definition in definitions:
        for field_name, related_id, expected_task in (
            ('generation_model', definition.generation_model, 'text-to-image'),
            ('edit_model', definition.edit_model, 'image-to-image'),
        ):
            if related_id is not None:
                _validate_relation(definition, field_name, related_id, expected_task, by_id)


def load_image_catalog(catalog_dir: Path | None = None) -> FalCatalog:
    root = (catalog_dir or _DEFAULT_IMAGE_CATALOG_DIR).resolve()
    try:
        manifest = CatalogManifest.model_validate(_read_json(root / 'manifest.json'))
    except ValidationError as error:
        raise FalCatalogError(f'invalid fal image catalog manifest: {error}') from error

    definitions: list[FalImageModelDefinition] = []
    for filename in manifest.files:
        try:
            definitions.extend(_MODEL_LIST_ADAPTER.validate_python(_read_json(root / filename)))
        except ValidationError as error:
            raise FalCatalogError(f'invalid fal model file {filename}: {error}') from error

    internal_ids = [definition.id for definition in definitions]
    public_ids = [definition.public_id for definition in definitions]
    if len(internal_ids) != len(set(internal_ids)):
        raise FalCatalogError('fal model internal ids must be unique')
    if len(public_ids) != len(set(public_ids)):
        raise FalCatalogError('fal model public ids must be unique')

    _validate_relations(manifest, definitions)
    internal_to_public = MappingProxyType({definition.id: definition.public_id for definition in definitions})
    public_to_internal = MappingProxyType({definition.public_id: definition.id for definition in definitions})
    return FalCatalog(
        generation_default=manifest.defaults.text_to_image,
        edit_default=manifest.defaults.image_to_image,
        definitions=tuple(definitions),
        internal_to_public=internal_to_public,
        public_to_internal=public_to_internal,
    )


def load_video_catalog(catalog_dir: Path | None = None) -> FalVideoCatalog:
    root = (catalog_dir or _DEFAULT_VIDEO_CATALOG_DIR).resolve()
    try:
        manifest = VideoCatalogManifest.model_validate(_read_json(root / 'manifest.json'))
    except ValidationError as error:
        raise FalCatalogError(f'invalid fal video catalog manifest: {error}') from error

    definitions: list[FalVideoModelDefinition] = []
    for filename in manifest.files:
        try:
            definitions.extend(_VIDEO_MODEL_LIST_ADAPTER.validate_python(_read_json(root / filename)))
        except ValidationError as error:
            raise FalCatalogError(f'invalid fal video model file {filename}: {error}') from error

    internal_ids = [definition.id for definition in definitions]
    public_ids = [definition.public_id for definition in definitions]
    if len(internal_ids) != len(set(internal_ids)):
        raise FalCatalogError('fal video model internal ids must be unique')
    if len(public_ids) != len(set(public_ids)):
        raise FalCatalogError('fal video model public ids must be unique')

    defaults = {
        'text-to-video': manifest.defaults.text_to_video,
        'image-to-video': manifest.defaults.image_to_video,
        'video-to-video': manifest.defaults.video_to_video,
    }
    by_id = {definition.id: definition for definition in definitions}
    for task, model_id in defaults.items():
        definition = by_id.get(model_id)
        if definition is None:
            raise FalCatalogError(f'default {task} video model is not registered')
        if definition.task != task:
            raise FalCatalogError(f'default {task} video model has the wrong task')

    return FalVideoCatalog(
        defaults=MappingProxyType(defaults),
        definitions=tuple(definitions),
        internal_to_public=MappingProxyType(dict(zip(internal_ids, public_ids, strict=True))),
        public_to_internal=MappingProxyType(dict(zip(public_ids, internal_ids, strict=True))),
    )


__all__ = [
    'FalCatalog',
    'FalCatalogError',
    'FalVideoCatalog',
    'load_image_catalog',
    'load_video_catalog',
]
