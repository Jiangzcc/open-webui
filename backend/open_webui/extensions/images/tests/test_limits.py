from __future__ import annotations

import asyncio

from open_webui.extensions.images import limits


def test_rate_check_uses_image_bucket(monkeypatch) -> None:
    # 图片限流使用独立的 images: 命名桶，不能与视频 videos: 桶共享配额。
    captured: list[str] = []

    async def fake_is_limited(key: str) -> bool:
        captured.append(key)
        return False

    monkeypatch.setattr(limits._gate, '_is_limited', fake_is_limited)
    asyncio.run(limits.enforce_image_generation_rate('user-1'))
    assert captured == ['images:generation:user-1']


def test_rate_check_over_limit_raises_credit_error(monkeypatch) -> None:
    async def always_limited(_key: str) -> bool:
        return True

    monkeypatch.setattr(limits._gate, '_is_limited', always_limited)
    try:
        asyncio.run(limits.enforce_image_generation_rate('user-1'))
    except Exception as error:  # noqa: BLE001
        assert error.code == 'rate_limited'  # type: ignore[attr-defined]
        assert error.context == {'reason': 'request_rate'}  # type: ignore[attr-defined]
    else:
        raise AssertionError('over-limit request must raise CreditError')


def test_module_exports_delegate_to_gate() -> None:
    assert limits._gate._bucket_prefix == 'images:generation'
    assert limits.acquire_image_generation_slot == limits._gate.acquire_slot
    assert limits.release_image_generation_slot == limits._gate.release_slot
    assert limits.enforce_image_generation_rate == limits._gate.enforce_rate
