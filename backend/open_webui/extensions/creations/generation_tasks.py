from __future__ import annotations

import asyncio
import hashlib
import json
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
from open_webui.extensions.creations.task_runtime import (
    publish_task_event_safely,
    schedule_tracked_task,
    task_state_values,
)
from open_webui.extensions.creations.task_states import ACTIVE_GENERATION_TASK_STATUSES
from sqlalchemy import and_, delete, desc, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

_PRIVATE_PAYLOAD_KEYS = frozenset({'prompt', 'image', 'mask', 'mask_url', 'mask_image_url'})
_TERMINAL_STATUSES = frozenset({'succeeded', 'failed'})


class IdempotencyPayloadConflictError(Exception):
    """幂等键命中但载荷不一致（客户端复用了键却改了提示词/参数）。"""


def _now() -> int:
    return int(time.time())


def _safe_params(payload: dict[str, Any]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if key not in _PRIVATE_PAYLOAD_KEYS and value is not None and isinstance(value, (str, int, float, bool))
    }


def _payload_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def _task_matches_payload(task: ImageGenerationTask, *, kind: str, payload: dict[str, Any]) -> bool:
    """幂等重放校验：同键同载荷才复用既有任务。

    同键不同载荷说明客户端复用了键却修改了内容（如网络失败后改了提示词
    或参考图重试）：静默复用旧任务会丢弃新载荷，必须由调用方拒绝。只持久化
    完整载荷摘要，不落库 image/mask 等私有原文。
    """
    if task.kind != kind:
        return False
    return task.payload_sha256 == _payload_sha256(payload)


async def get_generation_task_by_idempotency_key(
    session: AsyncSession,
    user_id: str,
    idempotency_key: str,
    *,
    kind: str,
    payload: dict[str, Any],
) -> ImageGenerationTaskResponse | None:
    """Return an exact idempotent replay before rate/concurrency admission."""
    task = await session.scalar(
        select(ImageGenerationTask).where(
            ImageGenerationTask.user_id == user_id,
            ImageGenerationTask.idempotency_key == idempotency_key,
        )
    )
    if task is None:
        return None
    if not _task_matches_payload(task, kind=kind, payload=payload):
        raise IdempotencyPayloadConflictError(idempotency_key)
    return _response(task)


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


async def _task_by_idempotency_key(
    session: AsyncSession,
    user_id: str,
    idempotency_key: str,
) -> ImageGenerationTask | None:
    return (
        await session.execute(
            select(ImageGenerationTask).where(
                ImageGenerationTask.user_id == user_id,
                ImageGenerationTask.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()


def _new_generation_task(
    *,
    user_id: str,
    idempotency_key: str,
    kind: str,
    payload: dict[str, Any],
) -> ImageGenerationTask:
    now = _now()
    return ImageGenerationTask(
        id=str(uuid4()),
        user_id=user_id,
        idempotency_key=idempotency_key,
        payload_sha256=_payload_sha256(payload),
        status='queued',
        kind=kind,
        prompt=str(payload.get('prompt') or ''),
        model_id=payload.get('model') if isinstance(payload.get('model'), str) else None,
        params_json=_safe_params(payload),
        expected_count=max(1, int(payload.get('n') or 1)),
        result_json=[],
        error_code=None,
        execution_mode=None,
        delivery_attempts=0,
        created_at=now,
        started_at=None,
        completed_at=None,
        updated_at=now,
    )


async def create_generation_task(
    session: AsyncSession,
    *,
    user_id: str,
    idempotency_key: str,
    kind: str,
    payload: dict[str, Any],
) -> tuple[ImageGenerationTaskResponse, bool]:
    existing = await _task_by_idempotency_key(session, user_id, idempotency_key)
    if existing is not None:
        if not _task_matches_payload(existing, kind=kind, payload=payload):
            raise IdempotencyPayloadConflictError(idempotency_key)
        return _response(existing), False

    task = _new_generation_task(
        user_id=user_id,
        idempotency_key=idempotency_key,
        kind=kind,
        payload=payload,
    )
    session.add(task)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raced = await _task_by_idempotency_key(session, user_id, idempotency_key)
        if raced is None:
            raise
        if not _task_matches_payload(raced, kind=kind, payload=payload):
            raise IdempotencyPayloadConflictError(idempotency_key) from None
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

    # 任务型生成的 creation batch_id 恒为 task.id（复盘：未上线无历史包袱，
    # 旧 credit-usage 映射的兼容清理分支已删）。
    creation_ids = select(CreationMediaItem.id).where(
        CreationMediaItem.user_id == user_id,
        CreationMediaItem.batch_id == task.id,
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
            CreationMediaItem.batch_id == task.id,
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
                ImageGenerationTask.status.in_(ACTIVE_GENERATION_TASK_STATUSES),
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
    values = task_state_values(status, now=now, result=result, error_code=error_code)
    async with creation_session() as session:
        await session.execute(update(ImageGenerationTask).where(ImageGenerationTask.id == task_id).values(**values))
        await session.commit()


async def fail_generation_task_scheduling(app: object, task_id: str, user_id: str) -> None:
    """Close a committed queued row when no worker could be scheduled."""
    error_code = 'image_scheduling_failed'
    await _set_task_state(task_id, status='failed', error_code=error_code)
    await _publish_image_task_event(app, task_id, user_id, 'failed', error_code=error_code)


async def set_image_task_execution_mode(task_id: str | None, mode: str) -> None:
    """Persist the paid-provider boundary before the FAL request is submitted."""
    if task_id is None:
        return
    async with creation_session() as session:
        await session.execute(
            update(ImageGenerationTask)
            .where(ImageGenerationTask.id == task_id)
            .values(execution_mode=mode, updated_at=_now())
        )
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
    await publish_task_event_safely(
        app,
        kind='image',
        task_id=task_id,
        user_id=user_id,
        status=status,
        error_code=error_code,
        logger=log,
    )


def _public_result(result: object) -> list[dict[str, object]]:
    if not isinstance(result, list):
        return []
    public: list[dict[str, object]] = []
    for item in result:
        if isinstance(item, dict) and isinstance(item.get('url'), str):
            public.append({'url': item['url']})
    return public


async def _completed_result_from_creations(
    request: Request,
    task_id: str,
    user_id: str,
) -> list[dict[str, object]] | None:
    """关停终态核对：按 creation 捕获行判断被取消任务的计费是否已提交。

    异步任务的计费 finalize 与 creation 捕获行同事务提交，batch_id 即
    task_id（capture.build_creation_capture_context）；行存在即证明用户
    已扣费且作品已落库。取消若落在该事务提交之后、结果返回之前的小窗口，
    必须据此恢复 succeeded，否则任务误标 failed——用户已扣费却看到失败，
    重试还会二次扣费。镜像 videos/service.py 的关停终态核对。
    """
    try:
        async with creation_session() as session:
            rows = (
                (
                    await session.execute(
                        select(CreationMediaItem)
                        .where(
                            CreationMediaItem.batch_id == task_id,
                            CreationMediaItem.user_id == user_id,
                            CreationMediaItem.soft_deleted.is_(False),
                        )
                        .order_by(CreationMediaItem.created_at, CreationMediaItem.id)
                    )
                )
                .scalars()
                .all()
            )
    except Exception:
        # 进程关停中 DB 也可能不可用：退回失败路径，已提交的 creation 行
        # 仍可由对账流程核对（与视频路径一致）。
        log.exception('Could not verify completed creations for interrupted image task %s', task_id)
        return None
    if not rows:
        return None
    app = getattr(request, 'app', None)
    if app is None:
        return None
    return [{'url': str(app.url_path_for('get_file_content_by_id', id=row.file_id))} for row in rows]


def _error_code(error: Exception) -> str:
    code = getattr(error, 'code', None)
    if isinstance(code, str) and code:
        return code[:64]
    return 'image_generation_failed'


async def _invoke_generation_provider(
    task_id: str,
    request: Request,
    user: object,
    form: object,
    kind: str,
) -> object:
    from open_webui.routers.images import image_edits, image_generations

    common = {
        'metadata': {'generation_task_id': task_id},
        'user': user,
        'concurrency_slot_held_by_caller': True,
    }
    if kind == 'image-to-image':
        return await image_edits(request, form, 'direct', **common)
    return await image_generations(request, form, 'direct', **common)


async def _restore_completed_image_task(
    request: Request,
    task_id: str,
    user_id: str,
    result: object | None,
) -> bool:
    completed = result
    if completed is None:
        completed = await _completed_result_from_creations(request, task_id, user_id)
    if completed is None:
        return False
    try:
        await _set_task_state(task_id, status='succeeded', result=_public_result(completed))
    except Exception:
        # A committed creation is irreversible success evidence. A task-row
        # write failure must never overwrite that truth with failed/refunded.
        log.exception('Could not restore succeeded state for image task %s', task_id)
    await _publish_image_task_event(request.app, task_id, user_id, 'succeeded')
    return True


async def _fail_image_task_safely(
    request: Request,
    task_id: str,
    user_id: str,
    error_code: str,
) -> None:
    try:
        await _set_task_state(task_id, status='failed', error_code=error_code)
    except Exception:
        log.exception('Could not persist failed image task %s', task_id)
    await _publish_image_task_event(request.app, task_id, user_id, 'failed', error_code=error_code)


async def run_generation_task(
    task_id: str,
    request: Request,
    user: object,
    form: object,
    kind: str,
) -> None:
    user_id = getattr(user, 'id', '')
    result: object | None = None
    try:
        await _set_task_state(task_id, status='running')
        await _publish_image_task_event(request.app, task_id, user_id, 'running')
        # 提交端（creations/router.py）已计入限流并占用任务全程的并发槽位，
        # 执行时显式声明跳过门禁，避免双重占用（复盘 P0-3 门禁下沉的配套）。
        result = await _invoke_generation_provider(task_id, request, user, form, kind)
        await _set_task_state(task_id, status='succeeded', result=_public_result(result))
        await _publish_image_task_event(request.app, task_id, user_id, 'succeeded')
    except asyncio.CancelledError:
        if await _restore_completed_image_task(request, task_id, user_id, result):
            raise
        await _fail_image_task_safely(request, task_id, user_id, 'server_shutdown')
        raise
    except Exception as error:
        log.exception('Image generation task %s failed', task_id)
        # provider/billing 调用可能已在同一事务中完成扣费和作品捕获，随后仅在
        # 返回结果或更新任务行时失败。此时 creation 行是不可逆成功证据；若
        # 直接把任务覆盖为 failed，会诱导重试并造成二次扣费。
        if await _restore_completed_image_task(request, task_id, user_id, result):
            return
        await _fail_image_task_safely(request, task_id, user_id, _error_code(error))


def schedule_generation_task(
    request: Request,
    *,
    task_id: str,
    user: object,
    form: object,
    kind: str,
    on_finished: Callable[[], Awaitable[None]] | None = None,
) -> None:
    running: dict[str, asyncio.Task[None]] = request.app.state.creation_generation_tasks
    schedule_tracked_task(
        running,
        task_id,
        lambda: run_generation_task(task_id, request, user, form, kind),
        kind='image',
        logger=log,
        on_finished=on_finished,
    )


async def fail_incomplete_generation_tasks() -> int:
    now = _now()
    async with creation_session() as session:
        result = await session.execute(
            update(ImageGenerationTask)
            .where(ImageGenerationTask.status.in_(ACTIVE_GENERATION_TASK_STATUSES))
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
    'create_generation_task',
    'delete_generation_task',
    'get_generation_task_by_idempotency_key',
    'fail_incomplete_generation_tasks',
    'fail_generation_task_scheduling',
    'get_generation_task',
    'list_generation_tasks',
    'run_generation_task',
    'schedule_generation_task',
    'set_image_task_execution_mode',
    'shutdown_generation_tasks',
]
