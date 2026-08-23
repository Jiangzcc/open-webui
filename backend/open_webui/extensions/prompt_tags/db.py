from __future__ import annotations

from open_webui.env import DATABASE_SCHEMA
from open_webui.internal.db import JSONField, engine
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

PromptTagBase = declarative_base(metadata=MetaData(schema=DATABASE_SCHEMA))

__all__ = ['JSONField', 'PromptTagBase', 'engine']
