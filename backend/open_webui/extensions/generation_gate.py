"""共享的生成限流与进程内并发槽（复盘：机制收敛）。

图片（extensions/images/limits.py）与视频（extensions/videos/limits.py）
此前各维护一份近乎相同的 RateLimiter + 每用户并发计数实现；收敛为
``GenerationGate``，每种媒体类型持有独立实例，保持桶前缀、计数器与
asyncio.Lock 互不共享。单 worker 部署前提下进程内计数即为准确口径。
"""

from __future__ import annotations

import asyncio

from open_webui.extensions.credits.errors import CreditError
from open_webui.utils.rate_limit import RateLimiter
from open_webui.utils.redis import get_redis_client


class GenerationGate:
    """Per-user request-rate limiter plus in-process concurrency slots."""

    def __init__(
        self,
        *,
        bucket_prefix: str,
        limit: int,
        window_seconds: int,
        max_concurrent_per_user: int,
    ) -> None:
        self._limiter = RateLimiter(
            get_redis_client(async_mode=False),
            limit=limit,
            window=window_seconds,
            bucket_size=10,
        )
        self._bucket_prefix = bucket_prefix
        self._max_concurrent_per_user = max_concurrent_per_user
        self._active_by_user: dict[str, int] = {}
        self._active_lock = asyncio.Lock()

    def enforce_rate(self, user_id: str) -> None:
        if self._limiter.is_limited(f'{self._bucket_prefix}:{user_id}'):
            raise CreditError(code='rate_limited', context={'reason': 'request_rate'})

    async def acquire_slot(self, user_id: str) -> None:
        async with self._active_lock:
            active = self._active_by_user.get(user_id, 0)
            if active >= self._max_concurrent_per_user:
                raise CreditError(code='rate_limited', context={'reason': 'concurrency'})
            self._active_by_user[user_id] = active + 1

    async def release_slot(self, user_id: str) -> None:
        async with self._active_lock:
            active = self._active_by_user.get(user_id, 0)
            if active <= 1:
                self._active_by_user.pop(user_id, None)
            else:
                self._active_by_user[user_id] = active - 1


__all__ = ['GenerationGate']
