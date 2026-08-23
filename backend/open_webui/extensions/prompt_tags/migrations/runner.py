from __future__ import annotations

from pathlib import Path

from open_webui.extensions.migration_kit import MigrationSpec, run_extension_migrations
from open_webui.extensions.prompt_tags.db import PromptTagBase, engine
from sqlalchemy import Connection

# 扩展迁移链的静态描述；锁与上游 head 校验等通用逻辑见 migration_kit。
SPEC = MigrationSpec(
    label='prompt tag',
    migrations_dir=Path(__file__).parent,
    metadata=PromptTagBase.metadata,
    engine=engine,
    version_table='ext_prompt_tag_schema_version',
    schema_attribute='prompt_tag_schema',
    lock_namespace='open-webui-prompt-tag-migrations',
    sqlite_lock_suffix='prompt-tag-migrations.lock',
)


def run_prompt_tag_migrations(
    connection: Connection | None = None,
    *,
    verify_upstream: bool = True,
    schema: str | None = None,
) -> None:
    """Upgrade the independent prompt tag migration chain to head; propagate migration failures."""
    run_extension_migrations(SPEC, connection, verify_upstream=verify_upstream, schema=schema)


__all__ = ['SPEC', 'run_prompt_tag_migrations']
