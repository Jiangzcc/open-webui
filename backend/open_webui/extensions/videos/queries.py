"""视频任务的查询与创建（CRUD）层，从 service.py 拆出（复盘：超长文件拆分）。

service.py 保留任务运行时（run/recover/调度）与状态持久化；本模块承载
HTTP 路由直接消费的数据库访问：任务创建（幂等）、查询、列表分页、删除，
以及持久化任务与提交表单之间的映射。
"""

from __future__ import annotations

import json
from uuid import uuid4

from open_webui.extensions.creations.models import VideoGenerationTask
from open_webui.extensions.creations.schemas import decode_keyset_cursor, encode_keyset_cursor
from open_webui.extensions.fal_catalog.video_schemas import FalVideoModelDefinition
from open_webui.extensions.videos.catalog import build_video_provider_payload
from open_webui.extensions.videos.delivery import _now
from open_webui.extensions.videos.schemas import (
    VideoAssetReference,
    VideoTaskListResponse,
    VideoTaskResponse,
    VideoTaskResult,
    VideoTaskSubmitForm,
)
from open_webui.models.files import Files
from sqlalchemy import and_, delete, desc, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# 仅终态任务可删（router 预检查与 DELETE 谓词共用同一来源）。
DELETABLE_STATUSES = ('succeeded', 'failed')


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
        # prompt/params 即用户输入的纯文本（标签点击时已直接插入 insert_text）。
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


def _submission_from_task(task: VideoTaskResponse) -> VideoTaskSubmitForm:
    """从持久化任务重建提交表单（run/recovery 复用）。

    params_json 里 JSON 字段（如 kling multi_prompt）以解析后的 dict/list
    落库以便前端直接消费；表单的 params 只接受标量值，重建时需把非标量值
    序列化回 JSON 字符串，否则 pydantic 校验直接失败、任务必然进入 failed。
    """
    params: dict[str, bool | str | int | float | None] = {
        key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
        for key, value in task.params.items()
    }
    return VideoTaskSubmitForm(
        task=task.task,
        model=task.model_id,
        prompt=task.prompt,
        assets=tuple(VideoAssetReference.model_validate(item) for item in task.assets),
        params=params,
    )


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
    """删除视频任务（仅终态）。

    「终态才可删」的谓词直接放进 DELETE：校验与删除之间任务可能被恢复循环
    置为 running（TOCTOU），此时本条 DELETE 影响 0 行，调用方应回 409，
    避免删除已扣费但仍在执行的任务、留下孤儿媒体记录。
    """
    result = await session.execute(
        delete(VideoGenerationTask).where(
            VideoGenerationTask.id == task_id,
            VideoGenerationTask.user_id == user_id,
            VideoGenerationTask.status.in_(DELETABLE_STATUSES),
        )
    )
    await session.commit()
    return bool(result.rowcount)


async def video_task_exists(session: AsyncSession, user_id: str, task_id: str) -> bool:
    result = await session.scalar(
        select(VideoGenerationTask.id).where(
            VideoGenerationTask.id == task_id,
            VideoGenerationTask.user_id == user_id,
        )
    )
    return result is not None
