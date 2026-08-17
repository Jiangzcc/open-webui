"""Mock video source backed by the Pexels Videos API.

This module exists purely to feed the local development "mock" video generation
path with a fresh random clip from Pexels (https://www.pexels.com/) instead of
the static ``welcome.mp4`` asset. It is a thin, optional client:

* The Pexels API key is read from the environment (``PEXELS_API_KEY``), which is
  expected to live in the gitignored repo-root ``.env``. It is never written
  into source, tests, logs, or error messages.
* When the key is absent or any network/parse error occurs, callers receive
  ``None`` so the generator can fall back to the bundled static mock assets.
  Mock data must stay isolated from the default production path, and failing
  open to the existing static asset keeps that contract.

Only the shared aiohttp session pool (``get_session``) is used so outbound
calls reuse the long-lived connector. Binary payloads are streamed into
``bytes``; list responses are parsed as JSON.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from pathlib import Path

import aiohttp
from open_webui.env import AIOHTTP_CLIENT_SESSION_SSL
from open_webui.utils.session_pool import get_session

log = logging.getLogger(__name__)

PEXELS_API_KEY_ENV = 'PEXELS_API_KEY'
_PEXELS_VIDEO_LIST_URL = 'https://api.pexels.com/videos/popular'
_PEXELS_PAGE_SIZE = 15
# Hard cap on the downloaded mock clip so a stray large file does not stall the
# generator. The static welcome.mp4 asset is ~1.9 MB; 12 MB comfortably covers
# SD clips while bounding worst-case memory.
_MAX_VIDEO_BYTES = 12 * 1024 * 1024


@dataclass(frozen=True)
class PexelsMockClip:
    """A downloaded mock clip held entirely in memory.

    ``video_bytes`` is an mp4 payload; ``poster_bytes`` is a still image
    (jpeg by default from Pexels' ``image`` field). ``duration_seconds`` is the
    integer clip duration reported by Pexels.
    """

    video_bytes: bytes
    poster_bytes: bytes
    poster_content_type: str
    duration_seconds: int


def pexels_api_key() -> str | None:
    """Return the configured Pexels API key, or ``None`` when not set."""
    import os

    return os.getenv(PEXELS_API_KEY_ENV) or None


async def _request_json(
    session: aiohttp.ClientSession,
    url: str,
    headers: dict[str, str],
    params: dict[str, str | int],
) -> dict[str, object] | None:
    async with session.get(
        url,
        headers=headers,
        params=params,
        ssl=AIOHTTP_CLIENT_SESSION_SSL,
    ) as response:
        if response.status != 200:
            log.debug('pexels mock list returned status %s', response.status)
            return None
        try:
            return await response.json(content_type=None)
        except aiohttp.ContentTypeError:
            return None


async def _download_bytes(
    session: aiohttp.ClientSession,
    url: str,
    *,
    max_bytes: int | None = None,
) -> bytes | None:
    async with session.get(url, ssl=AIOHTTP_CLIENT_SESSION_SSL) as response:
        if response.status != 200:
            log.debug('pexels mock download returned status %s for %s', response.status, url)
            return None
        declared = response.headers.get('Content-Length')
        if max_bytes is not None and declared and declared.isdigit() and int(declared) > max_bytes:
            log.debug('pexels mock asset exceeds %d bytes (declared %s)', max_bytes, declared)
            return None
        buffer = bytearray()
        async for chunk in response.content.iter_chunked(64 * 1024):
            buffer.extend(chunk)
            if max_bytes is not None and len(buffer) > max_bytes:
                log.debug('pexels mock asset exceeded %d bytes while streaming', max_bytes)
                return None
        return bytes(buffer)


def _pick_smallest_mp4(video: dict[str, object]) -> dict[str, object] | None:
    files = video.get('video_files') if isinstance(video, dict) else None
    if not isinstance(files, list):
        return None
    candidates: list[dict[str, object]] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        if item.get('file_type') != 'video/mp4':
            continue
        link = item.get('link')
        if not isinstance(link, str) or not link.startswith('https://'):
            continue
        candidates.append(item)
    if not candidates:
        return None

    def _area(item: dict[str, object]) -> int:
        width = item.get('width')
        height = item.get('height')
        if isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0:
            return width * height
        return 1 << 30  # unknown resolution → sort last, but keep it usable

    candidates.sort(key=_area)
    return candidates[0]


def _poster_url(video: dict[str, object]) -> tuple[str | None, str]:
    """Return ``(url, content_type)`` for the clip's still image, if any.

    Prefers the ``image`` field (a cropped preview); falls back to the first
    entry of ``video_pictures``.
    """
    image = video.get('image') if isinstance(video, dict) else None
    if isinstance(image, str) and image.startswith('https://'):
        return image, 'image/jpeg'
    pictures = video.get('video_pictures') if isinstance(video, dict) else None
    if isinstance(pictures, list):
        for picture in pictures:
            if isinstance(picture, dict):
                url = picture.get('picture')
                if isinstance(url, str) and url.startswith('https://'):
                    return url, 'image/jpeg'
    return None, 'image/jpeg'


async def fetch_random_pexels_clip() -> PexelsMockClip | None:
    """Fetch one random short clip from Pexels into memory.

    Returns ``None`` when the API key is missing, the API or download fails, or
    no suitable mp4 is found — callers should fall back to static mock assets.
    """
    api_key = pexels_api_key()
    if not api_key:
        log.debug('pexels mock disabled: %s not configured', PEXELS_API_KEY_ENV)
        return None

    session = await get_session()
    headers = {'Authorization': api_key}
    params = {'per_page': _PEXELS_PAGE_SIZE}

    payload = await _request_json(session, _PEXELS_VIDEO_LIST_URL, headers, params)
    if not isinstance(payload, dict):
        return None
    videos = payload.get('videos')
    if not isinstance(videos, list) or not videos:
        return None

    # Shuffle so repeated generations surface different clips. ``random.Random``
    # is seeded per-call from the default source; deterministic ordering is not
    # required for mock data.
    shuffled = list(videos)
    random.Random().shuffle(shuffled)

    for video in shuffled:
        clip = await _try_clip_from_video(session, video)
        if clip is not None:
            return clip
    return None


async def _try_clip_from_video(
    session: aiohttp.ClientSession,
    video: object,
) -> PexelsMockClip | None:
    """Download the smallest usable mp4 from one Pexels video entry.

    Returns ``None`` when the entry is malformed, lacks an mp4, or the download
    fails — the caller moves on to the next shuffled entry.
    """
    if not isinstance(video, dict):
        return None
    duration = video.get('duration')
    if not isinstance(duration, int) or duration <= 0:
        return None
    chosen = _pick_smallest_mp4(video)
    if not chosen:
        return None
    link = chosen['link']
    if not isinstance(link, str):
        return None
    video_bytes = await _download_bytes(session, link, max_bytes=_MAX_VIDEO_BYTES)
    if not video_bytes:
        return None
    poster_url, poster_content_type = _poster_url(video)
    poster_bytes: bytes | None = None
    if poster_url is not None:
        poster_bytes = await _download_bytes(session, poster_url)
    if not poster_bytes:
        # No usable still from Pexels; let the caller synthesize a poster
        # from the downloaded video instead of failing the whole clip.
        return PexelsMockClip(
            video_bytes=video_bytes,
            poster_bytes=b'',
            poster_content_type=poster_content_type,
            duration_seconds=duration,
        )
    return PexelsMockClip(
        video_bytes=video_bytes,
        poster_bytes=poster_bytes,
        poster_content_type=poster_content_type,
        duration_seconds=duration,
    )


def extract_poster_from_video(video_source: bytes | Path) -> tuple[bytes, str] | None:
    """Decode the first frame of a video payload or file into a webp still.

    Used when Pexels does not provide a usable poster image. Returns
    ``(webp_bytes, 'image/webp')`` or ``None`` when decoding is unavailable.
    """
    import io

    try:
        import av
    except ImportError:
        log.debug('pyav unavailable; cannot synthesize poster')
        return None
    try:
        container = av.open(str(video_source) if isinstance(video_source, Path) else io.BytesIO(video_source))
    except Exception:
        log.debug('pexels mock poster: could not open video bytes for frame extraction')
        return None
    try:
        stream = container.streams.video[0]
        for frame in container.decode(stream):
            image = frame.to_image()
            buffer = io.BytesIO()
            image.save(buffer, format='WEBP', quality=80)
            return (buffer.getvalue(), 'image/webp')
    except Exception:
        log.debug('pexels mock poster: frame extraction failed')
        return None
    finally:
        try:
            container.close()
        except Exception:
            pass


def probe_video_duration(video_path: Path) -> int | None:
    """Read the actual container duration without loading the video into memory."""
    try:
        import av
    except ImportError:
        return None
    try:
        container = av.open(str(video_path))
    except Exception:
        log.debug('could not open generated video for duration probing')
        return None
    try:
        if container.duration is not None:
            return max(1, round(container.duration / av.time_base))
        stream = container.streams.video[0]
        if stream.duration is not None and stream.time_base is not None:
            return max(1, round(float(stream.duration * stream.time_base)))
        return None
    except Exception:
        log.debug('could not determine generated video duration')
        return None
    finally:
        container.close()


async def fetch_pexels_mock_clip() -> PexelsMockClip | None:
    """Public seam used by the generator.

    Mirrors the synchronous fallback contract: returns ``None`` when Pexels is
    unavailable so the caller keeps the existing static-mock path. Exposed as a
    distinct name so tests can patch the module boundary cleanly.
    """
    return await fetch_random_pexels_clip()


__all__ = [
    'PEXELS_API_KEY_ENV',
    'PexelsMockClip',
    'extract_poster_from_video',
    'fetch_pexels_mock_clip',
    'pexels_api_key',
    'probe_video_duration',
]
