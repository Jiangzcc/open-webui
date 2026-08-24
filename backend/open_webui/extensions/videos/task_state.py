"""Durable video provider snapshots and recovery state persistence."""

from __future__ import annotations

import asyncio
import logging

from open_webui.extensions.creations.db import creation_session
from open_webui.extensions.creations.models import VideoGenerationTask
from open_webui.extensions.fal_catalog.video_schemas import FalVideoModelDefinition
from open_webui.extensions.provider_ops.service import load_provider_recovery_state
from open_webui.extensions.videos.delivery import _now
from open_webui.extensions.videos.execution_types import VideoExecutionError
from sqlalchemy import update

log = logging.getLogger(__name__)


def task_has_provider_submission(row: VideoGenerationTask) -> bool:
    return bool(row.provider_request_id or row.provider_response_url or row.provider_result_url)


def provider_execution_snapshot(
    row: VideoGenerationTask,
) -> tuple[FalVideoModelDefinition, dict[str, object]]:
    """Load the immutable provider contract captured before task creation."""
    definition = row.provider_definition_json
    payload = row.provider_payload_json
    if not isinstance(definition, dict) or not isinstance(payload, dict):
        raise VideoExecutionError('video_execution_snapshot_missing')
    try:
        return FalVideoModelDefinition.model_validate(definition), dict(payload)
    except ValueError as error:
        raise VideoExecutionError('video_execution_snapshot_invalid') from error


def _provider_url(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.startswith('https://'):
        return None
    return value[:4096]


async def persist_task_recovery_values(task_id: str, values: dict[str, object]) -> None:
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


async def persist_provider_submission(task_id: str, payload: dict[str, object]) -> None:
    request_id = payload.get('request_id')
    await persist_task_recovery_values(
        task_id,
        {
            'provider_request_id': request_id[:128] if isinstance(request_id, str) else None,
            'provider_status_url': _provider_url(payload, 'status_url'),
            'provider_response_url': _provider_url(payload, 'response_url'),
            'updated_at': _now(),
        },
    )


async def persist_provider_result_url(task_id: str, result_url: str) -> None:
    if not result_url.startswith('https://'):
        raise VideoExecutionError('video_result_invalid_url', provider_completed=True)
    await persist_task_recovery_values(
        task_id,
        {'provider_result_url': result_url[:4096], 'updated_at': _now()},
    )


async def merged_provider_recovery_values(
    task_id: str,
    row: VideoGenerationTask,
) -> tuple[str | None, str | None, str | None, str | None, bool]:
    request_id = row.provider_request_id
    status_url = row.provider_status_url
    response_url = row.provider_response_url
    result_url = row.provider_result_url
    fallback = await load_provider_recovery_state(task_id, request_id)
    if fallback is not None:
        request_id = request_id or fallback.provider_request_id
        status_url = status_url or fallback.status_url
        response_url = response_url or fallback.response_url
        result_url = result_url or fallback.result_url
        try:
            await persist_task_recovery_values(
                task_id,
                {
                    'provider_request_id': request_id,
                    'provider_status_url': status_url,
                    'provider_response_url': response_url,
                    'provider_result_url': result_url,
                    'updated_at': _now(),
                },
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            # Provider Ops remains sufficient for this pass; backfill can heal later.
            log.exception('Could not backfill provider recovery state for video task %s', task_id)
    submitted = bool(request_id or status_url or response_url or result_url)
    return request_id, status_url, response_url, result_url, submitted


__all__ = [
    'merged_provider_recovery_values',
    'persist_provider_result_url',
    'persist_provider_submission',
    'provider_execution_snapshot',
    'task_has_provider_submission',
]
