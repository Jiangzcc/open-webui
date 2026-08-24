"""Provider observer composition shared by new and recovered video runs."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from open_webui.extensions.provider_ops.service import DatabaseProviderInvocationObserver

ProviderSubmittedCallback = Callable[[dict[str, object]], Awaitable[None]]
ProviderResultCallback = Callable[[str], Awaitable[None]]


class VideoProviderObserver:
    def __init__(self, base: object | None, on_submitted: ProviderSubmittedCallback | None):
        self._base = base
        self._on_submitted = on_submitted

    async def _base_call(self, method: str, *args: object) -> None:
        if self._base is not None:
            await getattr(self._base, method)(*args)

    async def submitted(self, payload: dict[str, object]) -> None:
        # Persist Provider Ops first: it is the recovery fallback when the
        # task-specific callback cannot write its snapshot.
        await self._base_call('submitted', payload)
        if self._on_submitted is not None:
            await self._on_submitted(payload)

    async def status(self, payload: dict[str, object]) -> None:
        await self._base_call('status', payload)

    async def succeeded(self) -> None:
        await self._base_call('succeeded')

    async def failed(self, error: BaseException) -> None:
        await self._base_call('failed', error)


async def record_provider_result_url(
    observer: DatabaseProviderInvocationObserver | None,
    callback: ProviderResultCallback | None,
    result_url: str,
) -> None:
    if observer is not None:
        await observer.result_available(result_url)
    if callback is not None:
        await callback(result_url)


@dataclass
class ResumeContext:
    observer: DatabaseProviderInvocationObserver | None = None
    terminal_notified: bool = False


async def mark_observer_failed_if_pending(
    observer: DatabaseProviderInvocationObserver | None,
    error: BaseException,
    *,
    terminal_notified: bool,
) -> None:
    if observer is None or terminal_notified:
        return
    try:
        await observer.failed(error)
    except Exception:
        # Provider Ops diagnostics remain best-effort during recovery errors.
        pass


__all__ = [
    'ProviderResultCallback',
    'ProviderSubmittedCallback',
    'ResumeContext',
    'VideoProviderObserver',
    'mark_observer_failed_if_pending',
    'record_provider_result_url',
]
