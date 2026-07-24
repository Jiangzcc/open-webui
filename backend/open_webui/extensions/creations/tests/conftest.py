from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import pytest_asyncio
from open_webui.extensions.creations.db import CreationBase
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
def sqlite_database(tmp_path: Path):
    database_path = tmp_path / 'creations.sqlite'
    engine = create_engine(f'sqlite:///{database_path}')
    try:
        yield engine, database_path
    finally:
        engine.dispose()


@pytest_asyncio.fixture
async def creation_sessions(tmp_path: Path):
    database_path = tmp_path / 'creations.sqlite'
    engine = create_async_engine(f'sqlite+aiosqlite:///{database_path}')
    async with engine.begin() as connection:
        await connection.run_sync(CreationBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield sessions
    finally:
        await engine.dispose()


def make_file(file_id: str, user_id: str, content_type: str = 'image/png', created_at: int = 100) -> SimpleNamespace:
    return SimpleNamespace(
        id=file_id,
        user_id=user_id,
        created_at=created_at,
        meta={'content_type': content_type, 'size': 1234},
    )


def make_user(
    user_id: str,
    name: str | None = 'Some User',
    email: str | None = 'someone@example.com',
    role: str = 'user',
) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        name=name,
        email=email,
        role=role,
        profile_image_url='/avatar.png',
    )
