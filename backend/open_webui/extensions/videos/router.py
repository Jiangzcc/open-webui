from __future__ import annotations

import logging
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from open_webui.extensions.creations.db import get_creation_session
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.http import public_credit_error_response
from open_webui.extensions.model_ops.service import ensure_model_enabled
from open_webui.extensions.videos.billing import quote_video_usage
from open_webui.extensions.videos.catalog import VideoInputError, public_video_catalog_for_user
from open_webui.extensions.videos.executor import (
    FalVideoExecutor,
    VideoExecutionError,
    enforce_fal_video_policy,
    resolve_video_executor,
)
from open_webui.extensions.videos.limits import (
    acquire_video_generation_slot,
    enforce_video_generation_rate,
    release_video_generation_slot,
)
from open_webui.extensions.videos.queries import (
    DELETABLE_STATUSES,
    VideoIdempotencyConflictError,
    create_video_task,
    delete_video_task,
    get_video_task,
    get_video_task_by_idempotency_key,
    list_video_tasks,
    video_task_exists,
    video_task_matches_submission,
)
from open_webui.extensions.videos.schemas import (
    VideoTaskListResponse,
    VideoTaskResponse,
    VideoTaskSubmitForm,
)
from open_webui.extensions.videos.service import fail_video_task_scheduling, schedule_video_task
from open_webui.internal.db import get_async_session
from open_webui.utils.auth import get_verified_user
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

router = APIRouter(prefix='/api/v1/videos', tags=['videos'])


@router.get('/models')
async def get_video_models(
    _user=Depends(get_verified_user),
    model_session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    return await public_video_catalog_for_user(model_session)


def _idempotency_key(value: str | None) -> str:
    key = (value or str(uuid4())).strip()
    if not key or len(key) > 128:
        raise HTTPException(status_code=422, detail='invalid idempotency key')
    return key


async def _video_admission(
    user: object,
    submission: VideoTaskSubmitForm,
    model_session: AsyncSession,
) -> JSONResponse | None:
    await ensure_model_enabled(model_session, submission.model, media_kind='video')
    try:
        executor = await resolve_video_executor()
        await enforce_video_generation_rate(user.id)
        quote = await quote_video_usage(user, submission)
    except VideoInputError as error:
        return JSONResponse(status_code=422, content={'detail': str(error)})
    except VideoExecutionError as error:
        return JSONResponse(status_code=503, content={'detail': error.code})
    except CreditError as error:
        return public_credit_error_response(error)
    if not isinstance(executor, FalVideoExecutor):
        return None
    try:
        enforce_fal_video_policy(model_id=submission.model, charged_credits=quote.charged_credits or 0)
    except VideoExecutionError as error:
        status_code = 503 if error.code == 'video_fal_policy_invalid' else 403
        return JSONResponse(status_code=status_code, content={'detail': error.code})
    return None


async def _create_and_schedule_video_task(
    request: Request,
    session: AsyncSession,
    user: object,
    submission: VideoTaskSubmitForm,
    key: str,
) -> VideoTaskResponse | JSONResponse:
    try:
        await acquire_video_generation_slot(user.id)
    except CreditError as error:
        return public_credit_error_response(error)
    try:
        task, created = await create_video_task(
            session,
            user_id=user.id,
            idempotency_key=key,
            submission=submission,
        )
    except VideoIdempotencyConflictError:
        await release_video_generation_slot(user.id)
        return JSONResponse(status_code=409, content={'detail': 'idempotency_key_conflict'})
    except (VideoInputError, ValueError) as error:
        await release_video_generation_slot(user.id)
        return JSONResponse(status_code=422, content={'detail': str(error)})
    except Exception:
        await release_video_generation_slot(user.id)
        raise
    if not created:
        await release_video_generation_slot(user.id)
        return task
    try:
        schedule_video_task(request, task.id, user, on_finished=lambda: release_video_generation_slot(user.id))
    except Exception:
        await fail_video_task_scheduling(request.app, task.id, user.id)
        await release_video_generation_slot(user.id)
        raise
    return task


@router.post('/tasks', response_model=VideoTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_video_task(
    request: Request,
    submission: VideoTaskSubmitForm,
    idempotency_key: Annotated[str | None, Header(alias='Idempotency-Key')] = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
    model_session: AsyncSession = Depends(get_async_session),
):
    key = _idempotency_key(idempotency_key)
    existing = await get_video_task_by_idempotency_key(session, user.id, key)
    if existing is not None:
        if not video_task_matches_submission(existing, submission):
            return JSONResponse(status_code=409, content={'detail': 'idempotency_key_conflict'})
        return existing
    rejected = await _video_admission(user, submission, model_session)
    if rejected is not None:
        return rejected
    return await _create_and_schedule_video_task(request, session, user, submission, key)


@router.get('/tasks', response_model=VideoTaskListResponse)
async def get_video_tasks(
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
    since: Annotated[int | None, Query(ge=0)] = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        return await list_video_tasks(session, user.id, limit, cursor, since)
    except ValueError:
        return JSONResponse(status_code=422, content={'detail': 'invalid cursor'})


@router.get('/tasks/{task_id}', response_model=VideoTaskResponse)
async def get_one_video_task(
    task_id: str,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    task = await get_video_task(session, user.id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='video task not found')
    return task


@router.delete('/tasks/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_video_task(
    task_id: str,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    task = await get_video_task(session, user.id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='video task not found')
    if task.status not in DELETABLE_STATUSES:
        # 进行中/待恢复任务删除后 worker 照常扣费并产生孤儿媒体记录
        # （与图片端 delete 守卫一致）。
        raise HTTPException(status_code=409, detail='active video task cannot be deleted')
    if not await delete_video_task(session, user.id, task_id):
        # 终态谓词同时写在 DELETE 里：校验与删除之间任务被恢复循环重新置为
        # running（TOCTOU 竞态）时影响 0 行，按进行中任务拒绝。
        if await video_task_exists(session, user.id, task_id):
            raise HTTPException(status_code=409, detail='active video task cannot be deleted')
        raise HTTPException(status_code=404, detail='video task not found')
