from __future__ import annotations

from pathlib import Path

from open_webui.extensions.credits.db import CreditBase, engine
from open_webui.extensions.migration_kit import MigrationSpec, run_extension_migrations
from sqlalchemy import Connection

# 扩展迁移链的静态描述；锁与上游 head 校验等通用逻辑见 migration_kit。
SPEC = MigrationSpec(
    label='credit',
    migrations_dir=Path(__file__).parent,
    metadata=CreditBase.metadata,
    engine=engine,
    version_table='ext_credit_schema_version',
    schema_attribute='credit_schema',
    lock_namespace='open-webui-credits-migrations',
    sqlite_lock_suffix='credit-migrations.lock',
)


def run_credit_migrations(
    connection: Connection | None = None,
    *,
    verify_upstream: bool = True,
    schema: str | None = None,
) -> None:
    """Upgrade the independent credit migration chain to head; propagate migration failures."""
    run_extension_migrations(SPEC, connection, verify_upstream=verify_upstream, schema=schema)


__all__ = ['SPEC', 'run_credit_migrations']
