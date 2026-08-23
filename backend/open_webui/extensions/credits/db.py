from __future__ import annotations

from open_webui.env import DATABASE_SCHEMA
from open_webui.internal.db import engine, get_async_db
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

CreditBase = declarative_base(metadata=MetaData(schema=DATABASE_SCHEMA))

# 复盘 P2：四份二开 db.py 的 session helper 与上游 get_async_db 逐字重复——委托上游工厂。
credit_session = get_async_db

__all__ = ['CreditBase', 'credit_session', 'engine']
