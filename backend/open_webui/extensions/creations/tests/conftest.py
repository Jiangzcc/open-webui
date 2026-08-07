from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import pytest_asyncio
from open_webui.extensions.creations.db import CreationBase
from open_webui.extensions.creations.models import DiscoveryCategorySetting
from open_webui.extensions.credits.models import CreditUsage
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
        # Generation-task deletion keeps legacy usage-backed batch IDs compatible.
        await connection.run_sync(CreditUsage.__table__.create)
        await connection.execute(
            DiscoveryCategorySetting.__table__.insert(),
            [
                {'id': 'portrait', 'display_name': '人像', 'enabled': True, 'sort_order': 10, 'updated_at': 0},
                {'id': 'product', 'display_name': '商品', 'enabled': True, 'sort_order': 20, 'updated_at': 0},
                {'id': 'poster', 'display_name': '海报', 'enabled': True, 'sort_order': 30, 'updated_at': 0},
                {'id': 'illustration', 'display_name': '插画', 'enabled': True, 'sort_order': 40, 'updated_at': 0},
                {'id': 'anime', 'display_name': '动漫', 'enabled': True, 'sort_order': 50, 'updated_at': 0},
                {'id': 'landscape', 'display_name': '风景', 'enabled': True, 'sort_order': 60, 'updated_at': 0},
                {'id': 'other', 'display_name': '其他', 'enabled': True, 'sort_order': 999, 'updated_at': 0},
            ],
        )
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
