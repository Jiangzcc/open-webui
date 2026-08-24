from __future__ import annotations

import asyncio
import time

import pytest
from open_webui.extensions import generation_gate
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.generation_gate import GenerationGate


def _gate(max_concurrent: int = 2, limit: int = 10) -> GenerationGate:
    return GenerationGate(
        bucket_prefix='test:generation',
        limit=limit,
        window_seconds=60,
        max_concurrent_per_user=max_concurrent,
    )


async def _assert_third_rate_limited(gate: GenerationGate) -> None:
    await gate.enforce_rate('user-1')
    await gate.enforce_rate('user-1')
    with pytest.raises(CreditError):
        await gate.enforce_rate('user-1')


class _FakeAsyncRedis:
    """redis.asyncio 客户端替身：记录命令并按预设返回。"""

    def __init__(
        self,
        *,
        incr_error: Exception | None = None,
        incr_delay: float = 0.0,
        mget_counts: list[int] | None = None,
    ) -> None:
        self.incr_keys: list[str] = []
        self.expire_calls: list[tuple[str, int]] = []
        self.mget_keys: list[list[str]] = []
        self._incr_error = incr_error
        self._incr_delay = incr_delay
        self._mget_counts = mget_counts if mget_counts is not None else [0]

    async def incr(self, key: str) -> int:
        if self._incr_error is not None:
            raise self._incr_error
        if self._incr_delay:
            await asyncio.sleep(self._incr_delay)
        self.incr_keys.append(key)
        # 返回递增计数：真实 Redis 只有首次 incr 返回 1（触发 expire 分支）。
        return len(self.incr_keys)

    async def expire(self, key: str, ttl: int) -> bool:
        self.expire_calls.append((key, ttl))
        return True

    async def mget(self, keys: list[str]) -> list[int]:
        self.mget_keys.append(list(keys))
        return list(self._mget_counts)


def test_concurrency_slots_limit_release_and_user_isolation() -> None:
    gate = _gate(max_concurrent=2)

    async def scenario() -> None:
        await gate.acquire_slot('user-1')
        await gate.acquire_slot('user-1')
        with pytest.raises(CreditError) as raised:
            await gate.acquire_slot('user-1')
        assert raised.value.code == 'rate_limited'
        assert raised.value.context == {'reason': 'concurrency'}

        # 槽位按用户隔离，user-2 不受 user-1 占满影响。
        await gate.acquire_slot('user-2')
        await gate.release_slot('user-1')
        await gate.acquire_slot('user-1')
        await gate.release_slot('user-1')
        await gate.release_slot('user-1')
        await gate.release_slot('user-2')

    asyncio.run(scenario())
    assert gate._active_by_user == {}


def test_release_below_floor_is_idempotent() -> None:
    gate = _gate()

    async def scenario() -> None:
        await gate.release_slot('user-1')
        await gate.release_slot('user-1')

    asyncio.run(scenario())
    assert gate._active_by_user == {}


def test_rate_check_uses_prefixed_bucket(monkeypatch) -> None:
    gate = _gate()
    captured: list[str] = []

    async def fake_is_limited(key: str) -> bool:
        captured.append(key)
        return key.endswith('limited-user')

    monkeypatch.setattr(gate, '_is_limited', fake_is_limited)

    asyncio.run(gate.enforce_rate('user-1'))
    assert captured == ['test:generation:user-1']

    with pytest.raises(CreditError) as raised:
        asyncio.run(gate.enforce_rate('limited-user'))
    assert raised.value.code == 'rate_limited'
    assert raised.value.context == {'reason': 'request_rate'}
    assert raised.value.status_code == 429


def test_gate_constructs_async_redis_client(monkeypatch) -> None:
    """复盘 P1：GenerationGate 必须请求 redis.asyncio 客户端——同步客户端
    会在事件循环线程内执行阻塞网络 I/O，单 worker 部署下卡死全部请求。"""
    captured: list[bool] = []

    def fake_get_client(async_mode: bool = False):  # type: ignore[no-untyped-def]
        captured.append(async_mode)
        return None

    monkeypatch.setattr(generation_gate, 'get_redis_client', fake_get_client)
    _gate()
    assert captured == [True]


def test_rate_check_redis_path_counts_window_buckets(monkeypatch) -> None:
    """Redis 正常路径：incr 当前桶 + expire + mget 覆盖窗口内全部桶。"""
    gate = _gate(limit=10)
    redis = _FakeAsyncRedis(mget_counts=[3])
    monkeypatch.setattr(gate, '_redis', redis)

    async def scenario() -> None:
        # 窗口计数 3 ≤ limit 10 → 放行；再次提交计数 4 仍放行。
        await gate.enforce_rate('user-1')
        await gate.enforce_rate('user-1')

    asyncio.run(scenario())

    now_bucket = int(time.time()) // generation_gate._BUCKET_SIZE_SECONDS
    expected_key = generation_gate.GenerationGate._bucket_key('test:generation:user-1', now_bucket)
    assert redis.incr_keys == [expected_key, expected_key]
    # 仅首次 incr 需要设置过期（attempt==1 分支）。
    assert redis.expire_calls == [(expected_key, 60 + generation_gate._BUCKET_SIZE_SECONDS)]
    # mget 覆盖 window/bucket_size + 1 个桶（60/10 + 1 = 7）。
    assert all(len(keys) == 7 for keys in redis.mget_keys)
    assert len(redis.mget_keys) == 2


def test_rate_check_redis_over_limit_raises(monkeypatch) -> None:
    gate = _gate(limit=2)
    redis = _FakeAsyncRedis(mget_counts=[2, 1])
    monkeypatch.setattr(gate, '_redis', redis)

    with pytest.raises(CreditError) as raised:
        asyncio.run(gate.enforce_rate('user-1'))
    assert raised.value.code == 'rate_limited'
    assert raised.value.context == {'reason': 'request_rate'}


def test_rate_check_redis_error_falls_back_to_memory(monkeypatch) -> None:
    """Redis 故障（如连接拒绝）不得让请求失败：回退进程内内存限流。"""
    gate = _gate(limit=2)
    redis = _FakeAsyncRedis(incr_error=ConnectionError('redis down'))
    monkeypatch.setattr(gate, '_redis', redis)
    fallback_calls: list[str] = []

    def fake_fallback(key: str) -> bool:
        fallback_calls.append(key)
        return fallback_calls.count(key) > 2

    monkeypatch.setattr(gate._fallback_limiter, 'is_limited', fake_fallback)

    asyncio.run(_assert_third_rate_limited(gate))
    assert len(fallback_calls) == 3


def test_rate_check_slow_redis_times_out_to_memory(monkeypatch) -> None:
    """Redis 挂起（未配置 socket_timeout 时默认无限等待）：检查必须限时回退。"""
    gate = _gate(limit=10)
    redis = _FakeAsyncRedis(incr_delay=0.5)
    monkeypatch.setattr(gate, '_redis', redis)
    monkeypatch.setattr(generation_gate, '_REDIS_CHECK_TIMEOUT_SECONDS', 0.05)
    fallback_calls: list[str] = []

    def fake_fallback(key: str) -> bool:
        fallback_calls.append(key)
        return False

    monkeypatch.setattr(gate._fallback_limiter, 'is_limited', fake_fallback)

    asyncio.run(gate.enforce_rate('user-1'))
    assert fallback_calls == ['test:generation:user-1']


def test_rate_check_without_redis_uses_memory_limiter(monkeypatch) -> None:
    """未配置 Redis：直接走上游 RateLimiter 的内存模式，限流语义不变。"""
    gate = _gate(limit=2)
    monkeypatch.setattr(gate, '_redis', None)

    asyncio.run(_assert_third_rate_limited(gate))
