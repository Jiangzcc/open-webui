from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request
from open_webui.extensions.creations.db import creation_session
from open_webui.extensions.creations.models import CreationMediaItem, VideoGenerationTask
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
from open_webui.extensions.videos.catalog import VideoInputError, build_video_provider_payload
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
from open_webui.extensions.videos.schemas import VideoTaskResponse, VideoTaskResult
from open_webui.internal.db import get_async_db
from open_webui.models.users import Users
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

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


def _task_has_provider_submission(row: VideoGenerationTask) -> bool:
    """FAL 是否已受理过该任务的请求（存在任一持久化提交状态即视为已受理）。"""
    return bool(row.provider_request_id or row.provider_response_url or row.provider_result_url)


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


async def _settle_video_task_failure(
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
        #（usage 已离开 invoking，下一次 touch 返回 0 会自行退出）。
        heartbeat.cancel()
        await asyncio.gather(heartbeat, return_exceptions=True)
    if output is not None:
        try:
            await asyncio.to_thread(output.video_path.unlink, missing_ok=True)
        except Exception:
            log.exception('Could not remove %s video result for task %s', context, task_id)


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
    heartbeat: asyncio.Task | None = None
    try:
        await _set_task_state(task_id, 'running')
        await _publish_video_task_event(request.app, task_id, user_id, 'running')
        async with creation_session() as session:
            row = await session.scalar(
                select(VideoGenerationTask).where(
                    VideoGenerationTask.id == task_id,
                    VideoGenerationTask.user_id == getattr(user, 'id', ''),
                )
            )
        if row is None:
            return
        task = _response(row)
        executor = await resolve_video_executor()
        begin = await begin_video_usage(user, task, execution_mode=executor.mode)
        if begin.outcome != 'new':
            raise RuntimeError(f'unexpected video usage outcome: {begin.outcome}')
        usage_id = begin.usage.id
        await _set_task_usage_id(task_id, usage_id, executor.mode)
        await mark_video_usage_invoking(usage_id)
        if isinstance(executor, FalVideoExecutor):
            submission = _submission_from_task(task)
            definition, provider_payload, _safe_params = build_video_provider_payload(submission)
            # 心跳必须覆盖 invoke 与 finalize 两阶段：finalize 的两轮上传对大
            # 视频可能超过 15 分钟 stale 阈值，只在 invoke 期间心跳会让 usage
            # 被回收成 unknown → 成功转移写 0 行 → 已上传的付费视频被清理。
            heartbeat = asyncio.create_task(
                heartbeat_video_usage(usage_id),
                name=f'video-usage-heartbeat:{usage_id}',
            )
            output = await executor.invoke(
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
        await _settle_video_task_success(request, task_id, user_id, result)
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
            # 合并容错：落库失败时不再发布 succeeded 事件，避免客户端看到的
            # 事件与数据库终态不一致（恢复路径统一采用此语义）。
            try:
                await _settle_video_task_success(request, task_id, user_id, result)
            except Exception:
                log.exception('Could not restore succeeded state for interrupted video task %s', task_id)
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
        await _settle_video_task_failure(
            request,
            task_id,
            user_id,
            error_code=code,
            usage_id=usage_id,
            restore_prepaid=True,
            context='interrupted video task',
        )
        raise
    except CreditError as error:
        code = error.code[:64]
        await _settle_video_task_failure(
            request,
            task_id,
            user_id,
            error_code=code,
            usage_id=usage_id,
            usage_error_code=error.code,
            restore_prepaid=output is None,
            context='video task',
        )
    except VideoExecutionError as error:
        log.exception('Video generation task %s failed with %s', task_id, error.code)
        if usage_id is not None and (error.provider_completed or (error.provider_submitted and error.retryable)):
            # FAL has completed or accepted a request whose response is
            # uncertain. Keep the task recoverable and retry only polling,
            # response fetch, download, or local delivery; never submit again.
            await _set_task_state(task_id, 'running', error_code='video_delivery_pending')
            await recover_video_task(task_id, request, user)
            return
        await _settle_video_task_failure(
            request,
            task_id,
            user_id,
            error_code=error.code,
            usage_id=usage_id,
            restore_prepaid=not (error.provider_completed or output is not None),
            context='video task',
        )
    except Exception:
        log.exception('Video generation task %s failed', task_id)
        if usage_succeeded and result is not None:
            try:
                await _settle_video_task_success(request, task_id, user_id, result)
            except Exception:
                log.exception('Could not restore committed video success for task %s', task_id)
            return
        await _cleanup_result_files(result)
        # 已有产物（output）时失败在交付阶段，否则在生成阶段。
        code = 'video_delivery_failed' if output is not None else 'video_generation_failed'
        await _settle_video_task_failure(
            request,
            task_id,
            user_id,
            error_code=code,
            usage_id=usage_id,
            restore_prepaid=output is None,
            context='video task',
        )
    finally:
        await _finalize_task_resources(heartbeat, output, task_id=task_id, context='temporary')


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


async def recover_video_task(task_id: str, request: Request, user: object) -> None:  # noqa: C901
    """Resume a persisted task without issuing a second provider generation POST."""
    user_id = str(getattr(user, 'id', ''))
    output: VideoExecutionOutput | None = None
    usage_id: str | None = None
    result: dict[str, object] | None = None
    usage_succeeded = False
    heartbeat: asyncio.Task | None = None
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
            await _settle_video_task_success(request, task_id, user_id, existing_result)
            return

        if row.execution_mode == 'mock':
            await _run_mock_scenario()
        elif row.execution_mode == 'fal':
            if row.delivery_attempts >= _VIDEO_DELIVERY_MAX_ATTEMPTS:
                # 反复投递/轮询失败（如签名 URL 过期且无法刷新）：转终态，
                # 不让 60 秒恢复循环无限重试、预扣积分永久占用。
                raise VideoExecutionError('video_delivery_attempts_exceeded')
            executor = await resolve_video_executor()
            if not isinstance(executor, FalVideoExecutor):
                # 复盘 P1：FAL 配置被切走（如管理端开 mock）时，fal 模式的存量任务
                # 必须先计一次投递尝试再抛可重试错误——短暂切换可在重试窗口内
                # 自愈；持续缺失则耗尽 _VIDEO_DELIVERY_MAX_ATTEMPTS 后转终态，
                # 不再无限滞留、预扣积分永久占用。
                await _increment_delivery_attempts(task_id)
                raise VideoExecutionError('video_fal_not_configured', retryable=True)
            submission = _submission_from_task(task)
            definition, _provider_payload, _safe_params = build_video_provider_payload(submission)
            await _increment_delivery_attempts(task_id)
            # 与 run_video_task 相同：心跳覆盖 resume 与 finalize 两阶段。
            heartbeat = asyncio.create_task(
                heartbeat_video_usage(usage_id),
                name=f'video-recovery-usage-heartbeat:{usage_id}',
            )
            output = await executor.resume(
                task,
                definition,
                status_url=row.provider_status_url,
                response_url=row.provider_response_url,
                result_url=row.provider_result_url,
                provider_request_id=row.provider_request_id,
                on_result_url=lambda url: _persist_provider_result_url(task_id, url),
            )
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
        await _settle_video_task_success(request, task_id, user_id, result)
    except asyncio.CancelledError:
        raise
    except VideoExecutionError as error:
        log.exception('Video recovery task %s failed with %s', task_id, error.code)
        if error.retryable or error.code in _RECOVERABLE_VIDEO_ERRORS:
            await _set_task_state(task_id, 'running', error_code='video_delivery_pending')
            return
        if usage_id is not None:
            # 恢复状态缺失 ⇒ 无法确认 FAL 是否受理过该请求。与在线路径
            # 语义对齐：供应商受理未确认即退款（在线检出同类失败会即时
            # 退款）；已持久化提交状态（FAL 已受理）则保留预扣，交由
            # 对账修复流程处理。
            restore_prepaid = error.code == 'video_recovery_state_missing' and not _task_has_provider_submission(row)
        else:
            restore_prepaid = False
        await _settle_video_task_failure(
            request,
            task_id,
            user_id,
            error_code=error.code,
            usage_id=usage_id,
            restore_prepaid=restore_prepaid,
            context='video recovery task',
        )
    except VideoInputError as error:
        # 模型下架/参数不再受支持（catalog 变更）：交付永远无法完成，必须
        # 转终态；留在 running 会让 60 秒恢复循环无限重试。
        code = f'video_input_rejected:{error}'[:64]
        log.warning('Video recovery task %s rejected by catalog: %s', task_id, error)
        await _settle_video_task_failure(
            request,
            task_id,
            user_id,
            error_code=code,
            usage_id=usage_id,
            restore_prepaid=not _task_has_provider_submission(row),
            context='video recovery task',
        )
    except Exception:
        log.exception('Video recovery task %s failed', task_id)
        if usage_succeeded and result is not None:
            try:
                await _settle_video_task_success(request, task_id, user_id, result)
            except Exception:
                log.exception('Could not restore recovered video success for task %s', task_id)
            return
        await _cleanup_result_files(result)
        await _set_task_state(task_id, 'running', error_code='video_delivery_pending')
    finally:
        await _finalize_task_resources(heartbeat, output, task_id=task_id, context='recovered temporary')


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
    'recover_incomplete_video_tasks',
    'recover_video_task',
    'schedule_video_task',
    'shutdown_video_tasks',
]
