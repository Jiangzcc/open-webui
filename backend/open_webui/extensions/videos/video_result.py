"""Small result-shape and temporary-file helpers for video execution."""

from __future__ import annotations

import asyncio
import logging
import tempfile
import time
from pathlib import Path

from open_webui.extensions.url_security import require_https_url
from open_webui.extensions.videos.schemas import VideoTaskResponse

TEMP_FILE_PREFIX = 'open-webui-fal-video-'

log = logging.getLogger(__name__)


def extract_fal_video_url(result: object, output_field: str = 'video') -> str | None:
    if isinstance(result, dict) and isinstance(result.get('data'), dict):
        result = result['data']
    if not isinstance(result, dict):
        return None
    candidate = result.get(output_field)
    if isinstance(candidate, str) and candidate:
        return candidate
    if isinstance(candidate, dict) and isinstance(candidate.get('url'), str):
        return candidate['url']
    fallback = result.get('url')
    return fallback if isinstance(fallback, str) and fallback else None


async def cleanup_stale_fal_video_temp_files(*, max_age_seconds: int) -> int:
    cutoff = time.time() - max_age_seconds

    def cleanup() -> int:
        removed = 0
        for path in Path(tempfile.gettempdir()).glob(f'{TEMP_FILE_PREFIX}*.mp4'):
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                log.exception('Could not inspect or remove stale FAL video temp file %s', path)
        return removed

    return await asyncio.to_thread(cleanup)


def task_duration_seconds(task: VideoTaskResponse) -> int | None:
    value = task.params.get('duration')
    try:
        return max(1, round(float(value))) if value is not None else None
    except (TypeError, ValueError):
        return None


def looks_like_mp4_file(path: Path) -> bool:
    with path.open('rb') as source:
        header = source.read(12)
    return len(header) >= 12 and header[4:8] == b'ftyp'


async def remove_file(path: Path) -> None:
    try:
        await asyncio.to_thread(path.unlink, missing_ok=True)
    except Exception:
        log.exception('Could not remove temporary FAL video %s', path)


def is_safe_https_url(value: str) -> bool:
    try:
        require_https_url(value)
    except ValueError:
        return False
    return True


__all__ = [
    'TEMP_FILE_PREFIX',
    'cleanup_stale_fal_video_temp_files',
    'extract_fal_video_url',
    'is_safe_https_url',
    'looks_like_mp4_file',
    'remove_file',
    'task_duration_seconds',
]
