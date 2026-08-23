from __future__ import annotations

import asyncio

import pytest
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.generation_gate import GenerationGate


def _gate(max_concurrent: int = 2) -> GenerationGate:
    return GenerationGate(
        bucket_prefix='test:generation',
        limit=10,
        window_seconds=60,
        max_concurrent_per_user=max_concurrent,
    )


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

    def fake_is_limited(key: str) -> bool:
        captured.append(key)
        return key.endswith('limited-user')

    monkeypatch.setattr(gate._limiter, 'is_limited', fake_is_limited)

    gate.enforce_rate('user-1')
    assert captured == ['test:generation:user-1']

    with pytest.raises(CreditError) as raised:
        gate.enforce_rate('limited-user')
    assert raised.value.code == 'rate_limited'
    assert raised.value.context == {'reason': 'request_rate'}
    assert raised.value.status_code == 429
