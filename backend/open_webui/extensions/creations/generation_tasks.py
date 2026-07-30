from __future__ import annotations

import asyncio
import logging
import time
from typing import Any
from uuid import uuid4

from fastapi import Request
from open_webui.extensions.creations.db import creation_session
from open_webui.extensions.creations.models import ImageGenerationTask
from open_webui.extensions.creations.schemas import (
    ImageGenerationTaskListResponse,
    ImageGenerationTaskResponse,
)
from sqlalchemy import desc, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

_PRIVATE_PAYLOAD_KEYS = frozenset({'prompt', 'image', 'mask', 'mask_url', 'mask_image_url'})


def _now() -> int:
    return int(time.time())


def _safe_params(payload: dict[str, Any]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if key not in _PRIVATE_PAYLOAD_KEYS
        and value is not None
        and isinstance(value, (str, int, float, bool))
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


async def get_generation_task(
    session: AsyncSession, user_id: str, task_id: str
) -> ImageGenerationTaskResponse | None:
    task = (
        await session.execute(
            select(ImageGenerationTask).where(
                ImageGenerationTask.id == task_id,
                ImageGenerationTask.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    return _response(task) if task is not None else None


async def list_generation_tasks(
    session: AsyncSession, user_id: str, limit: int
) -> ImageGenerationTaskListResponse:
    tasks = (
        await session.execute(
            select(ImageGenerationTask)
            .where(ImageGenerationTask.user_id == user_id)
            .order_by(desc(ImageGenerationTask.created_at), desc(ImageGenerationTask.id))
            .limit(limit)
        )
    ).scalars()
    return ImageGenerationTaskListResponse(items=tuple(_response(task) for task in tasks))


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
        await session.execute(
            update(ImageGenerationTask).where(ImageGenerationTask.id == task_id).values(**values)
        )
        await session.commit()


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
    await _set_task_state(task_id, status='running')
    try:
        from open_webui.routers.images import image_edits, image_generations

        if kind == 'image-to-image':
            result = await image_edits(request, form, 'direct', user=user)
        else:
            result = await image_generations(request, form, 'direct', user=user)
        await _set_task_state(task_id, status='succeeded', result=_public_result(result))
    except asyncio.CancelledError:
        await _set_task_state(task_id, status='failed', error_code='server_shutdown')
        raise
    except Exception as error:
        log.exception('Image generation task %s failed', task_id)
        await _set_task_state(task_id, status='failed', error_code=_error_code(error))


def schedule_generation_task(
    request: Request,
    *,
    task_id: str,
    user: object,
    form: object,
    kind: str,
) -> None:
    running: set[asyncio.Task] = request.app.state.creation_generation_tasks
    task = asyncio.create_task(run_generation_task(task_id, request, user, form, kind))
    running.add(task)
    task.add_done_callback(running.discard)


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
    running: set[asyncio.Task] = getattr(app.state, 'creation_generation_tasks', set())
    for task in tuple(running):
        task.cancel()
    if running:
        await asyncio.gather(*tuple(running), return_exceptions=True)
    running.clear()


__all__ = [
    'create_generation_task',
    'fail_incomplete_generation_tasks',
    'get_generation_task',
    'list_generation_tasks',
    'run_generation_task',
    'schedule_generation_task',
    'shutdown_generation_tasks',
]
