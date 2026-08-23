from __future__ import annotations

import asyncio

from open_webui.extensions.videos import limits


def test_rate_limit_uses_video_bucket_not_image(monkeypatch) -> None:
    # 视频限流使用独立的 videos: 命名桶，不能与图片 images: 桶共享配额。
    captured: list[str] = []

    async def fake_is_limited(key: str) -> bool:
        captured.append(key)
        return False

    monkeypatch.setattr(limits._gate, '_is_limited', fake_is_limited)
    asyncio.run(limits.enforce_video_generation_rate('user-1'))
    assert captured == ['videos:generation:user-1']


def test_module_exports_delegate_to_gate() -> None:
    assert limits._gate._bucket_prefix == 'videos:generation'
    assert limits._gate._max_concurrent_per_user == limits.VIDEO_GENERATION_MAX_CONCURRENT_PER_USER
    assert limits.acquire_video_generation_slot == limits._gate.acquire_slot
    assert limits.release_video_generation_slot == limits._gate.release_slot
    assert limits.enforce_video_generation_rate == limits._gate.enforce_rate
