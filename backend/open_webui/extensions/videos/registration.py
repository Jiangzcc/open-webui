from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from open_webui.extensions.creations.recovery_request import recovery_request
from open_webui.extensions.videos.executor import cleanup_stale_fal_video_temp_files
from open_webui.extensions.videos.service import (
    recover_incomplete_video_tasks,
    shutdown_video_tasks,
)
from starlette.requests import Request

log = logging.getLogger(__name__)
_RECOVERY_INTERVAL_SECONDS = 60


async def _video_recovery_worker(request: Request) -> None:
    while True:
        await asyncio.sleep(_RECOVERY_INTERVAL_SECONDS)
        try:
            await recover_incomplete_video_tasks(request)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception('Video recovery pass failed')


async def initialize_videos_extension(app: FastAPI) -> None:
    app.state.video_generation_tasks = {}
    removed = await cleanup_stale_fal_video_temp_files()
    if removed:
        log.info('Removed %s stale FAL video temporary file(s)', removed)
    request = recovery_request(app)
    recovered = await recover_incomplete_video_tasks(request)
    if recovered:
        log.info('Scheduled %s persisted video task(s) for recovery', recovered)
    app.state.video_recovery_task = asyncio.create_task(
        _video_recovery_worker(request),
        name='video-delivery-recovery',
    )


async def shutdown_videos_extension(app: FastAPI) -> None:
    recovery = getattr(app.state, 'video_recovery_task', None)
    if recovery is not None:
        recovery.cancel()
        try:
            await recovery
        except asyncio.CancelledError:
            pass
        delattr(app.state, 'video_recovery_task')
    await shutdown_video_tasks(app)


__all__ = ['initialize_videos_extension', 'shutdown_videos_extension']
