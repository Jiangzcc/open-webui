from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field

from alembic.migration import MigrationContext
from open_webui.env import DATABASE_SCHEMA
from sqlalchemy import inspect

from .runner import script_heads
from .spec import MigrationSpec

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SchemaGuard:
    """Declarative post-migration schema validation for one extension chain.

    迁移跑完后由 ``validate_schema`` 依据本声明核对库内对象，替代此前每个
    extension/registration.py 里近乎相同的手写校验循环（复盘：注册表收敛）。

    - ``required_tables``：必须存在的表。
    - ``required_unique`` / ``required_checks`` / ``required_indexes``：按表
      列出必须存在的唯一约束 / CHECK / 索引名。
    - ``expected_foreign_keys``：None 表示不校验 FK；空映射表示所有
      required_tables 都不得声明 FK；非空映射则要求每张表的 FK 引用表
      集合与映射精确一致（未列出的表视为不允许 FK）。
    """

    spec: MigrationSpec
    required_tables: frozenset[str] = frozenset()
    required_unique: Mapping[str, frozenset[str]] = field(default_factory=dict)
    required_checks: Mapping[str, frozenset[str]] = field(default_factory=dict)
    required_indexes: Mapping[str, frozenset[str]] = field(default_factory=dict)
    expected_foreign_keys: Mapping[str, frozenset[str]] | None = None


def validate_schema(guard: SchemaGuard) -> None:
    """Validate the live database against ``guard``; raise RuntimeError on drift."""
    label = guard.spec.label
    with guard.spec.engine.connect() as connection:
        inspector = inspect(connection)
        existing_tables = set(inspector.get_table_names(schema=DATABASE_SCHEMA))
        missing_tables = guard.required_tables - existing_tables
        if missing_tables:
            raise RuntimeError(f'{label} migration validation failed: missing tables {sorted(missing_tables)}')

        expected_heads = script_heads(guard.spec)
        current_heads = set(
            MigrationContext.configure(
                connection,
                opts={
                    'version_table': guard.spec.version_table,
                    'version_table_schema': DATABASE_SCHEMA,
                },
            ).get_current_heads()
        )
        if current_heads != expected_heads:
            raise RuntimeError(
                f'{label} migration validation failed: '
                f'expected version {sorted(expected_heads)}, got {sorted(current_heads)}'
            )

        _validate_named_objects(label, inspector, 'get_unique_constraints', 'unique constraints', guard.required_unique)
        _validate_named_objects(label, inspector, 'get_check_constraints', 'check constraints', guard.required_checks)
        _validate_named_objects(label, inspector, 'get_indexes', 'indexes', guard.required_indexes)

        if guard.expected_foreign_keys is not None:
            _validate_foreign_keys(label, inspector, guard)


def _validate_named_objects(
    label: str,
    inspector,
    inspector_method: str,
    object_label: str,
    required_by_table: Mapping[str, frozenset[str]],
) -> None:
    getter = getattr(inspector, inspector_method)
    for table_name, required in required_by_table.items():
        existing = {item['name'] for item in getter(table_name, schema=DATABASE_SCHEMA)}
        missing = required - existing
        if missing:
            raise RuntimeError(
                f'{label} migration validation failed: {table_name} missing {object_label} {sorted(missing)}'
            )


def _validate_foreign_keys(label: str, inspector, guard: SchemaGuard) -> None:
    for table_name in guard.required_tables:
        expected = guard.expected_foreign_keys.get(table_name, frozenset())
        referred = {
            foreign_key['referred_table']
            for foreign_key in inspector.get_foreign_keys(table_name, schema=DATABASE_SCHEMA)
        }
        if referred != expected:
            raise RuntimeError(
                f'{label} migration validation failed: {table_name} foreign keys '
                f'expected {sorted(expected)}, got {sorted(referred)}'
            )


__all__ = ['SchemaGuard', 'validate_schema']
