from __future__ import annotations

import logging

import anyio
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from open_webui.env import DATABASE_SCHEMA
from sqlalchemy import inspect

from .db import engine
from .events import init_generation_event_bus
from .generation_tasks import fail_incomplete_generation_tasks, shutdown_generation_tasks
from .migrations.runner import _migration_config, run_creation_migrations
from .models import CreationBase

log = logging.getLogger(__name__)

_REQUIRED_TABLES = frozenset(table.name for table in CreationBase.metadata.sorted_tables)
_REQUIRED_UNIQUE = {
    'ext_creation_media_item': frozenset({'uq_ext_creation_media_file'}),
    'ext_creation_post_media': frozenset(
        {'uq_ext_creation_post_media_creation', 'uq_ext_creation_post_media_position'}
    ),
    'ext_creation_post_reaction': frozenset({'uq_ext_creation_post_reaction_actor_kind'}),
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


def _schema_tables(inspector) -> set[str]:
    return set(inspector.get_table_names(schema=DATABASE_SCHEMA))


def _validate_named_objects(inspector, required_by_table, inspector_method: str, label: str) -> None:
    getter = getattr(inspector, inspector_method)
    for table_name, required in required_by_table.items():
        existing = {item['name'] for item in getter(table_name, schema=DATABASE_SCHEMA)}
        missing = required - existing
        if missing:
            raise RuntimeError(f'creation migration validation failed: {table_name} missing {label} {sorted(missing)}')


def _validate_creation_schema() -> None:
    with engine.connect() as connection:
        inspector = inspect(connection)
        missing_tables = _REQUIRED_TABLES - _schema_tables(inspector)
        if missing_tables:
            raise RuntimeError(f'creation migration validation failed: missing tables {sorted(missing_tables)}')

        config = _migration_config(DATABASE_SCHEMA)
        expected_heads = set(ScriptDirectory.from_config(config).get_heads())
        current_heads = set(
            MigrationContext.configure(
                connection,
                opts={
                    'version_table': 'ext_creation_schema_version',
                    'version_table_schema': DATABASE_SCHEMA,
                },
            ).get_current_heads()
        )
        if current_heads != expected_heads:
            raise RuntimeError(
                'creation migration validation failed: '
                f'expected version {sorted(expected_heads)}, got {sorted(current_heads)}'
            )

        _validate_named_objects(
            inspector,
            _REQUIRED_UNIQUE,
            'get_unique_constraints',
            'unique constraints',
        )
        _validate_named_objects(
            inspector,
            _REQUIRED_CHECKS,
            'get_check_constraints',
            'check constraints',
        )
        _validate_named_objects(inspector, _REQUIRED_INDEXES, 'get_indexes', 'indexes')

        for table_name in _REQUIRED_TABLES:
            foreign_keys = inspector.get_foreign_keys(table_name, schema=DATABASE_SCHEMA)
            if foreign_keys:
                raise RuntimeError(f'creation migration validation failed: {table_name} must not declare foreign keys')


async def initialize_creations_extension(app: FastAPI) -> None:
    """Run the creation migration chain and validate the resulting schema.

    Media capture still piggy-backs on the credits terminal transaction. Direct
    image-page submissions additionally keep a tracked set of in-process tasks
    so the HTTP request can return immediately while status remains queryable.
    """
    await anyio.to_thread.run_sync(run_creation_migrations)
    await anyio.to_thread.run_sync(_validate_creation_schema)
    app.state.creation_generation_tasks = {}
    # 初始化任务事件总线，供 SSE 端点与任务执行体共享。早于 fail_incomplete
    # 初始化，确保中断任务标记失败时也能广播（尽管此时无订阅者，会安全跳过）。
    init_generation_event_bus(app)
    interrupted = await fail_incomplete_generation_tasks()
    if interrupted:
        log.warning('Marked %s interrupted image generation task(s) as failed', interrupted)


async def shutdown_creations_extension(app: FastAPI) -> None:
    await shutdown_generation_tasks(app)


__all__ = ['initialize_creations_extension', 'shutdown_creations_extension']
