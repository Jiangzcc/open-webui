from __future__ import annotations

from open_webui.env import DATABASE_SCHEMA
from open_webui.internal.db import JSONField, engine, get_async_db
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

ModelOpsBase = declarative_base(metadata=MetaData(schema=DATABASE_SCHEMA))

# 复盘 P2：四份二开 db.py 的 session helper 与上游 get_async_db 逐字重复——委托上游工厂。
model_ops_session = get_async_db

__all__ = ['JSONField', 'ModelOpsBase', 'engine', 'model_ops_session']
