from __future__ import annotations

import json
import logging
from hashlib import sha256

from open_webui.extensions.credits.constants import (
    CREDIT_QUOTE_CACHE_MAX_ENTRIES,
    CREDIT_QUOTE_CACHE_TTL_SECONDS,
)
from open_webui.utils.redis import get_redis_client

log = logging.getLogger(__name__)

# 报价缓存的跨进程实现：原 _quote_cache 是模块级 dict，多 worker 部署时各进程
# 各一份缓存，价格更新后最多 TTL（5s）后才一致。改为 Redis 存储缓存值，
# Redis 不可用时降级到进程内 dict 并告警（对齐 CreditRateLimiter 的 fallback 模式）。
#
# 缓存键与原 dict 键一致：(user_id, price_id, action:request_hash, price.updated_at)。
# price.updated_at 已编码进键，因此价格变更后旧键自然失效，无需显式失效逻辑。
# TTL 由 Redis EXPIRE 保证，避免进程内 dict 的手动过期清理。

_sync_redis = get_redis_client(async_mode=False)

# 进程内 fallback 缓存：仅在 Redis 不可用时使用。
_memory_cache: dict[tuple[str, str, str, int], tuple[float, dict[str, object]]] = {}


def _redis_available() -> bool:
    return _sync_redis is not None


def _redis_key(cache_key: tuple[str, str, str, int]) -> str:
    # 对完整元组做规范化编码并哈希，避免 user/action 等字段未来放宽字符集后
    # 与分隔符产生歧义。缓存 TTL 很短，无需保留人类可读的原始键段。
    encoded = json.dumps(cache_key, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return f'webui:credits:quote:{sha256(encoded).hexdigest()}'


def get_cached_quote(cache_key: tuple[str, str, str, int], balance: int, now: float) -> dict[str, object] | None:
    """读缓存。命中时复用缓存的报价，但用当前余额覆写 balance/sufficient。"""
    if _redis_available():
        try:
            raw = _sync_redis.get(_redis_key(cache_key))
        except Exception:
            log.warning('Quote cache Redis read failed, using process memory fallback')
        else:
            if raw is None:
                # Redis 正常响应但没有该键时，以共享缓存为准。不能读取某个 worker
                # 残留的本地值，否则多进程会对同一请求返回不一致报价。
                return None
            try:
                cached = json.loads(raw)
            except (ValueError, TypeError):
                log.debug('corrupt quote cache entry, ignoring')
                cached = None
            if cached is not None:
                response = dict(cached)
                response['balance'] = balance
                response['sufficient'] = balance >= response.get('charged_credits', 0)
                return response
            return None
    # Redis 未配置或读取异常时才走进程内降级。
    cached = _memory_cache.get(cache_key)
    if cached is not None and cached[0] > now:
        response = dict(cached[1])
        response['balance'] = balance
        response['sufficient'] = balance >= response.get('charged_credits', 0)
        return response
    if cached is not None:
        _memory_cache.pop(cache_key, None)
    return None


def cache_quote(cache_key: tuple[str, str, str, int], response: dict[str, object], now: float) -> None:
    """写缓存。Redis 用 SETEX 带 TTL；内存降级用原 LRU 策略。"""
    # 存储前剥离 balance/sufficient（这俩随余额实时变，不该缓存）。
    storable = {k: v for k, v in response.items() if k not in ('balance', 'sufficient')}
    # 始终写入进程内 fallback，保证 Redis 不可用时的读路径能命中。
    _write_memory_fallback(cache_key, storable, now)
    if _redis_available():
        try:
            _sync_redis.setex(
                _redis_key(cache_key),
                CREDIT_QUOTE_CACHE_TTL_SECONDS,
                json.dumps(storable, default=str),
            )
        except Exception:
            log.warning('Quote cache Redis write failed, using process memory fallback')


def _write_memory_fallback(cache_key: tuple[str, str, str, int], storable: dict[str, object], now: float) -> None:
    if len(_memory_cache) >= CREDIT_QUOTE_CACHE_MAX_ENTRIES:
        oldest_key = min(_memory_cache, key=lambda key: _memory_cache[key][0])
        _memory_cache.pop(oldest_key, None)
    _memory_cache[cache_key] = (now + CREDIT_QUOTE_CACHE_TTL_SECONDS, dict(storable))


def clear_quote_cache_for_test() -> None:
    """测试辅助：清空进程内 fallback 缓存，避免跨用例泄漏。"""
    _memory_cache.clear()


def memory_cache_for_legacy_tests() -> dict[tuple[str, str, str, int], tuple[float, dict[str, object]]]:
    """Expose the single fallback cache to older router tests without duplicating runtime state."""
    return _memory_cache


__all__ = [
    'cache_quote',
    'clear_quote_cache_for_test',
    'get_cached_quote',
    'memory_cache_for_legacy_tests',
]
