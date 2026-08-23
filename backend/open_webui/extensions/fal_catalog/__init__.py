"""Declarative fal.ai model catalog owned by the Open WebUI extension layer."""

from open_webui.extensions.fal_catalog.loader import (
    FalCatalog,
    FalCatalogError,
    FalVideoCatalog,
    load_image_catalog,
    load_video_catalog,
    load_video_catalog_cached,
)

__all__ = [
    'FalCatalog',
    'FalCatalogError',
    'FalVideoCatalog',
    'load_image_catalog',
    'load_video_catalog',
    'load_video_catalog_cached',
]
