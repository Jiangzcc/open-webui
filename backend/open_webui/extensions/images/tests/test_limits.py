from __future__ import annotations

from open_webui.extensions.images import limits


def test_rate_check_uses_image_bucket(monkeypatch) -> None:
    # 图片限流使用独立的 images: 命名桶，不能与视频 videos: 桶共享配额。
    captured: list[str] = []

    def fake_is_limited(key: str) -> bool:
        captured.append(key)
        return False

    monkeypatch.setattr(limits._gate._limiter, 'is_limited', fake_is_limited)
    limits.enforce_image_generation_rate('user-1')
    assert captured == ['images:generation:user-1']


def test_module_exports_delegate_to_gate() -> None:
    assert limits._gate._bucket_prefix == 'images:generation'
    assert limits.acquire_image_generation_slot == limits._gate.acquire_slot
    assert limits.release_image_generation_slot == limits._gate.release_slot
    assert limits.enforce_image_generation_rate == limits._gate.enforce_rate
