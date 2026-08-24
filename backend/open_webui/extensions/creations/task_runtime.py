"""Media-neutral process task bookkeeping used by image and video workers."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

_FINISH_CALLBACK_MAX_ATTEMPTS = 3


def task_state_values(
    status: str,
    *,
    now: int,
    result: object | None = None,
    error_code: str | None = None,
) -> dict[str, object]:
    values: dict[str, object] = {'status': status, 'updated_at': now, 'error_code': error_code}
    if status == 'running':
        values['started_at'] = now
    if status in {'succeeded', 'failed'}:
        values['completed_at'] = now
    if result is not None:
        values['result_json'] = result
    return values


async def publish_task_event_safely(
    app: object,
    *,
    kind: str,
    task_id: str,
    user_id: str,
    status: str,
    error_code: str | None,
    logger: logging.Logger,
) -> None:
    from open_webui.extensions.creations.events import publish_generation_event

    payload = {'error_code': error_code} if error_code is not None else None
    try:
        await publish_generation_event(
            app,
            kind=kind,
            task_id=task_id,
            status=status,
            user_id=user_id,
            payload=payload,
        )
    except Exception:
        # SSE is auxiliary: delivery failure must never replace persisted state.
        logger.exception('Could not publish %s event for %s task %s', status, kind, task_id)


async def _finish_with_retry(on_finished: Callable[[], Awaitable[None]]) -> None:
    for attempt in range(_FINISH_CALLBACK_MAX_ATTEMPTS):
        try:
            await on_finished()
            return
        except asyncio.CancelledError:
            raise
        except Exception:
            if attempt + 1 >= _FINISH_CALLBACK_MAX_ATTEMPTS:
                raise
            await asyncio.sleep(0)


async def _run_with_finish(
    worker: Callable[[], Awaitable[None]],
    on_finished: Callable[[], Awaitable[None]] | None,
    *,
    kind: str,
    task_id: str,
    logger: logging.Logger,
) -> None:
    original_error: BaseException | None = None
    try:
        await worker()
    except BaseException as error:
        original_error = error
        raise
    finally:
        await _finish_worker(on_finished, original_error, kind=kind, task_id=task_id, logger=logger)


async def _finish_worker(
    on_finished: Callable[[], Awaitable[None]] | None,
    original_error: BaseException | None,
    *,
    kind: str,
    task_id: str,
    logger: logging.Logger,
) -> None:
    if on_finished is None:
        return
    try:
        await _finish_with_retry(on_finished)
    except asyncio.CancelledError:
        if original_error is None:
            raise
        logger.warning('Finish callback cancelled for %s task %s', kind, task_id)
    except Exception:
        if original_error is None:
            raise
        logger.exception('Finish callback failed for %s task %s', kind, task_id)


def schedule_tracked_task(
    running: dict[str, asyncio.Task[None]],
    task_id: str,
    worker: Callable[[], Awaitable[None]],
    *,
    kind: str,
    logger: logging.Logger,
    on_finished: Callable[[], Awaitable[None]] | None = None,
    name: str | None = None,
) -> asyncio.Task[None]:
    task = asyncio.create_task(
        _run_with_finish(worker, on_finished, kind=kind, task_id=task_id, logger=logger),
        name=name,
    )
    running[task_id] = task

    def discard_finished(finished: asyncio.Task[None]) -> None:
        if running.get(task_id) is finished:
            running.pop(task_id, None)
        if not finished.cancelled():
            finished.exception()

    task.add_done_callback(discard_finished)
    return task


__all__ = ['publish_task_event_safely', 'schedule_tracked_task', 'task_state_values']
