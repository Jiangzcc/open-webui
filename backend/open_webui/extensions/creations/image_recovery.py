from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from fastapi import Request
from open_webui.extensions.creations.capture import finalize_created_images
from open_webui.extensions.creations.db import creation_session
from open_webui.extensions.creations.file_cleanup import cleanup_uploaded_files
from open_webui.extensions.creations.generation_tasks import (
    _completed_result_from_creations,
    _now,
    _publish_image_task_event,
    _set_task_state,
)
from open_webui.extensions.creations.models import ImageGenerationTask
from open_webui.extensions.creations.schemas import CapturedImageBatch, CreationCaptureContext
from open_webui.extensions.creations.task_runtime import schedule_tracked_task
from open_webui.extensions.credits.db import credit_session
from open_webui.extensions.credits.models import CreditUsage
from open_webui.extensions.credits.service import (
    SafeProviderError,
    mark_usage_failed,
    mark_usage_succeeded_in_session,
)
from open_webui.extensions.fal_images.client import resume_fal_queue
from open_webui.extensions.fal_images.models import (
    FAL_IMAGE_MODELS,
    normalize_fal_image_model_id,
    public_fal_image_model_id,
)
from open_webui.extensions.provider_ops.service import (
    load_provider_recovery_state,
    try_resume_provider_invocation,
)
from open_webui.models.files import Files
from open_webui.models.users import Users
from sqlalchemy import select, update

log = logging.getLogger(__name__)

_IMAGE_DELIVERY_MAX_ATTEMPTS = 5
_ACTIVE_IMAGE_TASK_STATUSES = ('queued', 'running')


def _capture_context(task: ImageGenerationTask, usage: CreditUsage) -> CreationCaptureContext:
    params = dict(task.params_json) if isinstance(task.params_json, dict) else {}
    negative_prompt = params.pop('negative_prompt', None)
    internal_model = normalize_fal_image_model_id(usage.resource_id)
    model_name = None
    if internal_model is not None:
        definition = next((item for item in FAL_IMAGE_MODELS if item.get('id') == internal_model), None)
        if definition is not None and isinstance(definition.get('name'), str):
            model_name = definition['name']
    source = usage.channel if usage.channel in {'web', 'api', 'chat', 'tool'} else 'web'
    return CreationCaptureContext(
        user_id=task.user_id,
        task=task.kind,
        source=source,
        prompt=task.prompt,
        negative_prompt=negative_prompt if isinstance(negative_prompt, str) else None,
        public_model_id=public_fal_image_model_id(internal_model) if internal_model else usage.resource_id,
        model_name_snapshot=model_name,
        params=params,
        batch_id=task.id,
    )


async def _increment_delivery_attempts(task_id: str) -> int:
    async with creation_session() as session:
        await session.execute(
            update(ImageGenerationTask)
            .where(ImageGenerationTask.id == task_id)
            .values(
                delivery_attempts=ImageGenerationTask.delivery_attempts + 1,
                updated_at=_now(),
            )
        )
        await session.commit()
        attempts = await session.scalar(
            select(ImageGenerationTask.delivery_attempts).where(ImageGenerationTask.id == task_id)
        )
    return int(attempts or 0)


async def _cleanup_batch(batch: CapturedImageBatch | None) -> None:
    if batch is None:
        return
    files = []
    for image in batch.images:
        file_id = getattr(image, 'file_id', None)
        if isinstance(file_id, str):
            file = await Files.get_file_by_id(file_id)
            if file is not None:
                files.append(file)
    await cleanup_uploaded_files(files)


async def _fail_usage_and_task(
    request: Request,
    task: ImageGenerationTask,
    usage: CreditUsage | None,
    code: str,
    *,
    restore_prepaid: bool,
) -> None:
    if usage is not None and usage.status == 'invoking':
        await mark_usage_failed(
            usage.id,
            SafeProviderError(code=code, summary='Image task recovery could not complete'),
            restore_prepaid=restore_prepaid,
        )
    await _set_task_state(task.id, status='failed', error_code=code)
    await _publish_image_task_event(request.app, task.id, task.user_id, 'failed', error_code=code)


async def _settle_existing_creation(
    request: Request,
    task: ImageGenerationTask,
    usage: CreditUsage,
    result: list[dict[str, object]],
) -> None:
    if usage.status == 'invoking':
        async with credit_session() as session, session.begin():
            changed = await mark_usage_succeeded_in_session(
                session,
                usage.id,
                [str(item['url']) for item in result],
            )
            if changed != 1:
                raise RuntimeError('image usage recovery success transition failed')
    elif usage.status != 'succeeded':
        raise RuntimeError('image recovery found creation with incompatible usage state')
    await _set_task_state(task.id, status='succeeded', result=result)
    await _publish_image_task_event(request.app, task.id, task.user_id, 'succeeded')


def _fal_credentials(config: object, kind: str) -> tuple[str, str]:
    if kind == 'image-to-image':
        api_key = getattr(config, 'IMAGES_EDIT_FAL_API_KEY', None) or getattr(config, 'FAL_API_KEY', None)
        base_url = getattr(config, 'IMAGES_EDIT_FAL_API_BASE_URL', None) or getattr(config, 'FAL_API_BASE_URL', None)
    else:
        api_key = getattr(config, 'FAL_API_KEY', None)
        base_url = getattr(config, 'FAL_API_BASE_URL', None)
    if not isinstance(api_key, str) or not api_key or not isinstance(base_url, str) or not base_url:
        raise RuntimeError('FAL image recovery is not configured')
    return api_key, base_url


@dataclass
class _RecoveryRun:
    batch: CapturedImageBatch | None = None
    attempts: int = 0
    terminal_committed: bool = False


async def _load_active_task_and_usage(
    task_id: str,
) -> tuple[ImageGenerationTask | None, CreditUsage | None]:
    async with creation_session() as session:
        task = await session.get(ImageGenerationTask, task_id)
    if task is None or task.status not in _ACTIVE_IMAGE_TASK_STATUSES:
        return None, None
    async with credit_session() as session:
        usage = await session.scalar(
            select(CreditUsage).where(
                CreditUsage.user_id == task.user_id,
                CreditUsage.idempotency_key == task.idempotency_key,
            )
        )
    return task, usage


async def _recovery_already_resolved(
    request: Request,
    task: ImageGenerationTask,
    usage: CreditUsage | None,
) -> bool:
    if task.status == 'queued':
        await _fail_usage_and_task(
            request,
            task,
            usage,
            'image_restarted_before_invocation',
            restore_prepaid=True,
        )
        return True
    if usage is None:
        await _fail_usage_and_task(request, task, None, 'image_recovery_usage_missing', restore_prepaid=False)
        return True
    existing = await _completed_result_from_creations(request, task.id, task.user_id)
    if existing is not None:
        await _settle_existing_creation(request, task, usage, existing)
        return True
    if task.execution_mode == 'fal' and usage.status == 'invoking':
        return False
    await _fail_usage_and_task(
        request,
        task,
        usage,
        'image_recovery_state_missing',
        restore_prepaid=task.execution_mode == 'mock',
    )
    return True


async def _load_usable_provider_state(
    request: Request,
    task: ImageGenerationTask,
    usage: CreditUsage,
) -> Any | None:
    state = await load_provider_recovery_state(task.id, media_kind='image')
    if state is None or state.response_url is None:
        await _fail_usage_and_task(
            request,
            task,
            usage,
            'image_provider_state_missing',
            restore_prepaid=False,
        )
        return None
    if task.delivery_attempts >= _IMAGE_DELIVERY_MAX_ATTEMPTS:
        await _fail_usage_and_task(
            request,
            task,
            usage,
            'image_delivery_attempts_exceeded',
            restore_prepaid=False,
        )
        return None
    return state


async def _perform_image_recovery(
    run: _RecoveryRun,
    request: Request,
    task: ImageGenerationTask,
    usage: CreditUsage,
    state: Any,
) -> None:
    from open_webui.routers.images import _capture_fal_image_result, get_image_config

    user = await Users.get_user_by_id(task.user_id)
    if user is None:
        raise RuntimeError('image recovery user no longer exists')
    api_key, base_url = _fal_credentials(await get_image_config(), task.kind)
    run.attempts = await _increment_delivery_attempts(task.id)
    observer = await try_resume_provider_invocation(
        task_id=task.id,
        provider_request_id=state.provider_request_id,
    )
    result = await resume_fal_queue(
        status_url=state.status_url,
        response_url=state.response_url,
        api_key=api_key,
        base_url=base_url,
        observer=observer,
    )
    run.batch = await _capture_fal_image_result(
        request,
        result,
        {},
        {'generation_task_id': task.id, 'image_recovery': True},
        user,
    )
    if not run.batch.images:
        raise RuntimeError('image provider returned no usable media URL')
    urls = [image.url for image in run.batch.images]
    async with credit_session() as session, session.begin():
        await finalize_created_images(session, _capture_context(task, usage), run.batch)
        if await mark_usage_succeeded_in_session(session, usage.id, urls) != 1:
            raise RuntimeError('image usage recovery success transition failed')
    run.terminal_committed = True
    await _set_task_state(task.id, status='succeeded', result=[{'url': url} for url in urls])
    await _publish_image_task_event(request.app, task.id, task.user_id, 'succeeded')


async def _handle_image_recovery_failure(
    run: _RecoveryRun,
    request: Request,
    task: ImageGenerationTask,
    usage: CreditUsage,
) -> None:
    if run.terminal_committed:
        restored = await _completed_result_from_creations(request, task.id, task.user_id)
        if restored is not None:
            await _set_task_state(task.id, status='succeeded', result=restored)
        return
    await _cleanup_batch(run.batch)
    if run.attempts >= _IMAGE_DELIVERY_MAX_ATTEMPTS:
        await _fail_usage_and_task(
            request,
            task,
            usage,
            'image_delivery_attempts_exceeded',
            restore_prepaid=False,
        )
    else:
        await _set_task_state(task.id, status='running', error_code='image_delivery_pending')


async def recover_generation_task(task_id: str, request: Request) -> None:
    """Resume a persisted FAL image request without issuing another paid POST."""
    task, usage = await _load_active_task_and_usage(task_id)
    if task is None:
        return
    if await _recovery_already_resolved(request, task, usage):
        return
    assert usage is not None
    state = await _load_usable_provider_state(request, task, usage)
    if state is None:
        return
    run = _RecoveryRun(attempts=task.delivery_attempts)
    try:
        await _perform_image_recovery(run, request, task, usage, state)
    except asyncio.CancelledError:
        if not run.terminal_committed:
            await _cleanup_batch(run.batch)
        raise
    except Exception:
        log.exception('Image recovery task %s failed', task.id)
        await _handle_image_recovery_failure(run, request, task, usage)


async def recover_incomplete_generation_tasks(request: Request) -> int:
    async with creation_session() as session:
        rows = (
            await session.scalars(
                select(ImageGenerationTask).where(ImageGenerationTask.status.in_(_ACTIVE_IMAGE_TASK_STATUSES))
            )
        ).all()
    running: dict[str, asyncio.Task] = request.app.state.creation_generation_tasks
    scheduled = 0

    for row in rows:
        if row.id in running:
            continue
        schedule_tracked_task(
            running,
            row.id,
            lambda task_id=row.id: recover_generation_task(task_id, request),
            kind='image-generation-recovery',
            logger=log,
            name=f'image-generation-recovery:{row.id}',
        )
        scheduled += 1
    return scheduled


__all__ = ['recover_generation_task', 'recover_incomplete_generation_tasks']
