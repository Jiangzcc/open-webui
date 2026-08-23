from __future__ import annotations

import pytest
from open_webui.extensions.credits import quote_cache
from open_webui.extensions.credits.constants import CREDIT_QUOTE_CACHE_TTL_SECONDS


@pytest.fixture(autouse=True)
def clean_cache():
    quote_cache.memory_cache().clear()
    yield
    quote_cache.memory_cache().clear()


@pytest.mark.asyncio
async def test_cache_stores_and_reads_within_ttl() -> None:
    cache_key = ('user-1', 'price-a', 'text-to-image:abc', 1)
    response = {
        'balance': 100,
        'sufficient': True,
        'configured': True,
        'factors': [],
        'charged_credits': 5,
        'error': None,
    }
    await quote_cache.cache_quote(cache_key, response, now=100.0)

    cached = await quote_cache.get_cached_quote(cache_key, balance=80, now=100.5)
    assert cached is not None
    # balance/sufficient 不应被缓存，应反映传入的实时余额。
    assert cached['balance'] == 80
    assert cached['sufficient'] is True
    assert cached['charged_credits'] == 5


@pytest.mark.asyncio
async def test_cache_expires_after_ttl() -> None:
    cache_key = ('user-1', 'price-a', 'text-to-image:abc', 1)
    await quote_cache.cache_quote(cache_key, {'charged_credits': 5, 'balance': 100}, now=100.0)

    # TTL 边界：刚好过期时返回 None。
    expired = await quote_cache.get_cached_quote(
        cache_key,
        balance=100,
        now=100.0 + CREDIT_QUOTE_CACHE_TTL_SECONDS + 0.01,
    )
    assert expired is None


@pytest.mark.asyncio
async def test_cache_bounded_eviction(monkeypatch) -> None:
    monkeypatch.setattr(quote_cache, 'CREDIT_QUOTE_CACHE_MAX_ENTRIES', 2)

    await quote_cache.cache_quote(('u', 'p1', 'a:1', 1), {'charged_credits': 1}, now=1.0)
    await quote_cache.cache_quote(('u', 'p2', 'a:2', 1), {'charged_credits': 2}, now=2.0)
    # 第三条应驱逐最旧的（now=1.0 的 p1）。
    await quote_cache.cache_quote(('u', 'p3', 'a:3', 1), {'charged_credits': 3}, now=3.0)

    assert await quote_cache.get_cached_quote(('u', 'p1', 'a:1', 1), 0, 3.0) is None
    assert await quote_cache.get_cached_quote(('u', 'p3', 'a:3', 1), 0, 3.0) is not None
