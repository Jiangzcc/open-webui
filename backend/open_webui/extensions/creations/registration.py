from __future__ import annotations

import asyncio
import logging

import anyio
from fastapi import FastAPI
from open_webui.extensions.migration_kit import SchemaGuard, validate_schema
from starlette.requests import Request

from .events import init_generation_event_bus
from .generation_tasks import shutdown_generation_tasks
from .image_recovery import recover_incomplete_generation_tasks
from .migrations.runner import SPEC, run_creation_migrations
from .models import CreationBase
from .recovery_request import recovery_request

log = logging.getLogger(__name__)
_RECOVERY_INTERVAL_SECONDS = 60

_REQUIRED_TABLES = frozenset(table.name for table in CreationBase.metadata.sorted_tables)
_REQUIRED_UNIQUE = {
    'ext_creation_media_item': frozenset({'uq_ext_creation_media_file'}),
    'ext_creation_post_media': frozenset({'uq_ext_creation_post_media_creation'}),
    'ext_image_generation_task': frozenset({'uq_ext_image_task_user_key'}),
    'ext_video_generation_task': frozenset({'uq_ext_video_task_user_key'}),
}
_REQUIRED_CHECKS = {
    'ext_creation_media_item': frozenset(
        {
            'ck_ext_creation_media_kind',
            'ck_ext_creation_media_task',
            'ck_ext_creation_media_source',
            'ck_ext_creation_media_duration',
        }
    ),
    'ext_creation_post': frozenset(
        {
            'ck_ext_creation_post_status',
            'ck_ext_creation_post_like_count',
            'ck_ext_creation_post_favorite_count',
            'ck_ext_creation_post_featured_rank',
        }
    ),
    'ext_creation_post_reaction': frozenset({'ck_ext_creation_post_reaction_kind'}),
    'ext_image_generation_task': frozenset(
        {
            'ck_ext_image_task_status',
            'ck_ext_image_task_kind',
            'ck_ext_image_task_expected_count',
            'ck_ext_image_task_execution_mode',
            'ck_ext_image_task_delivery_attempts',
        }
    ),
    'ext_video_generation_task': frozenset(
        {
            'ck_ext_video_task_status',
            'ck_ext_video_task_kind',
            'ck_ext_video_task_execution_mode',
            'ck_ext_video_task_delivery_attempts',
        }
    ),
    'ext_creation_category': frozenset({'ck_ext_creation_category_sort_order'}),
}
_REQUIRED_INDEXES = {
    'ext_creation_media_item': frozenset(
        {
            'ix_ext_creation_media_user_visible_created',
            'ix_ext_creation_media_visible_created',
            'ix_ext_creation_media_batch',
        }
    ),
    'ext_creation_post': frozenset(
        {
            'ix_ext_creation_post_status_published',
            'ix_ext_creation_post_status_popular',
            'ix_ext_creation_post_user_status',
            'ix_ext_creation_post_status_category',
            'ix_ext_creation_post_status_featured',
        }
    ),
    'ext_creation_post_media': frozenset({'ix_ext_creation_post_media_creation'}),
    'ext_creation_post_reaction': frozenset({'ix_ext_creation_post_reaction_user_kind'}),
    'ext_image_generation_task': frozenset(
        {
            'ix_ext_image_task_user_created',
            'ix_ext_image_task_status_updated',
        }
    ),
    'ext_video_generation_task': frozenset(
        {
            'ix_ext_video_task_user_created',
            'ix_ext_video_task_status_updated',
        }
    ),
    'ext_creation_category': frozenset({'ix_ext_creation_category_enabled_order'}),
}

# 创建链的全部表禁止外键（关联关系由应用层维护）。
_SCHEMA_GUARD = SchemaGuard(
    spec=SPEC,
    required_tables=_REQUIRED_TABLES,
    required_unique=_REQUIRED_UNIQUE,
    required_checks=_REQUIRED_CHECKS,
    required_indexes=_REQUIRED_INDEXES,
    expected_foreign_keys={},
)


def _validate_creation_schema() -> None:
    validate_schema(_SCHEMA_GUARD)


async def _image_recovery_worker(request: Request) -> None:
    while True:
        await asyncio.sleep(_RECOVERY_INTERVAL_SECONDS)
        try:
            await recover_incomplete_generation_tasks(request)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception('Image recovery pass failed')


async def initialize_creations_extension(app: FastAPI) -> None:
    """Run the creation migration chain and validate the resulting schema.

    Media capture still piggy-backs on the credits terminal transaction. Direct
    image-page submissions additionally keep a tracked set of in-process tasks
    so the HTTP request can return immediately while status remains queryable.
    """
    await anyio.to_thread.run_sync(run_creation_migrations)
    await anyio.to_thread.run_sync(_validate_creation_schema)
    app.state.creation_generation_tasks = {}
    # 初始化任务事件总线，供 SSE 端点与任务执行体共享。
    init_generation_event_bus(app)
    request = recovery_request(app)
    recovered = await recover_incomplete_generation_tasks(request)
    if recovered:
        log.info('Scheduled %s persisted image task(s) for recovery', recovered)
    app.state.image_recovery_task = asyncio.create_task(
        _image_recovery_worker(request),
        name='image-delivery-recovery',
    )


async def shutdown_creations_extension(app: FastAPI) -> None:
    recovery = getattr(app.state, 'image_recovery_task', None)
    if recovery is not None:
        recovery.cancel()
        try:
            await recovery
        except asyncio.CancelledError:
            pass
        delattr(app.state, 'image_recovery_task')
    await shutdown_generation_tasks(app)


__all__ = ['initialize_creations_extension', 'shutdown_creations_extension']
