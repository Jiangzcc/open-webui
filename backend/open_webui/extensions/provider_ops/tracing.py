from __future__ import annotations

from typing import Protocol


class ProviderInvocationObserver(Protocol):
    async def submitted(self, payload: dict[str, object]) -> None: ...

    async def status(self, payload: dict[str, object]) -> None: ...

    async def succeeded(self) -> None: ...

    async def failed(self, error: BaseException) -> None: ...


__all__ = ['ProviderInvocationObserver']
