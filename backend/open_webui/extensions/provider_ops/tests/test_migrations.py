from __future__ import annotations

from alembic import command
from alembic.migration import MigrationContext
from open_webui.extensions.provider_ops.migrations.runner import _migration_config, run_provider_ops_migrations
from sqlalchemy import create_engine, inspect


def test_provider_ops_migration_creates_invocation_table(tmp_path) -> None:
    engine = create_engine(f'sqlite:///{tmp_path / "provider-ops.sqlite"}')
    try:
        with engine.connect() as connection:
            run_provider_ops_migrations(connection, schema=None)
            inspector = inspect(connection)
            assert {
                'ext_provider_invocation',
                'ext_provider_price_snapshot',
                'ext_provider_billing_event',
                'ext_provider_request_record',
                'ext_provider_usage_bucket',
                'ext_provider_analytics_bucket',
                'ext_provider_sync_run',
            } <= set(inspector.get_table_names())
            assert {
                'ix_ext_provider_invocation_task',
                'ix_ext_provider_invocation_provider_created',
                'ix_ext_provider_invocation_model_created',
                'ix_ext_provider_invocation_status_updated',
            } <= {item['name'] for item in inspector.get_indexes('ext_provider_invocation')}
            assert (
                MigrationContext.configure(
                    connection,
                    opts={'version_table': 'ext_provider_ops_schema_version'},
                ).get_current_revision()
                == '0003_add_authoritative_requests_and_billing'
            )
    finally:
        engine.dispose()


def test_existing_platform_sync_schema_upgrades_to_authoritative_records(tmp_path) -> None:
    engine = create_engine(f'sqlite:///{tmp_path / "provider-ops-upgrade.sqlite"}')
    try:
        with engine.connect() as connection:
            config = _migration_config(None)
            config.attributes['connection'] = connection
            command.upgrade(config, '0002_add_platform_sync_tables')
            connection.commit()
            assert 'ext_provider_billing_event' not in inspect(connection).get_table_names()
            connection.commit()

            run_provider_ops_migrations(connection, schema=None)

            tables = set(inspect(connection).get_table_names())
            assert {'ext_provider_billing_event', 'ext_provider_request_record'} <= tables
            assert (
                MigrationContext.configure(
                    connection,
                    opts={'version_table': 'ext_provider_ops_schema_version'},
                ).get_current_revision()
                == '0003_add_authoritative_requests_and_billing'
            )
    finally:
        engine.dispose()
