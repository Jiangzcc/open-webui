from __future__ import annotations

import anyio
from fastapi import FastAPI
from open_webui.extensions.migration_kit import SchemaGuard, validate_schema

from . import models  # noqa: F401 - 副作用导入：确保派生 _REQUIRED_TABLES 前表已注册到 metadata
from .db import PromptTagBase
from .migrations.runner import SPEC, run_prompt_tag_migrations

_REQUIRED_TABLES = frozenset(table.name for table in PromptTagBase.metadata.sorted_tables)
_REQUIRED_UNIQUE = {
    'ext_prompt_tag_category': frozenset({'uq_ext_prompt_tag_category_slug'}),
    'ext_prompt_tag': frozenset({'uq_ext_prompt_tag_slug'}),
}
_REQUIRED_CHECKS = {
    'ext_prompt_tag_category': frozenset({'ck_ext_prompt_tag_category_sort_order'}),
    'ext_prompt_tag': frozenset({'ck_ext_prompt_tag_sort_order'}),
}
_REQUIRED_INDEXES = {
    'ext_prompt_tag_category': frozenset({'ix_ext_prompt_tag_category_visibility_order'}),
    'ext_prompt_tag': frozenset(
        {
            'ix_ext_prompt_tag_category_enabled_order',
            'ix_ext_prompt_tag_enabled_order',
        }
    ),
}

# 标签表必须恰好挂一条指向分类表的外键。
_SCHEMA_GUARD = SchemaGuard(
    spec=SPEC,
    required_tables=_REQUIRED_TABLES,
    required_unique=_REQUIRED_UNIQUE,
    required_checks=_REQUIRED_CHECKS,
    required_indexes=_REQUIRED_INDEXES,
    expected_foreign_keys={'ext_prompt_tag': frozenset({'ext_prompt_tag_category'})},
)


def _validate_prompt_tag_schema() -> None:
    validate_schema(_SCHEMA_GUARD)


async def initialize_prompt_tag_extension(_app: FastAPI) -> None:
    await anyio.to_thread.run_sync(run_prompt_tag_migrations)
    await anyio.to_thread.run_sync(_validate_prompt_tag_schema)


__all__ = ['initialize_prompt_tag_extension']
