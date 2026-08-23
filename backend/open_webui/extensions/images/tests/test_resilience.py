from __future__ import annotations

import asyncio

import pytest
from open_webui.extensions.images import resilience


def test_fal_operation_is_not_wrapped_or_retried(monkeypatch) -> None:
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        raise TimeoutError('fal owns its queue timeout')

    with pytest.raises(TimeoutError):
        asyncio.run(resilience.run_image_operation('fal', operation))
    assert calls == 1


def test_non_fal_timeout_is_not_replayed_without_provider_idempotency() -> None:
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        raise TimeoutError('provider may already have accepted the request')

    with pytest.raises(TimeoutError, match='already have accepted'):
        asyncio.run(resilience.run_image_operation('openai', operation))
    assert calls == 1


def test_non_fal_timeout_follows_upstream_session_timeout(monkeypatch) -> None:
    """复盘 #10：非 FAL 硬超时与上游 AIOHTTP_CLIENT_TIMEOUT 会话级超时
    （默认 300s，可配置）一致，不再是硬编码 180s 砍掉慢速合法生成；
    上游配置为不设限时（None）时不额外加限。"""
    monkeypatch.setattr(resilience, 'AIOHTTP_CLIENT_TIMEOUT', 0.05)
    calls = 0

    async def slow_operation():
        nonlocal calls
        calls += 1
        await asyncio.sleep(1)

    with pytest.raises(TimeoutError):
        asyncio.run(resilience.run_image_operation('openai', slow_operation))
    assert calls == 1

    monkeypatch.setattr(resilience, 'AIOHTTP_CLIENT_TIMEOUT', None)

    async def unbounded_operation():
        await asyncio.sleep(0)
        return 'done'

    assert asyncio.run(resilience.run_image_operation('openai', unbounded_operation)) == 'done'
