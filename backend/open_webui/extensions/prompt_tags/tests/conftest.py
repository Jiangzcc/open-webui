from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest_asyncio
from open_webui.extensions.prompt_tags.db import PromptTagBase
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def prompt_tag_sessions(tmp_path: Path):
    database_path = tmp_path / 'prompt-tags.sqlite'
    engine = create_async_engine(f'sqlite+aiosqlite:///{database_path}')

    @event.listens_for(engine.sync_engine, 'connect')
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(PromptTagBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield sessions
    finally:
        await engine.dispose()


def make_user(
    user_id: str = 'admin-1',
    name: str = 'Admin',
    role: str = 'admin',
) -> SimpleNamespace:
    return SimpleNamespace(id=user_id, name=name, role=role)

