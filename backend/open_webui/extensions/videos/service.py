from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import HTTPException, Request
from open_webui.extensions.creations.db import creation_session
from open_webui.extensions.creations.models import CreationMediaItem, VideoGenerationTask
from open_webui.extensions.creations.task_runtime import (
    publish_task_event_safely,
    schedule_tracked_task,
    task_state_values,
)
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.models import CreditUsage
from open_webui.extensions.model_ops.service import ensure_model_enabled
from open_webui.extensions.videos.billing import (
    begin_video_usage,
    credit_session,
    heartbeat_video_usage,
    mark_usage_succeeded_in_session,
    mark_video_usage_failed,
    mark_video_usage_invoking,
    quote_video_usage,
)
from open_webui.extensions.videos.catalog import VideoInputError
from open_webui.extensions.videos.delivery import (
    _cleanup_result_files,
    _finalize_mock_video,
    _finalize_real_video,
    _now,
    _run_mock_scenario,
)
from open_webui.extensions.videos.executor import (
    FalVideoExecutor,
    VideoExecutionError,
    VideoExecutionOutput,
    enforce_fal_video_policy,
    resolve_video_executor,
)
from open_webui.extensions.videos.limits import (
    acquire_video_generation_slot,
    release_video_generation_slot,
)
from open_webui.extensions.videos.queries import _response, _submission_from_task
from open_webui.extensions.videos.schemas import VideoTaskResult
from open_webui.extensions.videos.task_state import (
    merged_provider_recovery_values as _merged_provider_recovery_values,
)
from open_webui.extensions.videos.task_state import (
    persist_provider_result_url as _persist_provider_result_url,
)
from open_webui.extensions.videos.task_state import (
    persist_provider_submission as _persist_provider_submission,
)
from open_webui.extensions.videos.task_state import (
    provider_execution_snapshot as _provider_execution_snapshot,
)
from open_webui.extensions.videos.task_state import (
    task_has_provider_submission as _task_has_provider_submission,
)
from open_webui.internal.db import get_async_db
from open_webui.models.users import Users
from sqlalchemy import select, update

log = logging.getLogger(__name__)

_RECOVERABLE_VIDEO_ERRORS = frozenset(
    {
        'video_delivery_failed',
        'video_result_download_failed',
        'video_provider_timeout',
    }
)
# 恢复路径（重启/60 秒扫描）重试投递/轮询的最大次数：超过后任务转终态，
# 避免 URL 过期、模型下架等问题让任务永留 running、预扣积分永久占用。
_VIDEO_DELIVERY_MAX_ATTEMPTS = 5


async def _set_task_state(
    task_id: str,
    status: str,
    *,
    result: dict[str, object] | None = None,
    error_code: str | None = None,
) -> None:
    now = _now()
    values = task_state_values(status, now=now, result=result, error_code=error_code)
    async with creation_session() as session:
        await session.execute(update(VideoGenerationTask).where(VideoGenerationTask.id == task_id).values(**values))
        await session.commit()


async def fail_video_task_scheduling(app: object, task_id: str, user_id: str) -> None:
    """Close a committed queued row when no worker could be scheduled."""
    error_code = 'video_scheduling_failed'
    await _set_task_state(task_id, 'failed', error_code=error_code)
    await _publish_video_task_event(app, task_id, user_id, 'failed', error_code=error_code)


async def _publish_video_task_event(
    app: object,
    task_id: str,
    user_id: str,
    status: str,
    *,
    error_code: str | None = None,
) -> None:
    """广播视频任务状态变更到 SSE 事件总线。无订阅者时安全跳过。"""
    await publish_task_event_safely(
        app,
        kind='video',
        task_id=task_id,
        user_id=user_id,
        status=status,
        error_code=error_code,
        logger=log,
    )


async def _set_task_usage_id(task_id: str, usage_id: str, execution_mode: str | None = None) -> None:
    async with creation_session() as session:
        await session.execute(
            update(VideoGenerationTask)
            .where(VideoGenerationTask.id == task_id)
            .values(usage_id=usage_id, execution_mode=execution_mode, updated_at=_now())
        )
        await session.commit()


async def _persist_provider_result_for_delivery(task_id: str, result_url: str) -> None:
    await _persist_provider_result_url(task_id, result_url)
    await _increment_delivery_attempts(task_id)


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


async def _settle_video_task_success(
    request: Request,
    task_id: str,
    user_id: str,
    result: dict[str, object],
) -> None:
    """成功终态结算：task succeeded 落库 + SSE 事件发布（异常上抛交外层处理）。

    复盘 P2：run/recover 两侧逐字重复的骨架收敛。"""
    await _set_task_state(task_id, 'succeeded', result=result)
    await _publish_video_task_event(request.app, task_id, user_id, 'succeeded')


async def _try_settle_video_task_failure(
    request: Request,
    task_id: str,
    user_id: str,
    *,
    error_code: str,
    usage_id: str | None,
    restore_prepaid: bool,
    context: str,
    usage_error_code: str | None = None,
) -> None:
    """失败终态结算三连：usage 计费失败 → task failed 落库 → SSE 事件发布。

    复盘 P2：run/recover 两侧 6 处逐字重复的骨架收敛。每步独立容错——
    计费清理失败不能阻止任务行终态写入；此前 recover 侧 _set_task_state
    未包 try/except，DB 抖动会吞掉后续事件发布（漂移修复）。
    """
    if usage_id is not None:
        try:
            await mark_video_usage_failed(
                usage_id,
                usage_error_code if usage_error_code is not None else error_code,
                restore_prepaid=restore_prepaid,
            )
        except Exception:
            log.exception('Could not fail usage for %s %s', context, task_id)
    try:
        await _set_task_state(task_id, 'failed', error_code=error_code)
    except Exception:
        log.exception('Could not persist failed video task %s', task_id)
    try:
        await _publish_video_task_event(request.app, task_id, user_id, 'failed', error_code=error_code)
    except Exception:
        log.exception('Could not publish failed video task %s', task_id)


async def _finalize_task_resources(
    heartbeat: asyncio.Task | None,
    output: VideoExecutionOutput | None,
    *,
    task_id: str,
    context: str,
) -> None:
    """任务收尾：取消 usage 心跳并清理临时视频文件（run/recover 共用）。"""
    if heartbeat is not None:
        # 兜底取消：成功转移完成、异常处理结束后心跳不再有意义
        # （usage 已离开 invoking，下一次 touch 返回 0 会自行退出）。
        heartbeat.cancel()
        await asyncio.gather(heartbeat, return_exceptions=True)
    if output is not None:
        try:
            await asyncio.to_thread(output.video_path.unlink, missing_ok=True)
        except Exception:
            log.exception('Could not remove %s video result for task %s', context, task_id)


@dataclass
class _VideoRunState:
    usage_id: str | None = None
    result: dict[str, object] | None = None
    usage_succeeded: bool = False
    output: VideoExecutionOutput | None = None
    heartbeat: asyncio.Task | None = None


async def _finalize_video_usage(
    state: _VideoRunState,
    request: Request,
    user: object,
    task: object,
    task_id: str,
    user_id: str,
) -> None:
    assert state.usage_id is not None
    async with credit_session() as terminal_session, terminal_session.begin():
        if state.output is not None:
            state.result = await _finalize_real_video(request, user, task, terminal_session, state.output)
        else:
            state.result = await _finalize_mock_video(request, user, task, terminal_session)
        changed = await mark_usage_succeeded_in_session(
            terminal_session,
            state.usage_id,
            [str(state.result['url'])],
        )
        if changed != 1:
            raise RuntimeError('video usage success transition failed')
    state.usage_succeeded = True
    await _settle_video_task_success(request, task_id, user_id, state.result)


async def _execute_new_video_task(
    state: _VideoRunState,
    task_id: str,
    request: Request,
    user: object,
    user_id: str,
) -> None:
    await _set_task_state(task_id, 'running')
    await _publish_video_task_event(request.app, task_id, user_id, 'running')
    async with creation_session() as session:
        row = await session.scalar(
            select(VideoGenerationTask).where(
                VideoGenerationTask.id == task_id,
                VideoGenerationTask.user_id == user_id,
            )
        )
    if row is None:
        return
    task = _response(row)
    executor = await resolve_video_executor()
    begin = await begin_video_usage(user, task, execution_mode=executor.mode)
    if begin.outcome != 'new':
        raise RuntimeError(f'unexpected video usage outcome: {begin.outcome}')
    state.usage_id = begin.usage.id
    await _set_task_usage_id(task_id, state.usage_id, executor.mode)
    await mark_video_usage_invoking(state.usage_id)
    if isinstance(executor, FalVideoExecutor):
        definition, provider_payload = _provider_execution_snapshot(row)
        state.heartbeat = asyncio.create_task(
            heartbeat_video_usage(state.usage_id),
            name=f'video-usage-heartbeat:{state.usage_id}',
        )
        state.output = await executor.invoke(
            request,
            user,
            task,
            definition,
            provider_payload,
            on_submitted=lambda payload: _persist_provider_submission(task_id, payload),
            on_result_url=lambda url: _persist_provider_result_for_delivery(task_id, url),
        )
    else:
        await _run_mock_scenario()
    await _finalize_video_usage(state, request, user, task, task_id, user_id)


async def _persisted_usage_succeeded(usage_id: str, task_id: str) -> bool:
    try:
        async with credit_session() as session:
            status = await session.scalar(select(CreditUsage.status).where(CreditUsage.id == usage_id))
        return status == 'succeeded'
    except Exception:
        log.exception('Could not verify terminal usage state for interrupted video task %s', task_id)
        return False


async def _handle_run_cancellation(
    state: _VideoRunState,
    error: asyncio.CancelledError,
    request: Request,
    task_id: str,
    user_id: str,
) -> None:
    if not state.usage_succeeded and state.usage_id is not None and state.result is not None:
        state.usage_succeeded = await _persisted_usage_succeeded(state.usage_id, task_id)
    if state.usage_succeeded and state.result is not None:
        try:
            await _settle_video_task_success(request, task_id, user_id, state.result)
        except Exception:
            log.exception('Could not restore succeeded state for interrupted video task %s', task_id)
        return
    provider_submitted = bool(
        getattr(error, 'provider_completed', False)
        or getattr(error, 'provider_submitted', False)
        or state.output is not None
    )
    if state.usage_id is not None and provider_submitted:
        try:
            await _set_task_state(task_id, 'running', error_code='video_recovery_pending')
        except Exception:
            log.exception('Could not persist recoverable interrupted video task %s', task_id)
        return
    await _try_settle_video_task_failure(
        request,
        task_id,
        user_id,
        error_code='server_shutdown',
        usage_id=state.usage_id,
        restore_prepaid=True,
        context='interrupted video task',
    )


async def _handle_run_execution_error(
    state: _VideoRunState,
    error: VideoExecutionError,
    request: Request,
    task_id: str,
    user: object,
    user_id: str,
) -> None:
    log.exception('Video generation task %s failed with %s', task_id, error.code)
    if state.usage_id is not None and (error.provider_completed or (error.provider_submitted and error.retryable)):
        await _set_task_state(task_id, 'running', error_code='video_delivery_pending')
        await recover_video_task(task_id, request, user)
        return
    await _try_settle_video_task_failure(
        request,
        task_id,
        user_id,
        error_code=error.code,
        usage_id=state.usage_id,
        restore_prepaid=not (error.provider_submitted or error.provider_completed or state.output is not None),
        context='video task',
    )


async def _handle_unexpected_run_error(
    state: _VideoRunState,
    request: Request,
    task_id: str,
    user_id: str,
) -> None:
    log.exception('Video generation task %s failed', task_id)
    if state.usage_succeeded and state.result is not None:
        try:
            await _settle_video_task_success(request, task_id, user_id, state.result)
        except Exception:
            log.exception('Could not restore committed video success for task %s', task_id)
        return
    await _cleanup_result_files(state.result)
    code = 'video_delivery_failed' if state.output is not None else 'video_generation_failed'
    await _try_settle_video_task_failure(
        request,
        task_id,
        user_id,
        error_code=code,
        usage_id=state.usage_id,
        restore_prepaid=state.output is None,
        context='video task',
    )


async def run_video_task(
    task_id: str,
    request: Request,
    user: object,
) -> None:
    user_id = getattr(user, 'id', '')
    state = _VideoRunState()
    try:
        await _execute_new_video_task(state, task_id, request, user, user_id)
    except asyncio.CancelledError as error:
        await _handle_run_cancellation(state, error, request, task_id, user_id)
        raise
    except CreditError as error:
        await _try_settle_video_task_failure(
            request,
            task_id,
            user_id,
            error_code=error.code[:64],
            usage_id=state.usage_id,
            usage_error_code=error.code,
            restore_prepaid=state.output is None,
            context='video task',
        )
    except VideoExecutionError as error:
        await _handle_run_execution_error(state, error, request, task_id, user, user_id)
    except Exception:
        await _handle_unexpected_run_error(state, request, task_id, user_id)
    finally:
        await _finalize_task_resources(state.heartbeat, state.output, task_id=task_id, context='temporary')


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
    # 复盘 P1：封面可空（真实视频封面提取失败按无封面交付）——恢复判定
    # 只要求视频本体与时长存在，否则无封面作品会被误判为"无既有结果"
    # 而重新进入投递循环。
    if creation is None or not creation.duration_seconds:
        return None
    return VideoTaskResult(
        creation_id=creation.id,
        file_id=creation.file_id,
        poster_file_id=creation.poster_file_id,
        url=str(request.app.url_path_for('get_file_content_by_id', id=creation.file_id)),
        poster_url=(
            str(request.app.url_path_for('get_file_content_by_id', id=creation.poster_file_id))
            if creation.poster_file_id
            else None
        ),
        duration_seconds=creation.duration_seconds,
    ).model_dump()


@dataclass
class _VideoRecoveryState(_VideoRunState):
    row: VideoGenerationTask | None = None
    provider_was_submitted: bool = False


async def _settle_existing_video_result(
    state: _VideoRecoveryState,
    request: Request,
    task_id: str,
    user_id: str,
) -> bool:
    assert state.usage_id is not None
    existing = await _existing_creation_result(request, task_id, user_id)
    if existing is None:
        return False
    state.result = existing
    async with credit_session() as session, session.begin():
        usage_status = await session.scalar(select(CreditUsage.status).where(CreditUsage.id == state.usage_id))
        if usage_status == 'invoking':
            changed = await mark_usage_succeeded_in_session(
                session,
                state.usage_id,
                [str(existing['url'])],
            )
            if changed != 1:
                raise RuntimeError('video usage recovery success transition failed')
        elif usage_status != 'succeeded':
            raise VideoExecutionError('video_recovery_usage_invalid')
    state.usage_succeeded = True
    await _settle_video_task_success(request, task_id, user_id, existing)
    return True


async def _resume_fal_video_output(
    state: _VideoRecoveryState,
    task_id: str,
    task: object,
) -> None:
    assert state.row is not None and state.usage_id is not None
    (
        provider_request_id,
        provider_status_url,
        provider_response_url,
        provider_result_url,
        state.provider_was_submitted,
    ) = await _merged_provider_recovery_values(task_id, state.row)
    if state.row.delivery_attempts >= _VIDEO_DELIVERY_MAX_ATTEMPTS:
        raise VideoExecutionError('video_delivery_attempts_exceeded')
    executor = await resolve_video_executor()
    if not isinstance(executor, FalVideoExecutor):
        await _increment_delivery_attempts(task_id)
        raise VideoExecutionError('video_fal_not_configured', retryable=True)
    definition, _provider_payload = _provider_execution_snapshot(state.row)
    await _increment_delivery_attempts(task_id)
    state.heartbeat = asyncio.create_task(
        heartbeat_video_usage(state.usage_id),
        name=f'video-recovery-usage-heartbeat:{state.usage_id}',
    )
    state.output = await executor.resume(
        task,
        definition,
        status_url=provider_status_url,
        response_url=provider_response_url,
        result_url=provider_result_url,
        provider_request_id=provider_request_id,
        on_result_url=lambda url: _persist_provider_result_url(task_id, url),
    )


async def _resume_video_provider(
    state: _VideoRecoveryState,
    task_id: str,
    task: object,
) -> None:
    assert state.row is not None
    if state.row.execution_mode == 'mock':
        await _run_mock_scenario()
        return
    if state.row.execution_mode == 'fal':
        await _resume_fal_video_output(state, task_id, task)
        return
    raise VideoExecutionError('video_recovery_state_missing')


async def _execute_video_recovery(
    state: _VideoRecoveryState,
    task_id: str,
    request: Request,
    user: object,
    user_id: str,
) -> None:
    async with creation_session() as session:
        state.row = await session.scalar(select(VideoGenerationTask).where(VideoGenerationTask.id == task_id))
    if state.row is None or state.row.status not in {'queued', 'running'}:
        return
    if state.row.status == 'queued':
        await run_video_task(task_id, request, user)
        return
    task = _response(state.row)
    state.usage_id = state.row.usage_id
    state.provider_was_submitted = _task_has_provider_submission(state.row)
    if not state.usage_id:
        raise VideoExecutionError('video_recovery_state_missing')
    if await _settle_existing_video_result(state, request, task_id, user_id):
        return
    await _resume_video_provider(state, task_id, task)
    await _finalize_video_usage(state, request, user, task, task_id, user_id)


async def _handle_recovery_execution_error(
    state: _VideoRecoveryState,
    error: VideoExecutionError,
    request: Request,
    task_id: str,
    user_id: str,
) -> None:
    log.exception('Video recovery task %s failed with %s', task_id, error.code)
    if error.retryable or error.code in _RECOVERABLE_VIDEO_ERRORS:
        await _set_task_state(task_id, 'running', error_code='video_delivery_pending')
        return
    row = state.row
    restore_prepaid = bool(
        state.usage_id is not None
        and error.code == 'video_recovery_state_missing'
        and row is not None
        and row.execution_mode != 'fal'
        and not state.provider_was_submitted
    )
    await _try_settle_video_task_failure(
        request,
        task_id,
        user_id,
        error_code=error.code,
        usage_id=state.usage_id,
        restore_prepaid=restore_prepaid,
        context='video recovery task',
    )


async def _handle_recovery_input_error(
    state: _VideoRecoveryState,
    error: VideoInputError,
    request: Request,
    task_id: str,
    user_id: str,
) -> None:
    code = f'video_input_rejected:{error}'[:64]
    log.warning('Video recovery task %s rejected by catalog: %s', task_id, error)
    row = state.row
    restore_prepaid = bool(row is not None and row.execution_mode != 'fal' and not state.provider_was_submitted)
    await _try_settle_video_task_failure(
        request,
        task_id,
        user_id,
        error_code=code,
        usage_id=state.usage_id,
        restore_prepaid=restore_prepaid,
        context='video recovery task',
    )


async def _handle_unexpected_recovery_error(
    state: _VideoRecoveryState,
    request: Request,
    task_id: str,
    user_id: str,
) -> None:
    log.exception('Video recovery task %s failed', task_id)
    if state.usage_succeeded and state.result is not None:
        try:
            await _settle_video_task_success(request, task_id, user_id, state.result)
        except Exception:
            log.exception('Could not restore recovered video success for task %s', task_id)
        return
    await _cleanup_result_files(state.result)
    await _set_task_state(task_id, 'running', error_code='video_delivery_pending')


async def recover_video_task(task_id: str, request: Request, user: object) -> None:
    """Resume a persisted task without issuing a second provider generation POST."""
    user_id = str(getattr(user, 'id', ''))
    state = _VideoRecoveryState()
    try:
        await _execute_video_recovery(state, task_id, request, user, user_id)
    except asyncio.CancelledError:
        raise
    except VideoExecutionError as error:
        await _handle_recovery_execution_error(state, error, request, task_id, user_id)
    except VideoInputError as error:
        await _handle_recovery_input_error(state, error, request, task_id, user_id)
    except Exception:
        await _handle_unexpected_recovery_error(state, request, task_id, user_id)
    finally:
        await _finalize_task_resources(
            state.heartbeat,
            state.output,
            task_id=task_id,
            context='recovered temporary',
        )


def schedule_video_task(
    request: Request,
    task_id: str,
    user: object,
    *,
    on_finished: Callable[[], Awaitable[None]] | None = None,
) -> None:
    running: dict[str, asyncio.Task[None]] = request.app.state.video_generation_tasks
    schedule_tracked_task(
        running,
        task_id,
        lambda: run_video_task(task_id, request, user),
        kind='video',
        logger=log,
        on_finished=on_finished,
    )


def schedule_video_recovery_task(request: Request, task_id: str, user: object) -> bool:
    running: dict[str, asyncio.Task[None]] = request.app.state.video_generation_tasks
    if task_id in running:
        return False

    schedule_tracked_task(
        running,
        task_id,
        lambda: recover_video_task(task_id, request, user),
        kind='video recovery',
        logger=log,
        on_finished=lambda: release_video_generation_slot(str(getattr(user, 'id', ''))),
    )
    return True


async def _queued_task_rejection_code(row: VideoGenerationTask, user: object) -> str | None:
    """排队任务恢复前的重新准入检查，返回拒绝错误码（None 表示放行调度）。

    崩溃时排队任务尚未扣费，模型开关、FAL 限价或定价随后可能已调整：
    恢复必须按当前配置重新校验（与提交路径一致的检查），而不是直接按
    旧任务参数扣费。余额不足/价格未配置/执行器暂时不可用等非准入性
    原因也返回 None 放行——由 run_video_task 的 begin_usage 走既有
    CreditError 终态失败路径，排队任务不无限滞留。
    """
    try:
        async with get_async_db() as model_session:
            await ensure_model_enabled(model_session, row.model_id, media_kind='video')
    except HTTPException as error:
        detail = error.detail
        code = detail.get('code') if isinstance(detail, dict) else None
        return str(code or 'video_model_unavailable')[:64]
    except Exception:
        # 开关查询失败按暂时性处理，避免误杀可恢复的排队任务。
        log.exception('Could not verify video model availability for queued task %s', row.id)
        return None
    try:
        quote = await quote_video_usage(user, _submission_from_task(_response(row)))
    except VideoInputError:
        # 模型已从目录移除：交付永远无法完成，转终态。
        return 'unknown_video_model'
    except CreditError as error:
        log.info(
            'Queued video task %s passed admission (quote error %s; terminal handling left to run path)',
            row.id,
            error.code,
        )
        return None
    try:
        executor = await resolve_video_executor()
    except VideoExecutionError:
        return None
    if isinstance(executor, FalVideoExecutor):
        try:
            enforce_fal_video_policy(model_id=row.model_id, charged_credits=quote.charged_credits or 0)
        except VideoExecutionError as error:
            return error.code
    return None


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
        if row.status == 'queued':
            rejection = await _queued_task_rejection_code(row, user)
            if rejection is not None:
                await _set_task_state(row.id, 'failed', error_code=rejection)
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
    'fail_video_task_scheduling',
    'recover_incomplete_video_tasks',
    'recover_video_task',
    'schedule_video_task',
    'shutdown_video_tasks',
]
