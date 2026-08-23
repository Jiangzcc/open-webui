from __future__ import annotations

from pathlib import Path

from open_webui.extensions.migration_kit import MigrationSpec, run_extension_migrations
from open_webui.extensions.model_ops.db import ModelOpsBase, engine
from sqlalchemy import Connection

# 扩展迁移链的静态描述；锁与上游 head 校验等通用逻辑见 migration_kit。
SPEC = MigrationSpec(
    label='model ops',
    migrations_dir=Path(__file__).parent,
    metadata=ModelOpsBase.metadata,
    engine=engine,
    version_table='ext_model_ops_schema_version',
    schema_attribute='model_ops_schema',
    lock_namespace='open-webui-model-ops-migrations',
    sqlite_lock_suffix='model-ops-migrations.lock',
)


def run_model_ops_migrations(
    connection: Connection | None = None,
    *,
    verify_upstream: bool = True,
    schema: str | None = None,
) -> None:
    """Upgrade the independent model ops migration chain to head; propagate migration failures."""
    run_extension_migrations(SPEC, connection, verify_upstream=verify_upstream, schema=schema)


__all__ = ['SPEC', 'run_model_ops_migrations']
