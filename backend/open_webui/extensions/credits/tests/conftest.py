from pathlib import Path

import pytest
import pytest_asyncio
from open_webui.extensions.credits.db import CreditBase
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def router_database(tmp_path: Path):
    database_path = tmp_path / 'router.sqlite'
    engine = create_async_engine(f'sqlite+aiosqlite:///{database_path}')
    async with engine.begin() as connection:
        await connection.run_sync(CreditBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield sessions
    finally:
        await engine.dispose()


@pytest.fixture
def sqlite_database(tmp_path: Path):
    database_path = tmp_path / 'credits.sqlite'
    engine = create_engine(f'sqlite:///{database_path}')
    try:
        yield engine, database_path
    finally:
        engine.dispose()
