from __future__ import annotations

import asyncio
import io
import logging
import os
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from uuid import uuid4

from fastapi import Request
from open_webui.extensions.creations.db import creation_session
from open_webui.extensions.creations.models import CreationMediaItem, VideoGenerationTask
from open_webui.extensions.creations.schemas import decode_keyset_cursor, encode_keyset_cursor
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.models import CreditUsage
from open_webui.extensions.fal_catalog.video_schemas import FalVideoModelDefinition
from open_webui.extensions.videos.billing import (
    begin_video_usage,
    credit_session,
    heartbeat_video_usage,
    mark_usage_succeeded_in_session,
    mark_video_usage_failed,
    mark_video_usage_invoking,
)
from open_webui.extensions.videos.catalog import build_video_provider_payload
from open_webui.extensions.videos.executor import (
    FalVideoExecutor,
    VideoExecutionError,
    VideoExecutionOutput,
    resolve_video_executor,
)
from open_webui.extensions.videos.limits import (
    acquire_video_generation_slot,
    release_video_generation_slot,
)
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
from open_webui.models.users import Users
from open_webui.storage.provider import Storage
from sqlalchemy import and_, delete, desc, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile

log = logging.getLogger(__name__)
upload_file_handler = None  # lazily bound; tests replace this module-level seam

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
_MOCK_VIDEO_PATH = _REPOSITORY_ROOT / 'static' / 'assets' / 'welcome.mp4'
_MOCK_POSTER_PATH = _REPOSITORY_ROOT / 'static' / 'assets' / 'welcome.webp'
# Mock 路径的模拟延迟：模拟真实生成耗时，避免 mock 完成过快导致前端轮询异常。
_MOCK_VIDEO_DELAY_SECONDS = 1.2
_RECOVERABLE_VIDEO_ERRORS = frozenset(
    {
        'video_delivery_failed',
        'video_result_download_failed',
        'video_provider_timeout',
    }
)


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


async def get_video_task_by_idempotency_key(
    session: AsyncSession,
    user_id: str,
    idempotency_key: str,
) -> VideoTaskResponse | None:
    task = await session.scalar(
        select(VideoGenerationTask).where(
            VideoGenerationTask.user_id == user_id,
            VideoGenerationTask.idempotency_key == idempotency_key,
        )
    )
    return _response(task) if task is not None else None


def video_task_matches_submission(task: VideoTaskResponse, submission: VideoTaskSubmitForm) -> bool:
    try:
        _definition, _provider_payload, safe_params = build_video_provider_payload(submission)
    except Exception:
        return False
    return bool(
        task.task == submission.task
        and task.model_id == submission.model
        and task.prompt == submission.prompt
        and task.assets == submission.assets
        and task.params == safe_params
    )


async def list_video_tasks(
    session: AsyncSession,
    user_id: str,
    limit: int,
    cursor: str | None = None,
    since: int | None = None,
) -> VideoTaskListResponse:
    statement = select(VideoGenerationTask).where(VideoGenerationTask.user_id == user_id)
    # 创作页只展示最近 7 天的任务，更早的需到「我的作品」里查看。
    # 进行中的任务（queued/running）不受时间窗限制，避免轮询时被过滤掉而看不到进度。
    if since is not None:
        statement = statement.where(
            or_(
                VideoGenerationTask.created_at >= since,
                VideoGenerationTask.status.in_(['queued', 'running']),
            )
        )
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


async def _publish_video_task_event(
    app: object,
    task_id: str,
    user_id: str,
    status: str,
    *,
    error_code: str | None = None,
) -> None:
    """广播视频任务状态变更到 SSE 事件总线。无订阅者时安全跳过。"""
    from open_webui.extensions.creations.events import publish_generation_event

    payload: dict[str, object] | None = None
    if error_code is not None:
        payload = {'kind': 'video', 'error_code': error_code}
    try:
        await publish_generation_event(
            app,
            kind='video',
            task_id=task_id,
            status=status,
            user_id=user_id,
            payload=payload,
        )
    except Exception:
        # SSE 是辅助通知通道，失败不能覆盖已经持久化的任务终态。
        log.exception('Could not publish %s event for video task %s', status, task_id)


async def _set_task_usage_id(task_id: str, usage_id: str, execution_mode: str | None = None) -> None:
    async with creation_session() as session:
        await session.execute(
            update(VideoGenerationTask)
            .where(VideoGenerationTask.id == task_id)
            .values(usage_id=usage_id, execution_mode=execution_mode, updated_at=_now())
        )
        await session.commit()


def _provider_url(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.startswith('https://'):
        return None
    return value[:4096]


async def _persist_provider_submission(task_id: str, payload: dict[str, object]) -> None:
    request_id = payload.get('request_id')
    values: dict[str, object] = {
        'provider_request_id': request_id[:128] if isinstance(request_id, str) else None,
        'provider_status_url': _provider_url(payload, 'status_url'),
        'provider_response_url': _provider_url(payload, 'response_url'),
        'updated_at': _now(),
    }
    await _persist_task_recovery_values(task_id, values)


async def _persist_provider_result_url(task_id: str, result_url: str) -> None:
    if not result_url.startswith('https://'):
        raise VideoExecutionError('video_result_invalid_url', provider_completed=True)
    await _persist_task_recovery_values(
        task_id,
        {'provider_result_url': result_url[:4096], 'updated_at': _now()},
    )


async def _persist_provider_result_for_delivery(task_id: str, result_url: str) -> None:
    await _persist_provider_result_url(task_id, result_url)
    await _increment_delivery_attempts(task_id)


async def _persist_task_recovery_values(task_id: str, values: dict[str, object]) -> None:
    for attempt in range(3):
        try:
            async with creation_session() as session:
                await session.execute(
                    update(VideoGenerationTask).where(VideoGenerationTask.id == task_id).values(**values)
                )
                await session.commit()
            return
        except asyncio.CancelledError:
            raise
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(0.2 * (attempt + 1))


async def _increment_delivery_attempts(task_id: str) -> None:
    async with creation_session() as session:
        await session.execute(
            update(VideoGenerationTask)
            .where(VideoGenerationTask.id == task_id)
            .values(
                delivery_attempts=VideoGenerationTask.delivery_attempts + 1,
                updated_at=_now(),
            )
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


async def run_video_task(  # noqa: C901 - terminal billing and cancellation states must remain coordinated
    task_id: str,
    request: Request,
    user: object,
) -> None:
    user_id = getattr(user, 'id', '')
    usage_id: str | None = None
    result: dict[str, object] | None = None
    usage_succeeded = False
    output: VideoExecutionOutput | None = None
    try:
        await _set_task_state(task_id, 'running')
        await _publish_video_task_event(request.app, task_id, user_id, 'running')
        async with creation_session() as session:
            task = await get_video_task(session, getattr(user, 'id', ''), task_id)
        if task is None:
            return
        executor = resolve_video_executor(request)
        begin = await begin_video_usage(user, task, execution_mode=executor.mode)
        if begin.outcome != 'new':
            raise RuntimeError(f'unexpected video usage outcome: {begin.outcome}')
        usage_id = begin.usage.id
        await _set_task_usage_id(task_id, usage_id, executor.mode)
        await mark_video_usage_invoking(usage_id)
        if isinstance(executor, FalVideoExecutor):
            submission = VideoTaskSubmitForm(
                task=task.task,
                model=task.model_id,
                prompt=task.prompt,
                assets=task.assets,
                params=task.params,
            )
            definition, provider_payload, _safe_params = build_video_provider_payload(submission)
            heartbeat = asyncio.create_task(
                heartbeat_video_usage(usage_id),
                name=f'video-usage-heartbeat:{usage_id}',
            )
            try:
                output = await executor.invoke(
                    request,
                    user,
                    task,
                    definition,
                    provider_payload,
                    on_submitted=lambda payload: _persist_provider_submission(task_id, payload),
                    on_result_url=lambda url: _persist_provider_result_for_delivery(task_id, url),
                )
            finally:
                heartbeat.cancel()
                await asyncio.gather(heartbeat, return_exceptions=True)
        else:
            await _run_mock_scenario()
        async with credit_session() as terminal_session, terminal_session.begin():
            if output is not None:
                result = await _finalize_real_video(request, user, task, terminal_session, output)
            else:
                result = await _finalize_mock_video(request, user, task, terminal_session)
            changed = await mark_usage_succeeded_in_session(
                terminal_session,
                usage_id,
                [str(result['url'])],
            )
            if changed != 1:
                raise RuntimeError('video usage success transition failed')
        usage_succeeded = True
        await _set_task_state(task_id, 'succeeded', result=result)
        await _publish_video_task_event(request.app, task_id, user_id, 'succeeded')
    except asyncio.CancelledError as error:
        # 进程关停会取消运行中的 worker 并进入此分支。尚未提交到 FAL 的任务可退预扣积分；
        # 已提交或已生成结果的任务保留扣费等待对账，避免厂商已收费而平台自动退款。
        # 取消可能恰好落在 terminal_session 提交完成、usage_succeeded 赋值之前。
        # 此时以数据库中的 usage 终态为准，避免 usage=succeeded 而 task=failed。
        if not usage_succeeded and usage_id is not None and result is not None:
            try:
                async with credit_session() as status_session:
                    persisted_status = await status_session.scalar(
                        select(CreditUsage.status).where(CreditUsage.id == usage_id)
                    )
                usage_succeeded = persisted_status == 'succeeded'
            except Exception:
                log.exception('Could not verify terminal usage state for interrupted video task %s', task_id)
        if usage_succeeded and result is not None:
            try:
                await _set_task_state(task_id, 'succeeded', result=result)
            except Exception:
                log.exception('Could not restore succeeded state for interrupted video task %s', task_id)
            try:
                await _publish_video_task_event(request.app, task_id, user_id, 'succeeded')
            except Exception:
                log.exception('Could not publish succeeded state for interrupted video task %s', task_id)
            raise
        provider_was_submitted = bool(
            getattr(error, 'provider_completed', False)
            or getattr(error, 'provider_submitted', False)
            or output is not None
        )
        if usage_id is not None and provider_was_submitted:
            # Keep the invoking usage and task recoverable. The next startup (or
            # periodic recovery pass) will poll/deliver the same FAL request.
            try:
                await _set_task_state(task_id, 'running', error_code='video_recovery_pending')
            except Exception:
                log.exception('Could not persist recoverable interrupted video task %s', task_id)
            raise
        code = 'server_shutdown'
        if usage_id is not None:
            try:
                await mark_video_usage_failed(
                    usage_id,
                    code,
                    restore_prepaid=True,
                )
            except Exception:
                # 计费清理失败不能阻止任务行终态写入，也不能把原始取消异常
                # 替换成次生 DB 异常。后台对账仍可处理未完成 usage。
                log.exception('Could not fail usage for interrupted video task %s', task_id)
        try:
            await _set_task_state(task_id, 'failed', error_code=code)
        except Exception:
            log.exception('Could not persist interrupted video task %s', task_id)
        try:
            await _publish_video_task_event(request.app, task_id, user_id, 'failed', error_code=code)
        except Exception:
            log.exception('Could not publish interrupted video task %s', task_id)
        raise
    except CreditError as error:
        code = error.code[:64]
        if usage_id is not None:
            try:
                await mark_video_usage_failed(
                    usage_id,
                    error.code,
                    restore_prepaid=output is None,
                )
            except Exception:
                # 计费清理失败不能阻止任务行终态写入（与 CancelledError 处理器一致）。
                log.exception('Could not fail usage for video task %s', task_id)
        try:
            await _set_task_state(task_id, 'failed', error_code=code)
        except Exception:
            log.exception('Could not persist failed video task %s', task_id)
        try:
            await _publish_video_task_event(request.app, task_id, user_id, 'failed', error_code=code)
        except Exception:
            log.exception('Could not publish failed video task %s', task_id)
    except VideoExecutionError as error:
        log.exception('Video generation task %s failed with %s', task_id, error.code)
        if usage_id is not None and (
            error.provider_completed or (error.provider_submitted and error.retryable)
        ):
            # FAL has completed or accepted a request whose response is
            # uncertain. Keep the task recoverable and retry only polling,
            # response fetch, download, or local delivery; never submit again.
            await _set_task_state(task_id, 'running', error_code='video_delivery_pending')
            await recover_video_task(task_id, request, user)
            return
        if usage_id is not None:
            try:
                await mark_video_usage_failed(
                    usage_id,
                    error.code,
                    restore_prepaid=not (error.provider_completed or output is not None),
                )
            except Exception:
                log.exception('Could not fail usage for video task %s', task_id)
        try:
            await _set_task_state(task_id, 'failed', error_code=error.code)
        except Exception:
            log.exception('Could not persist failed video task %s', task_id)
        try:
            await _publish_video_task_event(
                request.app,
                task_id,
                user_id,
                'failed',
                error_code=error.code,
            )
        except Exception:
            log.exception('Could not publish failed video task %s', task_id)
    except Exception:
        log.exception('Video generation task %s failed', task_id)
        if usage_succeeded and result is not None:
            try:
                await _set_task_state(task_id, 'succeeded', result=result)
                await _publish_video_task_event(request.app, task_id, user_id, 'succeeded')
            except Exception:
                log.exception('Could not restore committed video success for task %s', task_id)
            return
        await _cleanup_result_files(result)
        if usage_id is not None:
            try:
                await mark_video_usage_failed(
                    usage_id,
                    'video_delivery_failed' if output is not None else 'video_generation_failed',
                    restore_prepaid=output is None,
                )
            except Exception:
                # 计费清理失败不能阻止任务行终态写入（与 CancelledError 处理器一致）。
                log.exception('Could not fail usage for video task %s', task_id)
        try:
            await _set_task_state(
                task_id,
                'failed',
                error_code='video_delivery_failed' if output is not None else 'video_generation_failed',
            )
        except Exception:
            log.exception('Could not persist failed video task %s', task_id)
        try:
            await _publish_video_task_event(
                request.app,
                task_id,
                user_id,
                'failed',
                error_code='video_delivery_failed' if output is not None else 'video_generation_failed',
            )
        except Exception:
            log.exception('Could not publish failed video task %s', task_id)
    finally:
        if output is not None:
            try:
                await asyncio.to_thread(output.video_path.unlink, missing_ok=True)
            except Exception:
                log.exception('Could not remove temporary video result for task %s', task_id)


async def _existing_creation_result(
    request: Request,
    task_id: str,
    user_id: str,
) -> dict[str, object] | None:
    async with creation_session() as session:
        creation = await session.scalar(
            select(CreationMediaItem).where(
                CreationMediaItem.batch_id == task_id,
                CreationMediaItem.user_id == user_id,
                CreationMediaItem.kind == 'video',
                CreationMediaItem.soft_deleted.is_(False),
            )
        )
    if creation is None or not creation.poster_file_id or not creation.duration_seconds:
        return None
    return VideoTaskResult(
        creation_id=creation.id,
        file_id=creation.file_id,
        poster_file_id=creation.poster_file_id,
        url=str(request.app.url_path_for('get_file_content_by_id', id=creation.file_id)),
        poster_url=str(request.app.url_path_for('get_file_content_by_id', id=creation.poster_file_id)),
        duration_seconds=creation.duration_seconds,
    ).model_dump()


async def recover_video_task(task_id: str, request: Request, user: object) -> None:  # noqa: C901
    """Resume a persisted task without issuing a second provider generation POST."""
    user_id = str(getattr(user, 'id', ''))
    output: VideoExecutionOutput | None = None
    usage_id: str | None = None
    result: dict[str, object] | None = None
    usage_succeeded = False
    try:
        async with creation_session() as session:
            row = await session.scalar(select(VideoGenerationTask).where(VideoGenerationTask.id == task_id))
        if row is None or row.status not in {'queued', 'running'}:
            return
        if row.status == 'queued':
            await run_video_task(task_id, request, user)
            return

        task = _response(row)
        usage_id = row.usage_id
        if not usage_id:
            raise VideoExecutionError('video_recovery_state_missing')

        existing_result = await _existing_creation_result(request, task_id, user_id)
        if existing_result is not None:
            result = existing_result
            async with credit_session() as session, session.begin():
                usage_status = await session.scalar(select(CreditUsage.status).where(CreditUsage.id == usage_id))
                if usage_status == 'invoking':
                    changed = await mark_usage_succeeded_in_session(
                        session,
                        usage_id,
                        [str(existing_result['url'])],
                    )
                    if changed != 1:
                        raise RuntimeError('video usage recovery success transition failed')
                elif usage_status != 'succeeded':
                    raise VideoExecutionError('video_recovery_usage_invalid')
            usage_succeeded = True
            await _set_task_state(task_id, 'succeeded', result=existing_result)
            await _publish_video_task_event(request.app, task_id, user_id, 'succeeded')
            return

        if row.execution_mode == 'mock':
            await _run_mock_scenario()
        elif row.execution_mode == 'fal':
            executor = resolve_video_executor(request)
            if not isinstance(executor, FalVideoExecutor):
                raise VideoExecutionError('video_fal_not_configured', retryable=True)
            submission = VideoTaskSubmitForm(
                task=task.task,
                model=task.model_id,
                prompt=task.prompt,
                assets=task.assets,
                params=task.params,
            )
            definition, _provider_payload, _safe_params = build_video_provider_payload(submission)
            await _increment_delivery_attempts(task_id)
            heartbeat = asyncio.create_task(
                heartbeat_video_usage(usage_id),
                name=f'video-recovery-usage-heartbeat:{usage_id}',
            )
            try:
                output = await executor.resume(
                    task,
                    definition,
                    status_url=row.provider_status_url,
                    response_url=row.provider_response_url,
                    result_url=row.provider_result_url,
                    provider_request_id=row.provider_request_id,
                    on_result_url=lambda url: _persist_provider_result_url(task_id, url),
                )
            finally:
                heartbeat.cancel()
                await asyncio.gather(heartbeat, return_exceptions=True)
        else:
            raise VideoExecutionError('video_recovery_state_missing')

        async with credit_session() as terminal_session, terminal_session.begin():
            if output is not None:
                result = await _finalize_real_video(request, user, task, terminal_session, output)
            else:
                result = await _finalize_mock_video(request, user, task, terminal_session)
            changed = await mark_usage_succeeded_in_session(
                terminal_session,
                usage_id,
                [str(result['url'])],
            )
            if changed != 1:
                raise RuntimeError('video usage recovery success transition failed')
        usage_succeeded = True
        await _set_task_state(task_id, 'succeeded', result=result)
        await _publish_video_task_event(request.app, task_id, user_id, 'succeeded')
    except asyncio.CancelledError:
        raise
    except VideoExecutionError as error:
        log.exception('Video recovery task %s failed with %s', task_id, error.code)
        if error.retryable or error.code in _RECOVERABLE_VIDEO_ERRORS:
            await _set_task_state(task_id, 'running', error_code='video_delivery_pending')
            return
        if usage_id is not None:
            await mark_video_usage_failed(
                usage_id,
                error.code,
                restore_prepaid=False,
            )
        await _set_task_state(task_id, 'failed', error_code=error.code)
        await _publish_video_task_event(request.app, task_id, user_id, 'failed', error_code=error.code)
    except Exception:
        log.exception('Video recovery task %s failed', task_id)
        if usage_succeeded and result is not None:
            try:
                await _set_task_state(task_id, 'succeeded', result=result)
                await _publish_video_task_event(request.app, task_id, user_id, 'succeeded')
            except Exception:
                log.exception('Could not restore recovered video success for task %s', task_id)
            return
        await _cleanup_result_files(result)
        await _set_task_state(task_id, 'running', error_code='video_delivery_pending')
    finally:
        if output is not None:
            try:
                await asyncio.to_thread(output.video_path.unlink, missing_ok=True)
            except Exception:
                log.exception('Could not remove recovered temporary video result for task %s', task_id)


def schedule_video_task(
    request: Request,
    task_id: str,
    user: object,
    *,
    on_finished: Callable[[], Awaitable[None]] | None = None,
) -> None:
    running: dict[str, asyncio.Task] = request.app.state.video_generation_tasks

    async def run_and_finish() -> None:
        original_exc: BaseException | None = None
        try:
            await run_video_task(task_id, request, user)
        except BaseException as exc:
            original_exc = exc
            raise
        finally:
            if on_finished is not None:
                try:
                    await on_finished()
                except asyncio.CancelledError:
                    # 如果 try 块已有原始异常在传播，不要让 on_finished 的
                    # CancelledError 替换它（否则日志丢失原始失败原因）。
                    # 无原始异常时正常重抛以遵守取消语义。
                    if original_exc is None:
                        raise
                    log.warning(
                        'on_finished cancelled for video task %s; original exception preserved',
                        task_id,
                    )
                except Exception:
                    # 槽位释放失败需要记录，但不能替换 worker 的原始异常。
                    # 进程内槽位也会随进程退出而回收。
                    log.exception('Could not release generation slot for video task %s', task_id)

    task = asyncio.create_task(run_and_finish())
    running[task_id] = task

    def discard_finished(finished: asyncio.Task) -> None:
        if running.get(task_id) is finished:
            running.pop(task_id, None)

    task.add_done_callback(discard_finished)


def schedule_video_recovery_task(request: Request, task_id: str, user: object) -> bool:
    running: dict[str, asyncio.Task] = request.app.state.video_generation_tasks
    if task_id in running:
        return False

    async def recover_and_release() -> None:
        try:
            await recover_video_task(task_id, request, user)
        finally:
            await release_video_generation_slot(str(getattr(user, 'id', '')))

    task = asyncio.create_task(recover_and_release())
    running[task_id] = task

    def discard_finished(finished: asyncio.Task) -> None:
        if running.get(task_id) is finished:
            running.pop(task_id, None)

    task.add_done_callback(discard_finished)
    return True


async def recover_incomplete_video_tasks(request: Request) -> int:
    async with creation_session() as session:
        rows = (
            (
                await session.execute(
                    select(VideoGenerationTask)
                    .where(VideoGenerationTask.status.in_(('queued', 'running')))
                    .order_by(VideoGenerationTask.created_at, VideoGenerationTask.id)
                )
            )
            .scalars()
            .all()
        )
    scheduled = 0
    for row in rows:
        user = await Users.get_user_by_id(row.user_id)
        if user is None:
            await _set_task_state(row.id, 'failed', error_code='video_user_not_found')
            continue
        try:
            await acquire_video_generation_slot(row.user_id)
        except CreditError:
            continue
        if schedule_video_recovery_task(request, row.id, user):
            scheduled += 1
        else:
            await release_video_generation_slot(row.user_id)
    return scheduled


async def shutdown_video_tasks(app) -> None:
    running: dict[str, asyncio.Task] = getattr(app.state, 'video_generation_tasks', {})
    tasks = tuple(running.values())
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    running.clear()


__all__ = [
    'create_video_task',
    'delete_video_task',
    'get_video_task',
    'get_video_task_by_idempotency_key',
    'list_video_tasks',
    'recover_incomplete_video_tasks',
    'recover_video_task',
    'schedule_video_task',
    'shutdown_video_tasks',
    'video_task_matches_submission',
]
