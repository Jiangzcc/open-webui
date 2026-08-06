from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from open_webui.env import DATABASE_SCHEMA
from open_webui.internal.db import AsyncSessionLocal, JSONField, engine
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

ModelOpsBase = declarative_base(metadata=MetaData(schema=DATABASE_SCHEMA))


@asynccontextmanager
async def model_ops_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


__all__ = ['JSONField', 'ModelOpsBase', 'engine', 'model_ops_session']
