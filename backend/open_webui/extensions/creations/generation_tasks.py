from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from fastapi import Request
from open_webui.extensions.creations.db import creation_session
from open_webui.extensions.creations.models import (
    CreationMediaItem,
    CreationPost,
    CreationPostMedia,
    ImageGenerationTask,
)
from open_webui.extensions.creations.schemas import (
    ImageGenerationTaskListResponse,
    ImageGenerationTaskResponse,
    decode_keyset_cursor,
    encode_keyset_cursor,
)
from sqlalchemy import and_, delete, desc, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

_PRIVATE_PAYLOAD_KEYS = frozenset({'prompt', 'image', 'mask', 'mask_url', 'mask_image_url'})
_TERMINAL_STATUSES = frozenset({'succeeded', 'failed'})


class GenerationTaskNotCancellable(Exception):
    """The caller owns the task, but no live worker can be cancelled."""


def _now() -> int:
    return int(time.time())


def _safe_params(payload: dict[str, Any]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if key not in _PRIVATE_PAYLOAD_KEYS and value is not None and isinstance(value, (str, int, float, bool))
    }


def _response(task: ImageGenerationTask) -> ImageGenerationTaskResponse:
    result = task.result_json if isinstance(task.result_json, list) else []
    return ImageGenerationTaskResponse(
        id=task.id,
        status=task.status,
        kind=task.kind,
        prompt=task.prompt,
        model_id=task.model_id,
        params=task.params_json if isinstance(task.params_json, dict) else None,
        expected_count=task.expected_count,
        result=tuple(item for item in result if isinstance(item, dict)),
        error_code=task.error_code,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        updated_at=task.updated_at,
    )


async def create_generation_task(
    session: AsyncSession,
    *,
    user_id: str,
    idempotency_key: str,
    kind: str,
    payload: dict[str, Any],
) -> tuple[ImageGenerationTaskResponse, bool]:
    existing = (
        await session.execute(
            select(ImageGenerationTask).where(
                ImageGenerationTask.user_id == user_id,
                ImageGenerationTask.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return _response(existing), False

    now = _now()
    task = ImageGenerationTask(
        id=str(uuid4()),
        user_id=user_id,
        idempotency_key=idempotency_key,
        status='queued',
        kind=kind,
        prompt=str(payload.get('prompt') or ''),
        model_id=payload.get('model') if isinstance(payload.get('model'), str) else None,
        params_json=_safe_params(payload),
        expected_count=max(1, int(payload.get('n') or 1)),
        result_json=[],
        error_code=None,
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
        raced = (
            await session.execute(
                select(ImageGenerationTask).where(
                    ImageGenerationTask.user_id == user_id,
                    ImageGenerationTask.idempotency_key == idempotency_key,
                )
            )
        ).scalar_one()
        return _response(raced), False
    return _response(task), True


async def get_generation_task(session: AsyncSession, user_id: str, task_id: str) -> ImageGenerationTaskResponse | None:
    task = (
        await session.execute(
            select(ImageGenerationTask).where(
                ImageGenerationTask.id == task_id,
                ImageGenerationTask.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    return _response(task) if task is not None else None


async def delete_generation_task(session: AsyncSession, user_id: str, task_id: str) -> bool:
    task = await session.scalar(
        select(ImageGenerationTask).where(
            ImageGenerationTask.id == task_id,
            ImageGenerationTask.user_id == user_id,
        )
    )
    if task is None:
        return False

    # New task-backed generations use task.id as their creation batch_id. Keep
    # the legacy credit-usage mapping so batches created before this change are
    # cleaned up by the same owner-scoped transaction as well.
    from open_webui.extensions.credits.models import CreditUsage

    legacy_usage_id = await session.scalar(
        select(CreditUsage.id).where(
            CreditUsage.user_id == user_id,
            CreditUsage.idempotency_key == task.idempotency_key,
        )
    )
    batch_ids = {task.id}
    if legacy_usage_id:
        batch_ids.add(legacy_usage_id)
    creation_ids = select(CreationMediaItem.id).where(
        CreationMediaItem.user_id == user_id,
        CreationMediaItem.batch_id.in_(batch_ids),
    )
    post_ids = select(CreationPostMedia.post_id).where(CreationPostMedia.creation_id.in_(creation_ids))
    now = _now()
    await session.execute(
        update(CreationPost)
        .where(CreationPost.id.in_(post_ids), CreationPost.status != 'hidden')
        .values(status='withdrawn', updated_at=now)
    )
    await session.execute(
        update(CreationMediaItem)
        .where(
            CreationMediaItem.user_id == user_id,
            CreationMediaItem.batch_id.in_(batch_ids),
        )
        .values(soft_deleted=True, updated_at=now)
    )
    result = await session.execute(
        delete(ImageGenerationTask).where(
            ImageGenerationTask.id == task_id,
            ImageGenerationTask.user_id == user_id,
        )
    )
    await session.commit()
    return bool(result.rowcount)


async def list_generation_tasks(
    session: AsyncSession, user_id: str, limit: int, cursor: str | None = None, since: int | None = None
) -> ImageGenerationTaskListResponse:
    # keyset 分页：cursor 锁定上一页末条 (created_at, id)，取更旧的记录。
    # 多查 1 条用 hasNext 判断，避免总条数恰为页大小整数倍时多返回一个空页游标
    # （与 service.list_personal_creations 的 limit+1 模式一致）。
    stmt = select(ImageGenerationTask).where(ImageGenerationTask.user_id == user_id)
    # 创作页只展示最近 7 天的任务，更早的需到「我的作品」里查看。
    # 进行中的任务（queued/running）不受时间窗限制，避免轮询时被过滤掉而看不到进度。
    if since is not None:
        stmt = stmt.where(
            or_(
                ImageGenerationTask.created_at >= since,
                ImageGenerationTask.status.in_(['queued', 'running']),
            )
        )
    if cursor:
        cursor_created_at, cursor_id = decode_keyset_cursor(cursor)
        stmt = stmt.where(
            or_(
                ImageGenerationTask.created_at < cursor_created_at,
                and_(
                    ImageGenerationTask.created_at == cursor_created_at,
                    ImageGenerationTask.id < cursor_id,
                ),
            )
        )
    rows = (
        (
            await session.execute(
                stmt.order_by(desc(ImageGenerationTask.created_at), desc(ImageGenerationTask.id)).limit(limit + 1)
            )
        )
        .scalars()
        .all()
    )

    page = rows[:limit]
    next_cursor = encode_keyset_cursor(page[-1].created_at, page[-1].id) if len(rows) > limit and page else None
    return ImageGenerationTaskListResponse(items=tuple(_response(task) for task in page), next_cursor=next_cursor)


async def _set_task_state(
    task_id: str,
    *,
    status: str,
    result: list[dict[str, object]] | None = None,
    error_code: str | None = None,
) -> None:
    now = _now()
    values: dict[str, object] = {'status': status, 'updated_at': now}
    if status == 'running':
        values['started_at'] = now
    if status in {'succeeded', 'failed'}:
        values['completed_at'] = now
    if result is not None:
        values['result_json'] = result
    values['error_code'] = error_code
    async with creation_session() as session:
        await session.execute(update(ImageGenerationTask).where(ImageGenerationTask.id == task_id).values(**values))
        await session.commit()


async def _publish_image_task_event(
    app: object,
    task_id: str,
    user_id: str,
    status: str,
    *,
    error_code: str | None = None,
) -> None:
    """广播图片任务状态变更到 SSE 事件总线。无订阅者时安全跳过。"""
    from open_webui.extensions.creations.events import publish_generation_event

    payload: dict[str, object] = {'kind': 'image'}
    if error_code is not None:
        payload['error_code'] = error_code
    try:
        await publish_generation_event(
            app,
            kind='image',
            task_id=task_id,
            status=status,
            user_id=user_id,
            payload=payload if error_code is not None else None,
        )
    except Exception:
        # SSE 是辅助通知通道，失败不能改变已经持久化的任务终态。
        log.exception('Could not publish %s event for image task %s', status, task_id)


def _public_result(result: object) -> list[dict[str, object]]:
    if not isinstance(result, list):
        return []
    public: list[dict[str, object]] = []
    for item in result:
        if isinstance(item, dict) and isinstance(item.get('url'), str):
            public.append({'url': item['url']})
    return public


def _error_code(error: Exception) -> str:
    code = getattr(error, 'code', None)
    if isinstance(code, str) and code:
        return code[:64]
    return 'image_generation_failed'


async def run_generation_task(task_id: str, request: Request, user: object, form: object, kind: str) -> None:
    user_id = getattr(user, 'id', '')
    result: object | None = None
    try:
        await _set_task_state(task_id, status='running')
        await _publish_image_task_event(request.app, task_id, user_id, 'running')
        from open_webui.routers.images import image_edits, image_generations

        if kind == 'image-to-image':
            result = await image_edits(
                request,
                form,
                'direct',
                metadata={'generation_task_id': task_id},
                user=user,
            )
        else:
            result = await image_generations(
                request,
                form,
                'direct',
                metadata={'generation_task_id': task_id},
                user=user,
            )
        await _set_task_state(task_id, status='succeeded', result=_public_result(result))
        await _publish_image_task_event(request.app, task_id, user_id, 'succeeded')
    except asyncio.CancelledError as error:
        # The billed call already returned a terminal result. A cancellation
        # arriving in the tiny window before the task-row update is too late;
        # preserve the completed result rather than reporting a false refund.
        if result is not None:
            try:
                await _set_task_state(task_id, status='succeeded', result=_public_result(result))
            except Exception:
                log.exception('Could not restore succeeded state for interrupted image task %s', task_id)
            try:
                await _publish_image_task_event(request.app, task_id, user_id, 'succeeded')
            except Exception:
                log.exception('Could not publish succeeded state for interrupted image task %s', task_id)
            return
        error_code = (
            'generation_cancelled' if error.args and error.args[0] == 'generation_cancelled' else 'server_shutdown'
        )
        try:
            await _set_task_state(task_id, status='failed', error_code=error_code)
        except Exception:
            log.exception('Could not persist interrupted image task %s', task_id)
        try:
            await _publish_image_task_event(request.app, task_id, user_id, 'failed', error_code=error_code)
        except Exception:
            log.exception('Could not publish interrupted image task %s', task_id)
        raise
    except Exception as error:
        log.exception('Image generation task %s failed', task_id)
        code = _error_code(error)
        await _set_task_state(task_id, status='failed', error_code=code)
        await _publish_image_task_event(request.app, task_id, user_id, 'failed', error_code=code)


def schedule_generation_task(
    request: Request,
    *,
    task_id: str,
    user: object,
    form: object,
    kind: str,
    on_finished: Callable[[], Awaitable[None]] | None = None,
) -> None:
    running: dict[str, asyncio.Task] = request.app.state.creation_generation_tasks
    task = asyncio.create_task(run_generation_task(task_id, request, user, form, kind))
    running[task_id] = task

    def discard_finished(finished: asyncio.Task) -> None:
        if running.get(task_id) is finished:
            running.pop(task_id, None)
        if on_finished is not None:
            asyncio.create_task(on_finished())

    task.add_done_callback(discard_finished)


async def cancel_generation_task(
    request: Request,
    session: AsyncSession,
    user_id: str,
    task_id: str,
) -> ImageGenerationTaskResponse | None:
    task = await get_generation_task(session, user_id, task_id)
    if task is None or task.status in _TERMINAL_STATUSES:
        return task

    running: dict[str, asyncio.Task] = getattr(
        request.app.state,
        'creation_generation_tasks',
        {},
    )
    worker = running.get(task_id)
    if worker is None or worker.done():
        raise GenerationTaskNotCancellable()

    worker.cancel('generation_cancelled')
    await asyncio.gather(worker, return_exceptions=True)

    async with creation_session() as fresh_session:
        cancelled = await get_generation_task(fresh_session, user_id, task_id)
    if cancelled is None:
        return None
    if cancelled.status not in _TERMINAL_STATUSES:
        await _set_task_state(task_id, status='failed', error_code='generation_cancelled')
        async with creation_session() as fresh_session:
            cancelled = await get_generation_task(fresh_session, user_id, task_id)
    return cancelled


async def fail_incomplete_generation_tasks() -> int:
    now = _now()
    async with creation_session() as session:
        result = await session.execute(
            update(ImageGenerationTask)
            .where(ImageGenerationTask.status.in_(('queued', 'running')))
            .values(status='failed', error_code='server_restarted', completed_at=now, updated_at=now)
        )
        await session.commit()
        return int(result.rowcount or 0)


async def shutdown_generation_tasks(app) -> None:
    running: dict[str, asyncio.Task] = getattr(app.state, 'creation_generation_tasks', {})
    for task in tuple(running.values()):
        task.cancel()
    if running:
        await asyncio.gather(*tuple(running.values()), return_exceptions=True)
    running.clear()


__all__ = [
    'GenerationTaskNotCancellable',
    'cancel_generation_task',
    'create_generation_task',
    'delete_generation_task',
    'fail_incomplete_generation_tasks',
    'get_generation_task',
    'list_generation_tasks',
    'run_generation_task',
    'schedule_generation_task',
    'shutdown_generation_tasks',
]
