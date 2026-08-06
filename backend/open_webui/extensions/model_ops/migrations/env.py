from __future__ import annotations

import logging.config

from alembic import context
from open_webui.env import DATABASE_SCHEMA
from open_webui.extensions.model_ops.db import ModelOpsBase
from open_webui.extensions.model_ops.migrations.config import migration_context_options
from open_webui.extensions.model_ops.models import ImageModelOperation  # noqa: F401
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name:
    logging.config.fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = ModelOpsBase.metadata
model_ops_schema = config.attributes.get('model_ops_schema', DATABASE_SCHEMA)


def _run_migrations(connection) -> None:
    context.configure(connection=connection, **migration_context_options(model_ops_schema, target_metadata))
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get('connection')
    if connection is not None:
        _run_migrations(connection)
        return
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}), prefix='sqlalchemy.', poolclass=pool.NullPool
    )
    with connectable.connect() as owned_connection:
        _run_migrations(owned_connection)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option('sqlalchemy.url'),
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        **migration_context_options(model_ops_schema, target_metadata),
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
