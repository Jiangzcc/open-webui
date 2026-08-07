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


def test_non_fal_timeout_retries_then_returns(monkeypatch) -> None:
    monkeypatch.setattr(resilience, 'NON_FAL_IMAGE_RETRY_BASE_SECONDS', 0)
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError('temporary timeout')
        return 'ok'

    assert asyncio.run(resilience.run_image_operation('openai', operation)) == 'ok'
    assert calls == 2


def test_non_fal_timeout_stops_after_finite_attempts(monkeypatch) -> None:
    monkeypatch.setattr(resilience, 'NON_FAL_IMAGE_RETRY_BASE_SECONDS', 0)
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        raise TimeoutError('still unavailable')

    with pytest.raises(TimeoutError):
        asyncio.run(resilience.run_image_operation('gemini', operation))
    assert calls == resilience.NON_FAL_IMAGE_MAX_ATTEMPTS
