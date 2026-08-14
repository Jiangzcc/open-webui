from __future__ import annotations

import asyncio

from open_webui.extensions.credits.errors import CreditError
from open_webui.utils.rate_limit import RateLimiter
from open_webui.utils.redis import get_redis_client

# 视频生成限流与并发槽：镜像 images/limits.py 的模式，但使用 video: 前缀的
# 限流桶与并发计数，避免与图片生成共享同一配额。视频任务通常更重、更慢，
# 因此默认并发上限更保守（每用户 1 个进行中任务），提交速率也更低。
VIDEO_GENERATION_RATE_LIMIT = 4
VIDEO_GENERATION_RATE_WINDOW_SECONDS = 60
VIDEO_GENERATION_MAX_CONCURRENT_PER_USER = 1

_request_limiter = RateLimiter(
    get_redis_client(async_mode=False),
    limit=VIDEO_GENERATION_RATE_LIMIT,
    window=VIDEO_GENERATION_RATE_WINDOW_SECONDS,
    bucket_size=10,
)
_active_by_user: dict[str, int] = {}
_active_lock = asyncio.Lock()


def enforce_video_generation_rate(user_id: str) -> None:
    if _request_limiter.is_limited(f'videos:generation:{user_id}'):
        raise CreditError(code='rate_limited', context={'reason': 'request_rate'})


async def acquire_video_generation_slot(user_id: str) -> None:
    async with _active_lock:
        active = _active_by_user.get(user_id, 0)
        if active >= VIDEO_GENERATION_MAX_CONCURRENT_PER_USER:
            raise CreditError(code='rate_limited', context={'reason': 'concurrency'})
        _active_by_user[user_id] = active + 1


async def release_video_generation_slot(user_id: str) -> None:
    async with _active_lock:
        active = _active_by_user.get(user_id, 0)
        if active <= 1:
            _active_by_user.pop(user_id, None)
        else:
            _active_by_user[user_id] = active - 1


__all__ = [
    'acquire_video_generation_slot',
    'enforce_video_generation_rate',
    'release_video_generation_slot',
]
