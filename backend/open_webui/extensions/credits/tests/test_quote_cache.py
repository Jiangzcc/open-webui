from __future__ import annotations

from open_webui.extensions.credits import quote_cache
from open_webui.extensions.credits.constants import CREDIT_QUOTE_CACHE_TTL_SECONDS


def test_memory_fallback_stores_and_reads_within_ttl(monkeypatch) -> None:
    # 强制走进程内降级路径（Redis 不可用时）。
    monkeypatch.setattr(quote_cache, '_sync_redis', None)
    quote_cache.clear_quote_cache_for_test()

    cache_key = ('user-1', 'price-a', 'text-to-image:abc', 1)
    response = {
        'balance': 100,
        'sufficient': True,
        'configured': True,
        'factors': [],
        'charged_credits': 5,
        'error': None,
    }
    quote_cache.cache_quote(cache_key, response, now=100.0)

    cached = quote_cache.get_cached_quote(cache_key, balance=80, now=100.5)
    assert cached is not None
    # balance/sufficient 不应被缓存，应反映传入的实时余额。
    assert cached['balance'] == 80
    assert cached['sufficient'] is True
    assert cached['charged_credits'] == 5


def test_memory_fallback_expires_after_ttl(monkeypatch) -> None:
    monkeypatch.setattr(quote_cache, '_sync_redis', None)
    quote_cache.clear_quote_cache_for_test()

    cache_key = ('user-1', 'price-a', 'text-to-image:abc', 1)
    quote_cache.cache_quote(cache_key, {'charged_credits': 5, 'balance': 100}, now=100.0)

    # TTL 边界：刚好过期时返回 None。
    expired = quote_cache.get_cached_quote(cache_key, balance=100, now=100.0 + CREDIT_QUOTE_CACHE_TTL_SECONDS + 0.01)
    assert expired is None


def test_memory_fallback_bounded_eviction(monkeypatch) -> None:
    monkeypatch.setattr(quote_cache, '_sync_redis', None)
    quote_cache.clear_quote_cache_for_test()
    monkeypatch.setattr(quote_cache, 'CREDIT_QUOTE_CACHE_MAX_ENTRIES', 2)

    quote_cache.cache_quote(('u', 'p1', 'a:1', 1), {'charged_credits': 1}, now=1.0)
    quote_cache.cache_quote(('u', 'p2', 'a:2', 1), {'charged_credits': 2}, now=2.0)
    # 第三条应驱逐最旧的（now=1.0 的 p1）。
    quote_cache.cache_quote(('u', 'p3', 'a:3', 1), {'charged_credits': 3}, now=3.0)

    assert quote_cache.get_cached_quote(('u', 'p1', 'a:1', 1), 0, 3.0) is None
    assert quote_cache.get_cached_quote(('u', 'p3', 'a:3', 1), 0, 3.0) is not None


class _FakeRedis:
    """模拟 Redis 客户端：内存 dict + setex 语义。"""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def setex(self, key: str, ttl: int, value: str) -> None:
        self.store[key] = value
        self._ttl[key] = ttl

    _ttl: dict[str, int] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)


def test_redis_path_round_trips_through_json(monkeypatch) -> None:
    # 模拟 Redis 可用：验证缓存值经 JSON 序列化往返后仍可还原。
    fake = _FakeRedis()
    monkeypatch.setattr(quote_cache, '_sync_redis', fake)
    quote_cache.clear_quote_cache_for_test()

    cache_key = ('user-1', 'price-a', 'text-to-image:abc', 1)
    response = {
        'balance': 100,
        'sufficient': True,
        'charged_credits': 7,
        'configured': True,
        'factors': [],
        'error': None,
    }
    quote_cache.cache_quote(cache_key, response, now=200.0)

    # Redis key 应被写入。
    assert any('webui:credits:quote:' in k for k in fake.store)
    cached = quote_cache.get_cached_quote(cache_key, balance=50, now=200.5)
    assert cached is not None
    assert cached['balance'] == 50  # 实时余额覆写
    assert cached['sufficient'] is True
    assert cached['charged_credits'] == 7  # 缓存的计费值保留


def test_redis_miss_does_not_return_worker_local_value(monkeypatch) -> None:
    fake = _FakeRedis()
    monkeypatch.setattr(quote_cache, '_sync_redis', fake)
    quote_cache.clear_quote_cache_for_test()

    cache_key = ('user-1', 'price-a', 'text-to-image:abc', 1)
    quote_cache._memory_cache[cache_key] = (999.0, {'charged_credits': 99})

    assert quote_cache.get_cached_quote(cache_key, balance=100, now=200.0) is None


def test_redis_key_encodes_ambiguous_segments_without_collision() -> None:
    first = quote_cache._redis_key(('user:a', 'price', 'action:hash', 1))
    second = quote_cache._redis_key(('user', 'a:price', 'action:hash', 1))

    assert first != second
    assert first.startswith('webui:credits:quote:')


def test_redis_unavailable_falls_back_to_memory_silently(monkeypatch) -> None:
    # Redis 抛异常时应降级到内存，不抛错。
    class _BrokenRedis:
        def get(self, *_a, **_kw):
            raise RuntimeError('redis down')

        def setex(self, *_a, **_kw):
            raise RuntimeError('redis down')

    monkeypatch.setattr(quote_cache, '_sync_redis', _BrokenRedis())
    quote_cache.clear_quote_cache_for_test()

    cache_key = ('user-1', 'price-a', 'text-to-image:abc', 1)
    # 写应走内存降级（setex 抛异常被吞）。
    quote_cache.cache_quote(cache_key, {'charged_credits': 9, 'balance': 100}, now=300.0)
    # 读也应降级到内存（get 抛异常被吞，None 后查内存）。
    cached = quote_cache.get_cached_quote(cache_key, balance=100, now=300.5)
    assert cached is not None
    assert cached['charged_credits'] == 9
