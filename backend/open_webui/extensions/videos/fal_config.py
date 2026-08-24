from __future__ import annotations

import logging
import os

from open_webui.extensions.videos.execution_types import VideoExecutionError
from open_webui.models.config import Config

VIDEO_FAL_MOCK_ENABLED_KEY = 'video_generation.fal.mock_enabled'
VIDEO_FAL_API_KEY_KEY = 'video_generation.fal.api_key'
IMAGE_FAL_API_KEY_KEY = 'image_generation.fal.api_key'

log = logging.getLogger(__name__)


def positive_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        log.warning('Ignoring invalid %s=%r', name, value)
        return default
    if parsed <= 0:
        log.warning('Ignoring non-positive %s=%r', name, value)
        return default
    return parsed


async def get_video_fal_settings() -> tuple[bool, str]:
    """Return the explicit mock gate and effective video API key."""
    values = await Config.get_many(
        VIDEO_FAL_MOCK_ENABLED_KEY,
        VIDEO_FAL_API_KEY_KEY,
        IMAGE_FAL_API_KEY_KEY,
    )
    mock_enabled = bool(values.get(VIDEO_FAL_MOCK_ENABLED_KEY, False))
    video_key = values.get(VIDEO_FAL_API_KEY_KEY)
    image_key = values.get(IMAGE_FAL_API_KEY_KEY)
    api_key = video_key.strip() if isinstance(video_key, str) else ''
    if not api_key and isinstance(image_key, str):
        api_key = image_key.strip()
    return mock_enabled, api_key


def enforce_fal_video_policy(*, model_id: str, charged_credits: int) -> None:
    """Apply optional server-side guards before a paid FAL task is queued."""
    raw_allowlist = os.getenv('VIDEO_GENERATION_FAL_ALLOWED_MODELS', '').strip()
    if raw_allowlist:
        allowed = {item.strip() for item in raw_allowlist.split(',') if item.strip()}
        if model_id not in allowed:
            raise VideoExecutionError('video_fal_model_not_allowed')

    raw_limit = os.getenv('VIDEO_GENERATION_FAL_MAX_CREDITS_PER_REQUEST', '').strip()
    if not raw_limit:
        return
    try:
        limit = int(raw_limit)
    except ValueError as error:
        raise VideoExecutionError('video_fal_policy_invalid') from error
    if limit <= 0:
        raise VideoExecutionError('video_fal_policy_invalid')
    if charged_credits > limit:
        raise VideoExecutionError('video_fal_cost_limit_exceeded')


__all__ = ['enforce_fal_video_policy', 'get_video_fal_settings', 'positive_int_env']
