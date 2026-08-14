from __future__ import annotations

import asyncio

import pytest
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.videos import limits


def test_per_user_concurrency_limit_and_release(monkeypatch) -> None:
    monkeypatch.setattr(limits, 'VIDEO_GENERATION_MAX_CONCURRENT_PER_USER', 1)
    limits._active_by_user.clear()

    async def scenario() -> None:
        await limits.acquire_video_generation_slot('user-1')
        with pytest.raises(CreditError) as raised:
            await limits.acquire_video_generation_slot('user-1')
        assert raised.value.code == 'rate_limited'
        assert raised.value.status_code == 429

        # Limits are isolated by user.
        await limits.acquire_video_generation_slot('user-2')
        await limits.release_video_generation_slot('user-1')
        # After release the slot is free again.
        await limits.acquire_video_generation_slot('user-1')
        await limits.release_video_generation_slot('user-1')
        await limits.release_video_generation_slot('user-2')

    asyncio.run(scenario())
    assert limits._active_by_user == {}


def test_request_rate_limit_returns_rate_limited_error(monkeypatch) -> None:
    monkeypatch.setattr(limits._request_limiter, 'is_limited', lambda _key: True)
    with pytest.raises(CreditError) as raised:
        limits.enforce_video_generation_rate('user-1')
    assert raised.value.code == 'rate_limited'
    assert raised.value.status_code == 429
    assert raised.value.context == {'reason': 'request_rate'}


def test_rate_limit_uses_video_bucket_not_image(monkeypatch) -> None:
    # 视频限流使用独立的 videos: 命名桶，不能与图片 images: 桶共享配额。
    captured: list[str] = []

    def fake_is_limited(key: str) -> bool:
        captured.append(key)
        return False

    monkeypatch.setattr(limits._request_limiter, 'is_limited', fake_is_limited)
    limits.enforce_video_generation_rate('user-1')
    assert captured == ['videos:generation:user-1']
