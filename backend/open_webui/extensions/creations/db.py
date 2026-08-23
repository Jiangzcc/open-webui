from __future__ import annotations

from open_webui.env import DATABASE_SCHEMA
from open_webui.internal.db import engine, get_async_db, get_async_session
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

CreationBase = declarative_base(metadata=MetaData(schema=DATABASE_SCHEMA))

# 复盘 P2：四份二开 db.py 的 session helper 与上游 get_async_db/get_async_session
# 逐字重复——改为委托上游工厂，语义随上游升级自动跟随。
creation_session = get_async_db
get_creation_session = get_async_session

__all__ = ['CreationBase', 'creation_session', 'engine', 'get_creation_session']
