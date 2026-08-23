from __future__ import annotations

import asyncio
import io
import logging
import os
import time
from pathlib import Path
from uuid import uuid4

from fastapi import Request
from open_webui.extensions.creations.models import CreationMediaItem
from open_webui.extensions.videos.executor import VideoExecutionError, VideoExecutionOutput
from open_webui.extensions.videos.pexels_mock import (
    PexelsMockClip,
    extract_poster_from_video,
    fetch_pexels_mock_clip,
)
from open_webui.extensions.videos.schemas import VideoTaskResponse, VideoTaskResult
from open_webui.models.files import Files
from open_webui.storage.provider import Storage
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile

log = logging.getLogger(__name__)
upload_file_handler = None  # lazily bound; tests replace this module-level seam

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
_MOCK_VIDEO_PATH = _REPOSITORY_ROOT / 'static' / 'assets' / 'welcome.mp4'
_MOCK_POSTER_PATH = _REPOSITORY_ROOT / 'static' / 'assets' / 'welcome.webp'
# Mock 路径的模拟延迟：模拟真实生成耗时，避免 mock 完成过快导致前端轮询异常。
_MOCK_VIDEO_DELAY_SECONDS = 1.2


def _now() -> int:
    return int(time.time())


def _positive_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        log.warning('Ignoring invalid %s=%r', name, raw)
        return default
    if value < 0:
        log.warning('Ignoring negative %s=%r', name, raw)
        return default
    return value


async def _run_mock_scenario() -> None:
    """Run a deterministic, mock-only fault scenario without touching FAL."""
    scenario = os.getenv('VIDEO_GENERATION_MOCK_SCENARIO', 'success').strip().lower()
    delay = _positive_float_env('VIDEO_GENERATION_MOCK_DELAY_SECONDS', _MOCK_VIDEO_DELAY_SECONDS)
    if scenario == 'slow':
        delay = _positive_float_env('VIDEO_GENERATION_MOCK_SLOW_SECONDS', 5.0)
    await asyncio.sleep(delay)
    errors = {
        'provider_timeout': 'video_provider_timeout',
        'provider_failure': 'video_provider_failed',
        'rate_limit': 'video_provider_rate_limited',
        'malformed_result': 'video_result_missing',
        'oversized_result': 'video_result_too_large',
        'delivery_failure': 'video_delivery_failed',
    }
    if scenario in {'success', 'slow'}:
        return
    code = errors.get(scenario)
    if code is None:
        raise VideoExecutionError('video_mock_scenario_invalid')
    # Mock failures always remain refundable: provider_completed must stay False.
    raise VideoExecutionError(code)


def _duration_seconds(params: dict[str, object]) -> int:
    value = params.get('duration', '5')
    try:
        return max(1, round(float(value)))
    except (TypeError, ValueError):
        return 5


async def _upload_mock_file(
    request: Request,
    user: object,
    source: Path | bytes,
    filename: str,
    content_type: str,
):
    """Upload an in-memory mock asset through the upstream file handler.

    ``source`` may be a ``Path`` (read on a thread to avoid blocking the event
    loop) or raw ``bytes`` already resident in memory (e.g. a Pexels clip).
    """
    return await _upload_video_file(
        request,
        user,
        source,
        filename,
        content_type,
        metadata={'video_generation_mock': True},
    )


async def _upload_video_file(
    request: Request,
    user: object,
    source: Path | bytes,
    filename: str,
    content_type: str,
    *,
    metadata: dict[str, object],
):
    global upload_file_handler
    if upload_file_handler is None:
        from open_webui.routers.files import upload_file_handler as upstream_upload_file_handler

        upload_file_handler = upstream_upload_file_handler

    if isinstance(source, (bytes, bytearray)):
        stream = io.BytesIO(bytes(source))
    else:
        stream = source.open('rb')
    try:
        return await upload_file_handler(
            request,
            file=UploadFile(
                file=stream,
                filename=filename,
                headers={'content-type': content_type},
            ),
            metadata=metadata,
            process=False,
            user=user,
        )
    finally:
        stream.close()


async def _finalize_mock_video(
    request: Request,
    user: object,
    task: VideoTaskResponse,
    session: AsyncSession,
) -> dict[str, object]:
    # Try the Pexels mock source first: it fetches a fresh random clip from the
    # Pexels Videos API when PEXELS_API_KEY is configured, and returns None when
    # the key is absent or any fetch/parse fails — in which case we fall back to
    # the bundled static welcome.mp4 / welcome.webp assets so the mock path
    # keeps working without the key. Mock data stays isolated from the default
    # production path either way; nothing here is wired into real generation.
    clip = await fetch_pexels_mock_clip()
    if clip is not None:
        return await _finalize_clip_mock_video(request, user, task, session, clip)
    if not _MOCK_VIDEO_PATH.is_file() or not _MOCK_POSTER_PATH.is_file():
        raise RuntimeError('video mock assets are missing')
    # File uploads commit through their own sessions. Keep these writes sequential so
    # SQLite does not have to arbitrate two writers for the same generated result.
    video_file = await _upload_mock_file(request, user, _MOCK_VIDEO_PATH, 'generated-video.mp4', 'video/mp4')
    poster_file = await _upload_mock_file(
        request,
        user,
        _MOCK_POSTER_PATH,
        'generated-video-poster.webp',
        'image/webp',
    )
    created_at = int(video_file.created_at or _now())
    duration = _duration_seconds(task.params)
    creation_id = uuid4().hex
    session.add(
        CreationMediaItem(
            id=creation_id,
            user_id=getattr(user, 'id'),
            kind='video',
            file_id=video_file.id,
            poster_file_id=poster_file.id,
            duration_seconds=duration,
            caption=None,
            prompt=task.prompt,
            negative_prompt=(str(task.params['negative_prompt']) if task.params.get('negative_prompt') else None),
            model_id=task.model_id,
            model_name_snapshot=None,
            task=task.task,
            params_json=dict(task.params),
            reference_file_ids_json=[asset.file_id for asset in task.assets] or None,
            source='web',
            batch_id=task.id,
            soft_deleted=False,
            created_at=created_at,
            updated_at=created_at,
        )
    )
    await session.flush()

    return VideoTaskResult(
        creation_id=creation_id,
        file_id=video_file.id,
        poster_file_id=poster_file.id,
        url=str(request.app.url_path_for('get_file_content_by_id', id=video_file.id)),
        poster_url=str(request.app.url_path_for('get_file_content_by_id', id=poster_file.id)),
        duration_seconds=duration,
    ).model_dump()


async def _finalize_clip_mock_video(
    request: Request,
    user: object,
    task: VideoTaskResponse,
    session: AsyncSession,
    clip: PexelsMockClip,
) -> dict[str, object]:
    """Persist a Pexels-sourced mock clip through the same creation pipeline.

    If Pexels returned a poster image we use it verbatim; otherwise we synthesize
    a webp poster from the first frame of the downloaded video via pyav/Pillow.
    """
    poster_bytes = clip.poster_bytes
    poster_content_type = clip.poster_content_type or 'image/jpeg'
    if not poster_bytes:
        synthesized = extract_poster_from_video(clip.video_bytes)
        if synthesized is not None:
            poster_bytes, poster_content_type = synthesized
        else:
            # No Pexels poster and frame extraction unavailable — fall back to the
            # static welcome poster so the result still has a preview image.
            if not _MOCK_POSTER_PATH.is_file():
                raise RuntimeError('video mock assets are missing')
            poster_bytes = await asyncio.to_thread(_MOCK_POSTER_PATH.read_bytes)
            poster_content_type = 'image/webp'

    if poster_content_type == 'image/jpeg':
        poster_filename_ext = 'generated-video-poster.jpg'
    elif poster_content_type == 'image/webp':
        poster_filename_ext = 'generated-video-poster.webp'
    else:
        poster_filename_ext = 'generated-video-poster.bin'

    # File uploads commit through their own sessions. Keep these writes sequential so
    # SQLite does not have to arbitrate two writers for the same generated result.
    video_file = await _upload_mock_file(request, user, clip.video_bytes, 'generated-video.mp4', 'video/mp4')
    poster_file = await _upload_mock_file(request, user, poster_bytes, poster_filename_ext, poster_content_type)
    created_at = int(video_file.created_at or _now())
    # Prefer the real clip duration reported by Pexels; fall back to the task's
    # configured duration when the API omits it.
    duration = clip.duration_seconds or _duration_seconds(task.params)
    creation_id = uuid4().hex
    session.add(
        CreationMediaItem(
            id=creation_id,
            user_id=getattr(user, 'id'),
            kind='video',
            file_id=video_file.id,
            poster_file_id=poster_file.id,
            duration_seconds=duration,
            caption=None,
            prompt=task.prompt,
            negative_prompt=(str(task.params['negative_prompt']) if task.params.get('negative_prompt') else None),
            model_id=task.model_id,
            model_name_snapshot=None,
            task=task.task,
            params_json=dict(task.params),
            reference_file_ids_json=[asset.file_id for asset in task.assets] or None,
            source='web',
            batch_id=task.id,
            soft_deleted=False,
            created_at=created_at,
            updated_at=created_at,
        )
    )
    await session.flush()

    return VideoTaskResult(
        creation_id=creation_id,
        file_id=video_file.id,
        poster_file_id=poster_file.id,
        url=str(request.app.url_path_for('get_file_content_by_id', id=video_file.id)),
        poster_url=str(request.app.url_path_for('get_file_content_by_id', id=poster_file.id)),
        duration_seconds=duration,
    ).model_dump()


async def _finalize_real_video(
    request: Request,
    user: object,
    task: VideoTaskResponse,
    session: AsyncSession,
    output: VideoExecutionOutput,
) -> dict[str, object]:
    uploaded_files: list[object] = []
    try:
        poster = await asyncio.to_thread(extract_poster_from_video, output.video_path)
        if poster is None:
            if not _MOCK_POSTER_PATH.is_file():
                raise VideoExecutionError('video_poster_generation_failed', provider_completed=True)
            poster_bytes = await asyncio.to_thread(_MOCK_POSTER_PATH.read_bytes)
            poster_content_type = 'image/webp'
        else:
            poster_bytes, poster_content_type = poster
        poster_filename = (
            'generated-video-poster.jpg' if poster_content_type == 'image/jpeg' else 'generated-video-poster.webp'
        )
        metadata = {'video_generation_provider': 'fal', 'video_generation_mock': False}
        video_file = await _upload_video_file(
            request,
            user,
            output.video_path,
            'generated-video.mp4',
            output.content_type,
            metadata=metadata,
        )
        uploaded_files.append(video_file)
        poster_file = await _upload_video_file(
            request,
            user,
            poster_bytes,
            poster_filename,
            poster_content_type,
            metadata=metadata,
        )
        uploaded_files.append(poster_file)
        created_at = int(video_file.created_at or _now())
        duration = output.duration_seconds or _duration_seconds(task.params)
        creation_id = uuid4().hex
        session.add(
            CreationMediaItem(
                id=creation_id,
                user_id=getattr(user, 'id'),
                kind='video',
                file_id=video_file.id,
                poster_file_id=poster_file.id,
                duration_seconds=duration,
                caption=None,
                prompt=task.prompt,
                negative_prompt=(str(task.params['negative_prompt']) if task.params.get('negative_prompt') else None),
                model_id=task.model_id,
                model_name_snapshot=None,
                task=task.task,
                params_json=dict(task.params),
                reference_file_ids_json=[asset.file_id for asset in task.assets] or None,
                source='web',
                batch_id=task.id,
                soft_deleted=False,
                created_at=created_at,
                updated_at=created_at,
            )
        )
        await session.flush()
        return VideoTaskResult(
            creation_id=creation_id,
            file_id=video_file.id,
            poster_file_id=poster_file.id,
            url=str(request.app.url_path_for('get_file_content_by_id', id=video_file.id)),
            poster_url=str(request.app.url_path_for('get_file_content_by_id', id=poster_file.id)),
            duration_seconds=duration,
        ).model_dump()
    except asyncio.CancelledError as error:
        setattr(error, 'provider_completed', True)
        await _cleanup_generated_files(uploaded_files)
        raise
    except Exception as error:
        await _cleanup_generated_files(uploaded_files)
        if isinstance(error, VideoExecutionError):
            raise
        raise VideoExecutionError('video_delivery_failed', str(error), provider_completed=True) from error


async def _cleanup_generated_files(files: list[object]) -> None:
    for file in reversed(files):
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


async def _cleanup_result_files(result: dict[str, object] | None) -> None:
    if result is None:
        return
    files = []
    for key in ('file_id', 'poster_file_id'):
        file_id = result.get(key)
        if isinstance(file_id, str):
            file = await Files.get_file_by_id(file_id)
            if file is not None:
                files.append(file)
    await _cleanup_generated_files(files)
