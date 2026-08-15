from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar('T')

NON_FAL_IMAGE_TIMEOUT_SECONDS = 180


async def run_image_operation(
    engine: str,
    operation: Callable[[], Awaitable[T]],
) -> T:
    """Bound non-fal image calls without replaying a possibly accepted request.

    These providers do not expose a shared idempotency contract here. A timeout
    or connection error can happen after the provider accepted the request, so
    automatically replaying it risks duplicate generation and duplicate cost.
    """
    if engine == 'fal':
        return await operation()

    async with asyncio.timeout(NON_FAL_IMAGE_TIMEOUT_SECONDS):
        return await operation()


__all__ = ['run_image_operation']
