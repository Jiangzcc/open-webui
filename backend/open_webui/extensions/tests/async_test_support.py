import asyncio
from types import SimpleNamespace


class AsyncContext:
    def __init__(self, value=None) -> None:
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *_args) -> None:
        return None


class TransactionalSession(SimpleNamespace):
    def begin(self):
        return AsyncContext()


class SelfTransactionalContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    def begin(self):
        return self


async def wait_until_cancelled(started: asyncio.Event) -> None:
    started.set()
    await asyncio.Event().wait()


__all__ = [
    'AsyncContext',
    'SelfTransactionalContext',
    'TransactionalSession',
    'wait_until_cancelled',
]
