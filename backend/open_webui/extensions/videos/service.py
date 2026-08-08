from __future__ import annotations

import asyncio
import io
import logging
import time
from pathlib import Path
from uuid import uuid4

from fastapi import Request
from open_webui.extensions.creations.db import creation_session
from open_webui.extensions.creations.models import CreationMediaItem, VideoGenerationTask
from open_webui.extensions.creations.schemas import decode_keyset_cursor, encode_keyset_cursor
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.fal_catalog.video_schemas import FalVideoModelDefinition
from open_webui.extensions.videos.billing import (
    begin_video_usage,
    credit_session,
    mark_usage_succeeded_in_session,
    mark_video_usage_failed,
    mark_video_usage_invoking,
)
from open_webui.extensions.videos.catalog import build_video_provider_payload
from open_webui.extensions.videos.pexels_mock import (
    PexelsMockClip,
    extract_poster_from_video,
    fetch_pexels_mock_clip,
)
from open_webui.extensions.videos.schemas import (
    VideoAssetReference,
    VideoTaskListResponse,
    VideoTaskResponse,
    VideoTaskResult,
    VideoTaskSubmitForm,
)
from open_webui.models.files import Files
from sqlalchemy import and_, delete, desc, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile

log = logging.getLogger(__name__)
upload_file_handler = None  # lazily bound; tests replace this module-level seam

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
_MOCK_VIDEO_PATH = _REPOSITORY_ROOT / 'static' / 'assets' / 'welcome.mp4'
_MOCK_POSTER_PATH = _REPOSITORY_ROOT / 'static' / 'assets' / 'welcome.webp'


def _now() -> int:
    return int(time.time())


def _result(value: object) -> VideoTaskResult | None:
    if not isinstance(value, dict):
        return None
    try:
        return VideoTaskResult.model_validate(value)
    except ValueError:
        return None


def _response(task: VideoGenerationTask) -> VideoTaskResponse:
    assets = task.assets_json if isinstance(task.assets_json, list) else []
    return VideoTaskResponse(
        id=task.id,
        status=task.status,
        task=task.task,
        prompt=task.prompt,
        model_id=task.model_id,
        params=task.params_json if isinstance(task.params_json, dict) else {},
        assets=tuple(VideoAssetReference.model_validate(item) for item in assets),
        result=_result(task.result_json),
        error_code=task.error_code,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        updated_at=task.updated_at,
    )


async def validate_video_assets(
    submission: VideoTaskSubmitForm,
    definition: FalVideoModelDefinition,
    user_id: str,
) -> None:
    constraints = {item.role: item for item in definition.asset_inputs or ()}
    for reference in submission.assets:
        file = await Files.get_file_by_id_and_user_id(reference.file_id, user_id)
        if file is None:
            raise ValueError(f'video_asset_not_found:{reference.role}')
        constraint = constraints[reference.role]
        metadata = file.meta if isinstance(file.meta, dict) else {}
        content_type = metadata.get('content_type')
        size = metadata.get('size')
        if content_type not in constraint.mime_types:
            raise ValueError(f'invalid_video_asset_type:{reference.role}')
        if isinstance(size, int) and size > constraint.max_bytes:
            raise ValueError(f'video_asset_too_large:{reference.role}')


async def create_video_task(
    session: AsyncSession,
    *,
    user_id: str,
    idempotency_key: str,
    submission: VideoTaskSubmitForm,
) -> tuple[VideoTaskResponse, bool]:
    existing = await session.scalar(
        select(VideoGenerationTask).where(
            VideoGenerationTask.user_id == user_id,
            VideoGenerationTask.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return _response(existing), False

    definition, _provider_payload, safe_params = build_video_provider_payload(submission)
    await validate_video_assets(submission, definition, user_id)
    now = _now()
    task = VideoGenerationTask(
        id=str(uuid4()),
        user_id=user_id,
        idempotency_key=idempotency_key,
        status='queued',
        task=submission.task,
        prompt=submission.prompt,
        model_id=submission.model,
        params_json=safe_params,
        assets_json=[item.model_dump() for item in submission.assets],
        result_json=None,
        error_code=None,
        usage_id=None,
        created_at=now,
        started_at=None,
        completed_at=None,
        updated_at=now,
    )
    session.add(task)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raced = await session.scalar(
            select(VideoGenerationTask).where(
                VideoGenerationTask.user_id == user_id,
                VideoGenerationTask.idempotency_key == idempotency_key,
            )
        )
        if raced is None:
            raise
        return _response(raced), False
    return _response(task), True


async def get_video_task(session: AsyncSession, user_id: str, task_id: str) -> VideoTaskResponse | None:
    task = await session.scalar(
        select(VideoGenerationTask).where(
            VideoGenerationTask.id == task_id,
            VideoGenerationTask.user_id == user_id,
        )
    )
    return _response(task) if task is not None else None


async def list_video_tasks(
    session: AsyncSession,
    user_id: str,
    limit: int,
    cursor: str | None = None,
) -> VideoTaskListResponse:
    statement = select(VideoGenerationTask).where(VideoGenerationTask.user_id == user_id)
    if cursor:
        cursor_created_at, cursor_id = decode_keyset_cursor(cursor)
        statement = statement.where(
            or_(
                VideoGenerationTask.created_at < cursor_created_at,
                and_(
                    VideoGenerationTask.created_at == cursor_created_at,
                    VideoGenerationTask.id < cursor_id,
                ),
            )
        )
    rows = (
        (
            await session.execute(
                statement.order_by(
                    desc(VideoGenerationTask.created_at),
                    desc(VideoGenerationTask.id),
                ).limit(limit + 1)
            )
        )
        .scalars()
        .all()
    )
    page = rows[:limit]
    next_cursor = encode_keyset_cursor(page[-1].created_at, page[-1].id) if len(rows) > limit and page else None
    return VideoTaskListResponse(
        items=tuple(_response(item) for item in page),
        next_cursor=next_cursor,
    )


async def delete_video_task(session: AsyncSession, user_id: str, task_id: str) -> bool:
    result = await session.execute(
        delete(VideoGenerationTask).where(
            VideoGenerationTask.id == task_id,
            VideoGenerationTask.user_id == user_id,
        )
    )
    await session.commit()
    return bool(result.rowcount)


async def _set_task_state(
    task_id: str,
    status: str,
    *,
    result: dict[str, object] | None = None,
    error_code: str | None = None,
) -> None:
    now = _now()
    values: dict[str, object] = {'status': status, 'updated_at': now, 'error_code': error_code}
    if status == 'running':
        values['started_at'] = now
    if status in {'succeeded', 'failed'}:
        values['completed_at'] = now
    if result is not None:
        values['result_json'] = result
    async with creation_session() as session:
        await session.execute(update(VideoGenerationTask).where(VideoGenerationTask.id == task_id).values(**values))
        await session.commit()


async def _set_task_usage_id(task_id: str, usage_id: str) -> None:
    async with creation_session() as session:
        await session.execute(
            update(VideoGenerationTask)
            .where(VideoGenerationTask.id == task_id)
            .values(usage_id=usage_id, updated_at=_now())
        )
        await session.commit()


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
    global upload_file_handler
    if upload_file_handler is None:
        from open_webui.routers.files import upload_file_handler as upstream_upload_file_handler

        upload_file_handler = upstream_upload_file_handler

    if isinstance(source, (bytes, bytearray)):
        payload = bytes(source)
    else:
        payload = await asyncio.to_thread(source.read_bytes)
    return await upload_file_handler(
        request,
        file=UploadFile(
            file=io.BytesIO(payload),
            filename=filename,
            headers={'content-type': content_type},
        ),
        metadata={'video_generation_mock': True},
        process=False,
        user=user,
    )


def _duration_seconds(params: dict[str, object]) -> int:
    value = params.get('duration', '5')
    try:
        return max(1, round(float(value)))
    except (TypeError, ValueError):
        return 5


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
    video_file = await _upload_mock_file(
        request, user, clip.video_bytes, 'generated-video.mp4', 'video/mp4'
    )
    poster_file = await _upload_mock_file(
        request, user, poster_bytes, poster_filename_ext, poster_content_type
    )
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


async def run_video_task(
    task_id: str,
    request: Request,
    user: object,
) -> None:
    await _set_task_state(task_id, 'running')
    usage_id: str | None = None
    try:
        async with creation_session() as session:
            task = await get_video_task(session, getattr(user, 'id'), task_id)
        if task is None:
            return
        begin = await begin_video_usage(user, task)
        if begin.outcome != 'new':
            raise RuntimeError(f'unexpected video usage outcome: {begin.outcome}')
        usage_id = begin.usage.id
        await _set_task_usage_id(task_id, usage_id)
        await mark_video_usage_invoking(usage_id)
        await asyncio.sleep(1.2)
        async with credit_session() as terminal_session, terminal_session.begin():
            result = await _finalize_mock_video(request, user, task, terminal_session)
            changed = await mark_usage_succeeded_in_session(
                terminal_session,
                usage_id,
                [str(result['url'])],
            )
            if changed != 1:
                raise RuntimeError('video usage success transition failed')
        await _set_task_state(task_id, 'succeeded', result=result)
    except asyncio.CancelledError:
        await _set_task_state(task_id, 'failed', error_code='server_shutdown')
        raise
    except CreditError as error:
        if usage_id is not None:
            await mark_video_usage_failed(usage_id, error.code)
        await _set_task_state(task_id, 'failed', error_code=error.code[:64])
    except Exception:
        log.exception('Mock video generation task %s failed', task_id)
        if usage_id is not None:
            await mark_video_usage_failed(usage_id, 'video_generation_failed')
        await _set_task_state(task_id, 'failed', error_code='video_generation_failed')


def schedule_video_task(request: Request, task_id: str, user: object) -> None:
    running: set[asyncio.Task] = request.app.state.video_generation_tasks
    task = asyncio.create_task(run_video_task(task_id, request, user))
    running.add(task)
    task.add_done_callback(running.discard)


async def fail_incomplete_video_tasks() -> int:
    now = _now()
    async with creation_session() as session:
        result = await session.execute(
            update(VideoGenerationTask)
            .where(VideoGenerationTask.status.in_(('queued', 'running')))
            .values(
                status='failed',
                error_code='server_restarted',
                completed_at=now,
                updated_at=now,
            )
        )
        await session.commit()
        return int(result.rowcount or 0)


async def shutdown_video_tasks(app) -> None:
    running: set[asyncio.Task] = getattr(app.state, 'video_generation_tasks', set())
    for task in tuple(running):
        task.cancel()
    if running:
        await asyncio.gather(*tuple(running), return_exceptions=True)
    running.clear()


__all__ = [
    'create_video_task',
    'delete_video_task',
    'fail_incomplete_video_tasks',
    'get_video_task',
    'list_video_tasks',
    'schedule_video_task',
    'shutdown_video_tasks',
]
