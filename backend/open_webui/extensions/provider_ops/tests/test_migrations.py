from __future__ import annotations

from alembic.migration import MigrationContext
from open_webui.extensions.provider_ops.migrations.runner import run_provider_ops_migrations
from sqlalchemy import create_engine, inspect


def test_provider_ops_migration_creates_all_tables(tmp_path) -> None:
    engine = create_engine(f'sqlite:///{tmp_path / "provider-ops.sqlite"}')
    try:
        with engine.connect() as connection:
            run_provider_ops_migrations(connection, verify_upstream=False, schema=None)
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
            invocation_columns = {item['name'] for item in inspector.get_columns('ext_provider_invocation')}
            assert {
                'actual_cost_total',
                'actual_cost_currency',
                'cost_accuracy',
                'billing_event_at',
            } <= invocation_columns
            sync_run_columns = {item['name'] for item in inspector.get_columns('ext_provider_sync_run')}
            assert 'heartbeat_at' in sync_run_columns
            sync_run_indexes = {item['name']: item for item in inspector.get_indexes('ext_provider_sync_run')}
            assert sync_run_indexes['ux_ext_provider_sync_run_running']['unique'] == 1
            assert (
                MigrationContext.configure(
                    connection,
                    opts={'version_table': 'ext_provider_ops_schema_version'},
                ).get_current_revision()
                == '0001_create_provider_ops_tables'
            )
    finally:
        engine.dispose()
