from __future__ import annotations

from pathlib import Path

from open_webui.extensions.migration_kit import MigrationSpec, run_extension_migrations
from open_webui.extensions.provider_ops.db import ProviderOpsBase, engine
from sqlalchemy import Connection

# 扩展迁移链的静态描述；锁与上游 head 校验等通用逻辑见 migration_kit。
SPEC = MigrationSpec(
    label='provider ops',
    migrations_dir=Path(__file__).parent,
    metadata=ProviderOpsBase.metadata,
    engine=engine,
    version_table='ext_provider_ops_schema_version',
    schema_attribute='provider_ops_schema',
    lock_namespace='open-webui-provider-ops-migrations',
    sqlite_lock_suffix='provider-ops-migrations.lock',
)


def run_provider_ops_migrations(
    connection: Connection | None = None,
    *,
    verify_upstream: bool = True,
    schema: str | None = None,
) -> None:
    """Upgrade the independent provider ops migration chain to head; propagate migration failures."""
    run_extension_migrations(SPEC, connection, verify_upstream=verify_upstream, schema=schema)


__all__ = ['SPEC', 'run_provider_ops_migrations']
