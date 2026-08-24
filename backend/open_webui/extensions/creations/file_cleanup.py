from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable

from open_webui.models.files import Files
from open_webui.storage.provider import Storage

log = logging.getLogger(__name__)


async def cleanup_uploaded_files(files: Iterable[object]) -> None:
    """Best-effort removal for uploads whose owning transaction did not commit."""
    for file in reversed(tuple(files)):
        file_id = getattr(file, 'id', None)
        file_path = getattr(file, 'path', None)
        if isinstance(file_path, str) and file_path:
            try:
                await asyncio.to_thread(Storage.delete_file, file_path)
            except Exception:
                log.exception('Could not remove orphaned generated file payload %s', file_id)
        if isinstance(file_id, str) and file_id:
            try:
                await Files.delete_file_by_id(file_id)
            except Exception:
                log.exception('Could not remove orphaned generated file row %s', file_id)


__all__ = ['cleanup_uploaded_files']
