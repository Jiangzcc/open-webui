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
