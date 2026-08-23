from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine, MetaData


@dataclass(frozen=True)
class MigrationSpec:
    """Describe one extension's independent Alembic migration chain.

    每个扩展的 migrations/runner.py 持有一份静态 SPEC，共享 runner 与 env
    逻辑都以此为唯一参数面（复盘 #15：此前 5 份 runner 拷贝已发生行为漂移）。

    - ``label``：错误消息中的扩展名（如 ``creation``）。
    - ``migrations_dir``：扩展 migrations 目录（含 env.py 与 versions/）。
    - ``metadata`` / ``engine``：扩展 ORM 的 Base.metadata 与共享 engine。
    - ``version_table``：该扩展独立迁移链的版本表名（ext_ 命名空间）。
    - ``schema_attribute``：env.py 从 config.attributes 读取目标 schema 的键。
    - ``lock_namespace`` / ``sqlite_lock_suffix``：并发迁移锁的命名。
    """

    label: str
    migrations_dir: Path
    metadata: MetaData
    engine: Engine
    version_table: str
    schema_attribute: str
    lock_namespace: str
    sqlite_lock_suffix: str


__all__ = ['MigrationSpec']
