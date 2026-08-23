from __future__ import annotations

from threading import Lock

from open_webui.extensions.credits.constants import (
    CREDIT_QUOTE_CACHE_MAX_ENTRIES,
    CREDIT_QUOTE_CACHE_TTL_SECONDS,
)

# 报价缓存（进程内 TTL+LRU）。当前部署形态为单 worker：进程内缓存即全局
# 缓存。复盘 #12 移除了为多 worker 准备的 Redis 双路径——该部署模式不存在，
# 双路径只增加降级分支和"配置了 Redis 但不可用"的告警噪音。
#
# 缓存键：(user_id, price_id, action:request_hash, price.updated_at)。
# price.updated_at 已编码进键，价格变更后旧键自然失效，无需显式失效逻辑。

_memory_cache: dict[tuple[str, str, str, int], tuple[float, dict[str, object]]] = {}
# 保护 LRU 驱逐的 check-then-act 操作，避免并发协程在检查长度 → pop → 写入
# 之间交错导致缓存超限或驱逐错误条目。
_memory_lock = Lock()


async def get_cached_quote(
    cache_key: tuple[str, str, str, int],
    balance: int,
    now: float,
) -> dict[str, object] | None:
    """读缓存。命中时复用缓存的报价，但用当前余额覆写 balance/sufficient。"""
    with _memory_lock:
        cached = _memory_cache.get(cache_key)
        if cached is not None and cached[0] <= now:
            _memory_cache.pop(cache_key, None)
            cached = None
        cached_value = dict(cached[1]) if cached is not None else None
    if cached_value is not None:
        cached_value['balance'] = balance
        cached_value['sufficient'] = balance >= cached_value.get('charged_credits', 0)
    return cached_value


async def cache_quote(cache_key: tuple[str, str, str, int], response: dict[str, object], now: float) -> None:
    """写缓存。balance/sufficient 随余额实时变化，存储前剥离。"""
    storable = {k: v for k, v in response.items() if k not in ('balance', 'sufficient')}
    with _memory_lock:
        if len(_memory_cache) >= CREDIT_QUOTE_CACHE_MAX_ENTRIES:
            oldest_key = min(_memory_cache, key=lambda key: _memory_cache[key][0])
            _memory_cache.pop(oldest_key, None)
        _memory_cache[cache_key] = (now + CREDIT_QUOTE_CACHE_TTL_SECONDS, dict(storable))


def memory_cache() -> dict[tuple[str, str, str, int], tuple[float, dict[str, object]]]:
    """进程内缓存本体。router._quote_cache 测试桩别名指向它（旧测试直接
    clear/注入缓存）；生产读写请使用 get_cached_quote / cache_quote。"""
    return _memory_cache


__all__ = [
    'cache_quote',
    'get_cached_quote',
    'memory_cache',
]
