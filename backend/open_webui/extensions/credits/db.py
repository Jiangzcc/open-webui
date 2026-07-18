from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from open_webui.env import DATABASE_SCHEMA
from open_webui.internal.db import AsyncSessionLocal, JSONField, async_engine, engine
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

CreditBase = declarative_base(metadata=MetaData(schema=DATABASE_SCHEMA))


@asynccontextmanager
async def credit_session() -> AsyncIterator[AsyncSession]:
    """Provide a credit transaction session from the upstream async factory."""
    async with AsyncSessionLocal() as session:
        yield session


__all__ = [
    'AsyncSessionLocal',
    'CreditBase',
    'JSONField',
    'async_engine',
    'credit_session',
    'engine',
]
