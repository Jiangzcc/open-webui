from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest_asyncio
from open_webui.extensions.model_ops.db import ModelOpsBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def model_ops_sessions(tmp_path: Path):
    """为服务层测试提供基于临时 SQLite 文件的异步会话工厂。

    使用独立引擎和 ModelOpsBase 元数据创建表，避免依赖真实数据库连接。
    """
    database_path = tmp_path / 'model-ops.sqlite'
    engine = create_async_engine(f'sqlite+aiosqlite:///{database_path}')
    async with engine.begin() as connection:
        await connection.run_sync(ModelOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield sessions
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def router_database(tmp_path: Path):
    """为路由层测试提供基于临时 SQLite 文件的异步会话工厂。"""
    database_path = tmp_path / 'router.sqlite'
    engine = create_async_engine(f'sqlite+aiosqlite:///{database_path}')
    async with engine.begin() as connection:
        await connection.run_sync(ModelOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield sessions
    finally:
        await engine.dispose()


def make_user(
    user_id: str = 'admin-1',
    name: str = 'Admin',
    email: str = 'admin@example.test',
    role: str = 'admin',
) -> SimpleNamespace:
    """构造模拟用户对象，用于路由层鉴权覆盖或服务层 operator 参数。"""
    return SimpleNamespace(
        id=user_id,
        name=name,
        email=email,
        role=role,
        profile_image_url='/avatar.png',
    )
