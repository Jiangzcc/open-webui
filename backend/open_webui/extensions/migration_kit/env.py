from __future__ import annotations

import logging.config

from alembic import context
from open_webui.env import DATABASE_SCHEMA
from sqlalchemy import engine_from_config, pool

from .context import migration_context_options
from .spec import MigrationSpec


def run_env(spec: MigrationSpec) -> None:
    """Shared body for per-extension Alembic env.py files.

    每个扩展的 env.py 只需导入自己的 SPEC 并调用本函数；目标 schema 通过
    ``config.attributes[spec.schema_attribute]`` 传入（由共享 runner 设置），
    未提供时回退到 DATABASE_SCHEMA。
    """
    config = context.config
    if config.config_file_name:
        logging.config.fileConfig(config.config_file_name, disable_existing_loggers=False)

    schema = config.attributes.get(spec.schema_attribute, DATABASE_SCHEMA)
    options = migration_context_options(spec.version_table, schema, spec.metadata)

    if context.is_offline_mode():
        url = config.get_main_option('sqlalchemy.url')
        context.configure(
            url=url,
            literal_binds=True,
            dialect_opts={'paramstyle': 'named'},
            **options,
        )
        with context.begin_transaction():
            context.run_migrations()
        return

    connection = config.attributes.get('connection')
    if connection is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}), prefix='sqlalchemy.', poolclass=pool.NullPool
        )
        with connectable.connect() as owned_connection:
            _run_migrations(owned_connection, options)
        return
    _run_migrations(connection, options)


def _run_migrations(connection, options: dict) -> None:
    context.configure(connection=connection, **options)
    with context.begin_transaction():
        context.run_migrations()


__all__ = ['run_env']
