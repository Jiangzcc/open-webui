from __future__ import annotations

import anyio
from fastapi import FastAPI
from open_webui.extensions.migration_kit import SchemaGuard, validate_schema

from .migrations.runner import SPEC, run_model_ops_migrations

_SCHEMA_GUARD = SchemaGuard(
    spec=SPEC,
    required_tables=frozenset({'ext_image_model_operation'}),
    required_checks={'ext_image_model_operation': frozenset({'ck_ext_image_model_operation_sort_order'})},
)


def _validate_model_ops_schema() -> None:
    validate_schema(_SCHEMA_GUARD)


async def initialize_model_ops_extension(_app: FastAPI) -> None:
    await anyio.to_thread.run_sync(run_model_ops_migrations)
    await anyio.to_thread.run_sync(_validate_model_ops_schema)


__all__ = ['initialize_model_ops_extension']
