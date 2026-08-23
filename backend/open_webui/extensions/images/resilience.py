from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from open_webui.env import AIOHTTP_CLIENT_TIMEOUT

T = TypeVar('T')


async def run_image_operation(
    engine: str,
    operation: Callable[[], Awaitable[T]],
) -> T:
    """Bound non-fal image calls without replaying a possibly accepted request.

    These providers do not expose a shared idempotency contract here. A timeout
    or connection error can happen after the provider accepted the request, so
    automatically replaying it risks duplicate generation and duplicate cost.

    复盘 #10：硬超时与上游会话级超时（AIOHTTP_CLIENT_TIMEOUT，默认 300s，
    可配置）保持一致；原先硬编码 180s 会砍掉上游本可完成的慢速生成
    （如 A1111 高步数）。上游配置为不设限时这里也不额外加限。
    """
    if engine == 'fal':
        return await operation()
    if AIOHTTP_CLIENT_TIMEOUT is None:
        return await operation()
    async with asyncio.timeout(AIOHTTP_CLIENT_TIMEOUT):
        return await operation()


__all__ = ['run_image_operation']
