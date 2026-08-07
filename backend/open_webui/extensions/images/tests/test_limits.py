from __future__ import annotations

import asyncio

import pytest
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.images import limits


def test_per_user_concurrency_limit_and_release(monkeypatch) -> None:
    monkeypatch.setattr(limits, 'IMAGE_GENERATION_MAX_CONCURRENT_PER_USER', 2)
    limits._active_by_user.clear()

    async def scenario() -> None:
        await limits.acquire_image_generation_slot('user-1')
        await limits.acquire_image_generation_slot('user-1')
        with pytest.raises(CreditError) as raised:
            await limits.acquire_image_generation_slot('user-1')
        assert raised.value.code == 'rate_limited'

        # Limits are isolated by authenticated user ID.
        await limits.acquire_image_generation_slot('user-2')
        await limits.release_image_generation_slot('user-1')
        await limits.acquire_image_generation_slot('user-1')
        await limits.release_image_generation_slot('user-1')
        await limits.release_image_generation_slot('user-1')
        await limits.release_image_generation_slot('user-2')

    asyncio.run(scenario())
    assert limits._active_by_user == {}


def test_request_rate_limit_returns_public_rate_limited_error(monkeypatch) -> None:
    monkeypatch.setattr(limits._request_limiter, 'is_limited', lambda _key: True)
    with pytest.raises(CreditError) as raised:
        limits.enforce_image_generation_rate('user-1')
    assert raised.value.code == 'rate_limited'
    assert raised.value.status_code == 429
