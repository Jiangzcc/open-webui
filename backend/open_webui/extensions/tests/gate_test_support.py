import asyncio


def assert_rate_bucket(monkeypatch, limits, enforce, expected: str) -> None:
    captured: list[str] = []

    async def record_bucket(key: str) -> bool:
        captured.append(key)
        return False

    monkeypatch.setattr(limits._gate, '_is_limited', record_bucket)
    asyncio.run(enforce('user-1'))
    assert captured == [expected]


__all__ = ['assert_rate_bucket']
