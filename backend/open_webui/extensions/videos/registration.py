from __future__ import annotations

import logging

from fastapi import FastAPI
from open_webui.extensions.videos.service import (
    fail_incomplete_video_tasks,
    shutdown_video_tasks,
)

log = logging.getLogger(__name__)


async def initialize_videos_extension(app: FastAPI) -> None:
    app.state.video_generation_tasks = {}
    interrupted = await fail_incomplete_video_tasks()
    if interrupted:
        log.warning('Marked %s interrupted video generation task(s) as failed', interrupted)


async def shutdown_videos_extension(app: FastAPI) -> None:
    await shutdown_video_tasks(app)


__all__ = ['initialize_videos_extension', 'shutdown_videos_extension']
