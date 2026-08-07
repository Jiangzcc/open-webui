from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

import aiohttp

T = TypeVar('T')

NON_FAL_IMAGE_TIMEOUT_SECONDS = 180
NON_FAL_IMAGE_MAX_ATTEMPTS = 2
NON_FAL_IMAGE_RETRY_BASE_SECONDS = 0.5

_RETRYABLE_ERRORS = (
    TimeoutError,
    aiohttp.ClientConnectionError,
    aiohttp.ServerTimeoutError,
)


async def run_image_operation(
    engine: str,
    operation: Callable[[], Awaitable[T]],
) -> T:
    """Bound non-fal image calls and retry only transient transport failures."""
    if engine == 'fal':
        return await operation()

    for attempt in range(NON_FAL_IMAGE_MAX_ATTEMPTS):
        try:
            async with asyncio.timeout(NON_FAL_IMAGE_TIMEOUT_SECONDS):
                return await operation()
        except _RETRYABLE_ERRORS:
            if attempt + 1 >= NON_FAL_IMAGE_MAX_ATTEMPTS:
                raise
            await asyncio.sleep(NON_FAL_IMAGE_RETRY_BASE_SECONDS * (2**attempt))

    raise RuntimeError('unreachable image retry state')


__all__ = ['run_image_operation']
