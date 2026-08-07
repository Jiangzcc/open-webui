from __future__ import annotations

import asyncio

from open_webui.extensions.credits.errors import CreditError
from open_webui.utils.rate_limit import RateLimiter
from open_webui.utils.redis import get_redis_client

IMAGE_GENERATION_RATE_LIMIT = 10
IMAGE_GENERATION_RATE_WINDOW_SECONDS = 60
IMAGE_GENERATION_MAX_CONCURRENT_PER_USER = 3

_request_limiter = RateLimiter(
    get_redis_client(async_mode=False),
    limit=IMAGE_GENERATION_RATE_LIMIT,
    window=IMAGE_GENERATION_RATE_WINDOW_SECONDS,
    bucket_size=10,
)
_active_by_user: dict[str, int] = {}
_active_lock = asyncio.Lock()


def enforce_image_generation_rate(user_id: str) -> None:
    if _request_limiter.is_limited(f'images:generation:{user_id}'):
        raise CreditError(code='rate_limited', context={'reason': 'request_rate'})


async def acquire_image_generation_slot(user_id: str) -> None:
    async with _active_lock:
        active = _active_by_user.get(user_id, 0)
        if active >= IMAGE_GENERATION_MAX_CONCURRENT_PER_USER:
            raise CreditError(code='rate_limited', context={'reason': 'concurrency'})
        _active_by_user[user_id] = active + 1


async def release_image_generation_slot(user_id: str) -> None:
    async with _active_lock:
        active = _active_by_user.get(user_id, 0)
        if active <= 1:
            _active_by_user.pop(user_id, None)
        else:
            _active_by_user[user_id] = active - 1


__all__ = [
    'acquire_image_generation_slot',
    'enforce_image_generation_rate',
    'release_image_generation_slot',
]
