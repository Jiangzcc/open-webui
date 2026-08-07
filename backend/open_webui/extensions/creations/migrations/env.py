from __future__ import annotations

import logging.config

from alembic import context
from open_webui.env import DATABASE_SCHEMA
from open_webui.extensions.creations.db import CreationBase
from open_webui.extensions.creations.migrations.config import migration_context_options
from open_webui.extensions.creations.models import (  # noqa: F401
    CreationMediaItem,
    ImageGenerationTask,
    VideoGenerationTask,
)
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name:
    logging.config.fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = CreationBase.metadata
creation_schema = config.attributes.get('creation_schema', DATABASE_SCHEMA)


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        **migration_context_options(creation_schema, target_metadata),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get('connection')
    if connection is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}), prefix='sqlalchemy.', poolclass=pool.NullPool
        )
        with connectable.connect() as owned_connection:
            _run_migrations(owned_connection)
        return
    _run_migrations(connection)


def _run_migrations(connection) -> None:
    context.configure(connection=connection, **migration_context_options(creation_schema, target_metadata))
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
