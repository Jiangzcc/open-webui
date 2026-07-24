from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from open_webui.env import DATABASE_SCHEMA
from open_webui.internal.db import AsyncSessionLocal, JSONField, async_engine, engine
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

CreationBase = declarative_base(metadata=MetaData(schema=DATABASE_SCHEMA))


@asynccontextmanager
async def creation_session() -> AsyncIterator[AsyncSession]:
    """Provide a creation transaction session from the upstream async factory."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_creation_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a creation session bound to the upstream factory."""
    async with AsyncSessionLocal() as session:
        yield session


__all__ = [
    'AsyncSessionLocal',
    'CreationBase',
    'JSONField',
    'async_engine',
    'creation_session',
    'engine',
    'get_creation_session',
]
