"""共享的生成限流与进程内并发槽（复盘：机制收敛）。

图片（extensions/images/limits.py）与视频（extensions/videos/limits.py）
此前各维护一份近乎相同的 RateLimiter + 每用户并发计数实现；收敛为
``GenerationGate``，每种媒体类型持有独立实例，保持桶前缀、计数器与
asyncio.Lock 互不共享。单 worker 部署前提下进程内计数即为准确口径。
"""

from __future__ import annotations

import asyncio
import logging
import time

from open_webui.env import REDIS_KEY_PREFIX
from open_webui.extensions.credits.errors import CreditError
from open_webui.utils.rate_limit import RateLimiter
from open_webui.utils.redis import get_redis_client

log = logging.getLogger(__name__)

# 滚动窗口分桶粒度：与上游 RateLimiter 的 key 布局保持一致，切换实现时共享计数。
_BUCKET_SIZE_SECONDS = 10
# Redis 单次限流检查的总超时（复盘 P1）：未配置 socket_timeout 时 redis-py
# 默认无限等待；超时或故障一律回退进程内内存限流，请求不能无限挂起。
_REDIS_CHECK_TIMEOUT_SECONDS = 2.0


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
        # EXT: 二开新增（复盘 P1）—— 上游 RateLimiter 只有同步 Redis 路径，
        # 在 async 请求处理中直接调用会在事件循环线程里执行阻塞网络 I/O
        # （单 worker 部署下 Redis 慢/挂起会卡死全部请求）。因此取
        # redis.asyncio 客户端自行实现同一滚动窗口算法；上游 RateLimiter
        # 保留为 Redis 缺失/故障时的进程内内存回退（client=None 走内存路径）。
        self._redis = get_redis_client(async_mode=True)
        self._fallback_limiter = RateLimiter(
            None,
            limit=limit,
            window=window_seconds,
            bucket_size=_BUCKET_SIZE_SECONDS,
        )
        self._limit = limit
        self._window_seconds = window_seconds
        self._num_buckets = window_seconds // _BUCKET_SIZE_SECONDS
        self._bucket_prefix = bucket_prefix
        self._max_concurrent_per_user = max_concurrent_per_user
        self._active_by_user: dict[str, int] = {}
        self._active_lock = asyncio.Lock()

    async def enforce_rate(self, user_id: str) -> None:
        if await self._is_limited(f'{self._bucket_prefix}:{user_id}'):
            raise CreditError(code='rate_limited', context={'reason': 'request_rate'})

    async def _is_limited(self, key: str) -> bool:
        if self._redis is None:
            return self._fallback_limiter.is_limited(key)
        try:
            return await asyncio.wait_for(
                self._is_limited_redis(key),
                timeout=_REDIS_CHECK_TIMEOUT_SECONDS,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            log.warning(
                'Generation gate Redis check failed; falling back to in-memory limiter',
                exc_info=True,
            )
            return self._fallback_limiter.is_limited(key)

    async def _is_limited_redis(self, key: str) -> bool:
        # 与上游 RateLimiter 相同的算法与 key 布局，仅改为 await 逐命令执行。
        now_bucket = int(time.time()) // _BUCKET_SIZE_SECONDS
        bucket_key = self._bucket_key(key, now_bucket)

        attempts = await self._redis.incr(bucket_key)
        if attempts == 1:
            await self._redis.expire(bucket_key, self._window_seconds + _BUCKET_SIZE_SECONDS)

        buckets = [self._bucket_key(key, now_bucket - i) for i in range(self._num_buckets + 1)]
        counts = await self._redis.mget(buckets)
        return sum(int(count) for count in counts if count) > self._limit

    @staticmethod
    def _bucket_key(key: str, bucket_index: int) -> str:
        return f'{REDIS_KEY_PREFIX}:ratelimit:{key.lower()}:{bucket_index}'

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
