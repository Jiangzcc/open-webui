from __future__ import annotations

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
from open_webui.extensions.videos.limits import (
    acquire_video_generation_slot,
    enforce_video_generation_rate,
    release_video_generation_slot,
)
from open_webui.extensions.videos.schemas import (
    VideoTaskListResponse,
    VideoTaskResponse,
    VideoTaskSubmitForm,
)
from open_webui.extensions.videos.service import (
    create_video_task,
    delete_video_task,
    get_video_task,
    get_video_task_by_idempotency_key,
    list_video_tasks,
    schedule_video_task,
)
from open_webui.internal.db import get_async_session
from open_webui.utils.auth import get_verified_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/v1/videos', tags=['videos'])


@router.get('/models')
async def get_video_models(
    _user=Depends(get_verified_user),
    model_session: AsyncSession = Depends(get_async_session),
) -> dict[str, object]:
    return await public_video_catalog_for_user(model_session)


@router.post('/tasks', response_model=VideoTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_video_task(  # noqa: C901 - admission, idempotency, and slot cleanup share one lifecycle
    request: Request,
    submission: VideoTaskSubmitForm,
    idempotency_key: Annotated[str | None, Header(alias='Idempotency-Key')] = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
    model_session: AsyncSession = Depends(get_async_session),
):
    key = (idempotency_key or str(uuid4())).strip()
    if not key or len(key) > 128:
        raise HTTPException(status_code=422, detail='invalid idempotency key')
    await ensure_model_enabled(
        model_session,
        submission.model,
        media_kind='video',
    )
    existing = await get_video_task_by_idempotency_key(session, user.id, key)
    if existing is not None:
        return existing
    # 提交速率限流：在落库前拦截刷量请求，避免无效任务占据 DB 行 + 调度槽。
    # 与 images/limits.py 一致：Redis 滚窗 + 内存兜底；超限返回 429。
    try:
        enforce_video_generation_rate(user.id)
    except CreditError as error:
        return public_credit_error_response(error)
    # 配额前置校验：在调度前预检余额，避免任务进 run_video_task 才发现余额不足，
    # 浪费 DB 行 + 用户看到「生成失败」而非「余额不足」的清晰提示。
    # quote 只读账户与定价表，不扣费、不占位。
    try:
        await quote_video_usage(user, submission)
    except VideoInputError as error:
        return JSONResponse(status_code=422, content={'detail': str(error)})
    except CreditError as error:
        return public_credit_error_response(error)
    # 并发槽：每用户进行中任务上限。acquire 后无论后续成功失败都必须 release。
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
    except (VideoInputError, ValueError) as error:
        await release_video_generation_slot(user.id)
        return JSONResponse(status_code=422, content={'detail': str(error)})
    except Exception:
        await release_video_generation_slot(user.id)
        raise
    if created:
        try:
            schedule_video_task(
                request,
                task.id,
                user,
                on_finished=lambda: release_video_generation_slot(user.id),
            )
        except Exception:
            await release_video_generation_slot(user.id)
            raise
    else:
        await release_video_generation_slot(user.id)
    return task


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
    if not await delete_video_task(session, user.id, task_id):
        raise HTTPException(status_code=404, detail='video task not found')
