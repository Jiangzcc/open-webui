from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from open_webui import env as upstream_env
from open_webui.extensions.credits import db as credit_db
from open_webui.extensions.credits.db import CreditBase, credit_session
from open_webui.extensions.credits.migrations.config import migration_context_options
from open_webui.extensions.credits.migrations.runner import (
    _LOCK_NAMESPACE,
    _acquire_postgres_lock,
    _acquire_sqlite_lock,
    _postgres_lock_key,
    _release_postgres_lock,
    _run_postgres_migration,
    _validate_upstream_head,
    run_credit_migrations,
)
from open_webui.extensions.credits.models import CreditAccount, CreditLedger, CreditPrice, CreditUsage
from open_webui.internal import db as upstream_db
from sqlalchemy import BigInteger, MetaData, Table, create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError

TABLE_NAMES = {'ext_credit_account', 'ext_credit_usage', 'ext_credit_ledger', 'ext_credit_price'}
EXPECTED_INDEXES = {
    'ext_credit_usage': {
        'ix_ext_credit_usage_status_updated',
        'ix_ext_credit_usage_user_created',
    },
    'ext_credit_ledger': {
        'ix_ext_credit_ledger_user_created',
        'ix_ext_credit_ledger_created',
        'ix_ext_credit_ledger_usage',
        'ux_ext_credit_ledger_related_refund',
    },
    'ext_credit_price': {'ix_ext_credit_price_enabled_service_action'},
}
BIGINT_COLUMNS = {
    'ext_credit_account': {'balance', 'created_at', 'updated_at'},
    'ext_credit_usage': {
        'charged_credits',
        'invocation_started_at',
        'created_at',
        'updated_at',
        'completed_at',
    },
    'ext_credit_ledger': {'amount', 'balance_before', 'balance_after', 'created_at'},
    'ext_credit_price': {'created_at', 'updated_at'},
}


def _sqlite_fingerprint(connection):
    rows = connection.execute(
        text(
            'SELECT type, name, tbl_name, sql FROM sqlite_master '
            "WHERE name = 'user' OR tbl_name = 'user' ORDER BY type, name"
        )
    ).fetchall()
    return [(row.type, row.name, row.tbl_name, row.sql) for row in rows]


def _upgrade_sqlite(engine) -> None:
    with engine.connect() as connection:
        run_credit_migrations(connection=connection, verify_upstream=False)
        assert not connection.in_transaction()


def _migration_config(schema: str | None = None) -> Config:
    config = Config()
    config.set_main_option('script_location', str(Path(__file__).parents[1] / 'migrations'))
    config.attributes['credit_schema'] = schema
    return config


def test_upgrade_preserves_sentinel_and_creates_only_extension_objects(sqlite_database):
    engine, database_path = sqlite_database
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE user (id VARCHAR(128) PRIMARY KEY, name VARCHAR(128) NOT NULL)'))
        connection.execute(text('CREATE UNIQUE INDEX ix_user_name ON user (name)'))
        before = _sqlite_fingerprint(connection)

    _upgrade_sqlite(engine)

    with engine.connect() as connection:
        assert _sqlite_fingerprint(connection) == before
        names = set(inspect(connection).get_table_names())
        assert names == TABLE_NAMES | {'user', 'ext_credit_schema_version'}
        assert 'alembic_version' not in names
        assert connection.execute(text('SELECT version_num FROM ext_credit_schema_version')).scalar_one() == (
            '0002_add_reconciliation_guard'
        )
    assert not Path(f'{database_path}.credit-migrations.lock').exists()


def test_upgrade_is_idempotent_and_downgrade_preserves_sentinel(sqlite_database):
    engine, _ = sqlite_database
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE user (id VARCHAR(128) PRIMARY KEY)'))
    _upgrade_sqlite(engine)
    _upgrade_sqlite(engine)

    config = _migration_config()
    with engine.connect() as connection:
        config.attributes['connection'] = connection
        command.downgrade(config, 'base')
        assert not connection.in_transaction()
    with engine.connect() as connection:
        names = set(inspect(connection).get_table_names())
        assert names == {'user', 'ext_credit_schema_version'}
        assert connection.execute(text('SELECT COUNT(*) FROM ext_credit_schema_version')).scalar_one() == 0


def test_revision_has_columns_bigints_constraints_foreign_keys_and_indexes(sqlite_database):
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)
    inspector = inspect(engine)

    assert set(inspector.get_table_names()) >= TABLE_NAMES
    assert {
        foreign_key['referred_table'] for table in TABLE_NAMES for foreign_key in inspector.get_foreign_keys(table)
    } <= TABLE_NAMES
    ledger_foreign_keys = {
        foreign_key['constrained_columns'][0]: foreign_key
        for foreign_key in inspector.get_foreign_keys('ext_credit_ledger')
    }
    assert ledger_foreign_keys['account_id']['referred_table'] == 'ext_credit_account'
    assert ledger_foreign_keys['usage_id']['referred_table'] == 'ext_credit_usage'
    assert all(foreign_key['options']['ondelete'] == 'RESTRICT' for foreign_key in ledger_foreign_keys.values())
    assert not inspector.get_foreign_keys('ext_credit_usage')

    unique_names = {
        table_name: {constraint['name'] for constraint in inspector.get_unique_constraints(table_name)}
        for table_name in TABLE_NAMES
    }
    assert unique_names['ext_credit_account'] >= {'uq_ext_credit_account_user'}
    assert unique_names['ext_credit_usage'] >= {
        'uq_ext_credit_usage_idempotency',
        'uq_ext_credit_usage_ledger',
    }
    assert unique_names['ext_credit_price'] >= {'uq_ext_credit_price_service'}

    for table_name, expected_names in EXPECTED_INDEXES.items():
        assert {index['name'] for index in inspector.get_indexes(table_name)} >= expected_names
    for table_name, column_names in BIGINT_COLUMNS.items():
        reflected = {column['name']: column for column in inspector.get_columns(table_name)}
        assert all(isinstance(reflected[name]['type'], BigInteger) for name in column_names)

    checks = {
        table_name: {
            constraint['name']: constraint['sqltext'] for constraint in inspector.get_check_constraints(table_name)
        }
        for table_name in TABLE_NAMES
    }
    assert {
        'ck_ext_credit_usage_status',
        'ck_ext_credit_usage_channel',
        'ck_ext_credit_usage_exempt_consistency',
    } <= checks['ext_credit_usage'].keys()
    assert {
        'ck_ext_credit_ledger_balance_equation',
        'ck_ext_credit_ledger_balance_nonnegative',
        'ck_ext_credit_ledger_entry_type',
        'ck_ext_credit_ledger_request_source',
        'ck_ext_credit_ledger_reason_code',
    } <= checks['ext_credit_ledger'].keys()


def test_orm_metadata_matches_every_revision_table(sqlite_database):
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)
    inspector = inspect(engine)

    assert set(CreditBase.metadata.tables) == TABLE_NAMES
    for table_name in TABLE_NAMES:
        model_table = CreditBase.metadata.tables[table_name]
        assert set(model_table.columns.keys()) == {column['name'] for column in inspector.get_columns(table_name)}
        assert {index.name for index in model_table.indexes} == EXPECTED_INDEXES.get(table_name, set())
    for table_name, column_names in BIGINT_COLUMNS.items():
        model_table = CreditBase.metadata.tables[table_name]
        assert all(isinstance(model_table.c[name].type, BigInteger) for name in column_names)


def test_jsonfield_roundtrip_and_placeholder_constraints(sqlite_database):
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)
    with engine.begin() as connection:
        connection.execute(
            CreditPrice.__table__.insert().values(
                id='price-1',
                service_type='image',
                resource_id='image',
                action='generate',
                base_price='1.25',
                rules={'dimensions': [{'key': 'quality'}]},
                enabled=True,
                created_at=1,
                updated_at=1,
            )
        )
        assert connection.execute(select(CreditPrice.rules)).scalar_one() == {'dimensions': [{'key': 'quality'}]}
        connection.execute(
            CreditAccount.__table__.insert().values(id='a', user_id='u', balance=10, created_at=1, updated_at=1)
        )
        connection.execute(
            CreditUsage.__table__.insert().values(
                id='usage',
                user_id='u',
                idempotency_key='key',
                request_hash='hash',
                service_type='image',
                resource_id='image',
                action='generate',
                channel='api',
                status='debited',
                exempt=False,
                charged_credits=2,
                created_at=1,
                updated_at=1,
            )
        )
        connection.execute(
            CreditLedger.__table__.insert().values(
                id='ledger',
                account_id='a',
                usage_id='usage',
                user_id='u',
                amount=-2,
                balance_before=10,
                balance_after=8,
                entry_type='consumption',
                request_source='api',
                request_id='request',
                created_at=1,
            )
        )


def test_server_defaults_are_applied_by_database(sqlite_database):
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)
    with engine.begin() as connection:
        connection.execute(CreditAccount.__table__.insert().values(id='a', user_id='u', created_at=1, updated_at=1))
        connection.execute(
            CreditUsage.__table__.insert().values(
                id='usage',
                user_id='u',
                idempotency_key='key',
                request_hash='hash',
                service_type='image',
                resource_id='image',
                action='generate',
                channel='api',
                status='debited',
                created_at=1,
                updated_at=1,
            )
        )
        connection.execute(
            CreditPrice.__table__.insert().values(
                id='price',
                service_type='image',
                resource_id='image',
                action='generate',
                base_price='1',
                rules={},
                created_at=1,
                updated_at=1,
            )
        )
        assert connection.execute(select(CreditAccount.balance)).scalar_one() == 0
        assert connection.execute(select(CreditUsage.charged_credits, CreditUsage.exempt)).one() == (0, False)
        assert connection.execute(select(CreditPrice.enabled)).scalar_one() is True


def test_production_adapter_identity():
    assert credit_db.engine is upstream_db.engine
    assert credit_db.async_engine is upstream_db.async_engine
    assert credit_db.AsyncSessionLocal is upstream_db.AsyncSessionLocal
    assert credit_db.JSONField is upstream_db.JSONField
    assert CreditBase.metadata.schema == upstream_env.DATABASE_SCHEMA


def test_database_controlled_enums_reject_invalid_values(sqlite_database):
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)
    with engine.begin() as connection:
        connection.execute(
            CreditAccount.__table__.insert().values(id='a', user_id='u', balance=10, created_at=1, updated_at=1)
        )
        usage_values = {
            'id': 'usage',
            'user_id': 'u',
            'idempotency_key': 'key',
            'request_hash': 'hash',
            'service_type': 'future-service',
            'resource_id': 'future-resource',
            'action': 'future-action',
            'status': 'debited',
            'exempt': False,
            'charged_credits': 0,
            'created_at': 1,
            'updated_at': 1,
        }
        with pytest.raises(IntegrityError):
            connection.execute(CreditUsage.__table__.insert().values(**usage_values, channel='invalid'))

    for field, value in [('request_source', 'invalid'), ('reason_code', 'invalid')]:
        with engine.begin() as connection, pytest.raises(IntegrityError):
            ledger_values = {
                'id': f'bad-{field}',
                'account_id': 'a',
                'user_id': 'u',
                'amount': 0,
                'balance_before': 10,
                'balance_after': 10,
                'entry_type': 'system_adjustment',
                'request_source': 'api',
                'request_id': 'request',
                'created_at': 1,
            }
            ledger_values[field] = value
            connection.execute(CreditLedger.__table__.insert().values(**ledger_values))


def test_upstream_head_missing_and_behind_fail_before_extension_ddl(sqlite_database):
    engine, _ = sqlite_database
    for revision in (None, 'not-current-head'):
        if revision:
            with engine.begin() as connection:
                connection.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)'))
                connection.execute(text('INSERT INTO alembic_version VALUES (:revision)'), {'revision': revision})
        with engine.connect() as connection, pytest.raises(RuntimeError, match='upstream Alembic'):
            run_credit_migrations(connection=connection, verify_upstream=True)
        with engine.connect() as connection:
            assert 'ext_credit_account' not in inspect(connection).get_table_names()
        if revision:
            with engine.begin() as connection:
                connection.execute(text('DROP TABLE alembic_version'))


def test_upstream_head_uses_upstream_version_table_and_schema(monkeypatch):
    captured = {}

    class FakeMigrationContext:
        @classmethod
        def configure(cls, connection, opts):
            captured.update(opts)
            return SimpleNamespace(get_current_heads=lambda: ('head',))

    monkeypatch.setattr('open_webui.extensions.credits.migrations.runner.MigrationContext', FakeMigrationContext)
    monkeypatch.setattr(
        'open_webui.extensions.credits.migrations.runner.ScriptDirectory.from_config',
        lambda config: SimpleNamespace(get_heads=lambda: ['head']),
    )
    monkeypatch.setattr('open_webui.extensions.credits.migrations.runner.DATABASE_SCHEMA', 'tenant')

    _validate_upstream_head(object())

    assert captured == {'version_table': 'alembic_version', 'version_table_schema': 'tenant'}


def test_external_transaction_is_rejected_before_lock(sqlite_database):
    engine, _ = sqlite_database
    with engine.connect() as connection:
        transaction = connection.begin()
        with pytest.raises(RuntimeError, match='active transaction'):
            run_credit_migrations(connection=connection, verify_upstream=False)
        transaction.rollback()


def test_sqlite_lock_timeout_without_sleeping(monkeypatch, sqlite_database):
    engine, database_path = sqlite_database
    lock_path = Path(f'{database_path}.credit-migrations.lock')
    lock_path.touch()
    ticks = iter([0.0, 0.0, 20.0])
    monkeypatch.setattr('open_webui.extensions.credits.migrations.runner.time.monotonic', lambda: next(ticks))
    monkeypatch.setattr('open_webui.extensions.credits.migrations.runner.time.sleep', lambda _: None)
    try:
        with engine.connect() as connection, pytest.raises(TimeoutError, match='SQLite migration lock'):
            _acquire_sqlite_lock(connection)
    finally:
        lock_path.unlink()


def test_postgres_lock_sql_stable_key_timeout_and_release(monkeypatch):
    statements = []

    class FakeConnection:
        def __init__(self, results=None):
            self.results = iter(results or [True])

        def execute(self, statement, params):
            statements.append((str(statement), params))
            return SimpleNamespace(scalar=lambda: next(self.results))

    ticks = iter([0.0, 0.0, 20.0])
    monkeypatch.setattr('open_webui.extensions.credits.migrations.runner.time.monotonic', lambda: next(ticks))
    monkeypatch.setattr('open_webui.extensions.credits.migrations.runner.time.sleep', lambda _: None)
    with pytest.raises(TimeoutError, match='PostgreSQL'):
        _acquire_postgres_lock(FakeConnection([False, False]))

    release_connection = FakeConnection([True])
    _release_postgres_lock(release_connection, _postgres_lock_key())
    assert _postgres_lock_key() == int.from_bytes(
        __import__('hashlib').sha256(_LOCK_NAMESPACE.encode()).digest()[:8], 'big', signed=True
    )
    assert 'pg_try_advisory_lock' in statements[0][0]
    assert 'pg_advisory_unlock' in statements[-1][0]


def test_postgres_transaction_order_commits_acquire_upgrade_and_release(monkeypatch):
    events = []

    class FakeConnection:
        def __init__(self):
            self.active = False

        def execute(self, statement, params):
            sql = str(statement)
            self.active = True
            events.append('acquire' if 'try_advisory' in sql else 'release')
            return SimpleNamespace(scalar=lambda: True)

        def commit(self):
            events.append('commit')
            self.active = False

        def in_transaction(self):
            return self.active

    def upgrade(connection, verify_upstream, schema):
        events.append('upgrade')
        connection.active = True

    monkeypatch.setattr('open_webui.extensions.credits.migrations.runner._upgrade', upgrade)
    connection = FakeConnection()
    _run_postgres_migration(connection, verify_upstream=False, schema='tenant')

    assert events == ['acquire', 'commit', 'upgrade', 'commit', 'release', 'commit']
    assert not connection.in_transaction()


def test_migration_error_remains_primary_when_release_also_fails(monkeypatch, sqlite_database):
    engine, _ = sqlite_database
    monkeypatch.setattr(
        'open_webui.extensions.credits.migrations.runner._acquire_database_lock', lambda connection: object()
    )

    def fail_upgrade(*args, **kwargs):
        raise ValueError('migration failed')

    def fail_release(*args, **kwargs):
        raise RuntimeError('release failed')

    monkeypatch.setattr('open_webui.extensions.credits.migrations.runner._upgrade', fail_upgrade)
    monkeypatch.setattr('open_webui.extensions.credits.migrations.runner._release_database_lock', fail_release)
    with engine.connect() as connection, pytest.raises(ValueError, match='migration failed'):
        run_credit_migrations(connection=connection, verify_upstream=False)


def test_dynamic_schema_context_options_are_behavioral():
    tenant_options = migration_context_options('tenant', CreditBase.metadata)
    assert tenant_options == {
        'target_metadata': CreditBase.metadata,
        'version_table': 'ext_credit_schema_version',
        'version_table_schema': 'tenant',
        'include_schemas': True,
    }
    default_options = migration_context_options(None, CreditBase.metadata)
    assert default_options['version_table_schema'] is None
    assert default_options['include_schemas'] is False
    assert default_options['target_metadata'] is CreditBase.metadata


def _schema_fingerprint(connection, schema: str) -> dict:
    inspector = inspect(connection)
    fingerprint = {}
    for table_name in inspector.get_table_names(schema=schema):
        fingerprint[table_name] = {
            'columns': [
                (column['name'], str(column['type']), column['nullable'], str(column.get('default')))
                for column in inspector.get_columns(table_name, schema=schema)
            ],
            'indexes': sorted(
                (index['name'], tuple(index['column_names']), index['unique'])
                for index in inspector.get_indexes(table_name, schema=schema)
            ),
            'unique': sorted(
                (constraint['name'], tuple(constraint['column_names']))
                for constraint in inspector.get_unique_constraints(table_name, schema=schema)
            ),
            'foreign_keys': sorted(
                (
                    constraint.get('name'),
                    tuple(constraint['constrained_columns']),
                    constraint.get('referred_schema'),
                    constraint['referred_table'],
                    tuple(constraint['referred_columns']),
                    constraint.get('options', {}).get('ondelete'),
                )
                for constraint in inspector.get_foreign_keys(table_name, schema=schema)
            ),
            'checks': sorted(
                (constraint['name'], constraint['sqltext'])
                for constraint in inspector.get_check_constraints(table_name, schema=schema)
            ),
        }
    return fingerprint


def _postgres_tables(schema: str) -> dict[str, Table]:
    metadata = MetaData()
    return {
        table.name: table.to_metadata(metadata, schema=schema)
        for table in (CreditAccount.__table__, CreditUsage.__table__, CreditLedger.__table__, CreditPrice.__table__)
    }


@pytest.mark.skipif(
    not os.getenv('TEST_POSTGRES_DATABASE_URL'),
    reason='TEST_POSTGRES_DATABASE_URL is not set; PostgreSQL migration tests skipped',
)
def test_postgresql_non_public_schema_concurrent_migrations_and_constraints():
    engine = create_engine(os.environ['TEST_POSTGRES_DATABASE_URL'])
    schema = f'credit_test_{uuid4().hex}'
    try:
        with engine.connect() as connection:
            public_before = _schema_fingerprint(connection, 'public')
            connection.rollback()
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))

        def migrate() -> None:
            with engine.connect() as connection:
                run_credit_migrations(connection=connection, verify_upstream=False, schema=schema)
                assert not connection.in_transaction()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(migrate) for _ in range(2)]
            for future in futures:
                future.result()

        with engine.connect() as connection:
            inspector = inspect(connection)
            assert set(inspector.get_table_names(schema=schema)) == TABLE_NAMES | {'ext_credit_schema_version'}
            assert 'alembic_version' not in inspector.get_table_names(schema=schema)
            assert (
                connection.execute(text(f'SELECT version_num FROM "{schema}".ext_credit_schema_version')).scalar_one()
                == '0001_create_credit_tables'
            )
            for table_name, expected_names in EXPECTED_INDEXES.items():
                assert {index['name'] for index in inspector.get_indexes(table_name, schema=schema)} >= expected_names
            for table_name, column_names in BIGINT_COLUMNS.items():
                columns = {column['name']: column for column in inspector.get_columns(table_name, schema=schema)}
                assert all(isinstance(columns[name]['type'], BigInteger) for name in column_names)
            unique_names = {
                table_name: {
                    constraint['name'] for constraint in inspector.get_unique_constraints(table_name, schema=schema)
                }
                for table_name in TABLE_NAMES
            }
            assert unique_names['ext_credit_account'] >= {'uq_ext_credit_account_user'}
            assert unique_names['ext_credit_usage'] >= {
                'uq_ext_credit_usage_idempotency',
                'uq_ext_credit_usage_ledger',
            }
            assert unique_names['ext_credit_price'] >= {'uq_ext_credit_price_service'}
            foreign_keys = inspector.get_foreign_keys('ext_credit_ledger', schema=schema)
            assert {foreign_key['referred_table'] for foreign_key in foreign_keys} == {
                'ext_credit_account',
                'ext_credit_usage',
            }
            assert all(foreign_key['options']['ondelete'] == 'RESTRICT' for foreign_key in foreign_keys)
            expected_checks = {
                'ext_credit_usage': {
                    'ck_ext_credit_usage_status',
                    'ck_ext_credit_usage_channel',
                    'ck_ext_credit_usage_charged_nonnegative',
                    'ck_ext_credit_usage_exempt_consistency',
                },
                'ext_credit_ledger': {
                    'ck_ext_credit_ledger_balance_equation',
                    'ck_ext_credit_ledger_balance_nonnegative',
                    'ck_ext_credit_ledger_entry_type',
                    'ck_ext_credit_ledger_request_source',
                    'ck_ext_credit_ledger_reason_code',
                },
            }
            for table_name, names in expected_checks.items():
                assert {
                    constraint['name'] for constraint in inspector.get_check_constraints(table_name, schema=schema)
                } >= names
            defaults = {
                table_name: {
                    column['name']: str(column.get('default'))
                    for column in inspector.get_columns(table_name, schema=schema)
                }
                for table_name in TABLE_NAMES
            }
            assert defaults['ext_credit_account']['balance'] not in {'None', ''}
            assert defaults['ext_credit_usage']['charged_credits'] not in {'None', ''}
            assert defaults['ext_credit_usage']['exempt'] not in {'None', ''}
            assert defaults['ext_credit_price']['enabled'] not in {'None', ''}
            connection.rollback()

        tables = _postgres_tables(schema)
        with engine.begin() as connection:
            connection.execute(
                tables['ext_credit_price']
                .insert()
                .values(
                    id='price',
                    service_type='image',
                    resource_id='image',
                    action='generate',
                    base_price='1',
                    rules={'items': [1, 2]},
                    created_at=1,
                    updated_at=1,
                )
            )
            connection.execute(
                tables['ext_credit_account'].insert().values(id='account', user_id='user', created_at=1, updated_at=1)
            )
        with engine.connect() as connection:
            assert connection.execute(select(tables['ext_credit_price'].c.rules)).scalar_one() == {'items': [1, 2]}
            assert connection.execute(select(tables['ext_credit_account'].c.balance)).scalar_one() == 0
            assert connection.execute(select(tables['ext_credit_price'].c.enabled)).scalar_one() is True
            connection.rollback()

        invalid_usage = {
            'id': 'bad-usage',
            'user_id': 'user',
            'idempotency_key': 'bad',
            'request_hash': 'hash',
            'service_type': 'future',
            'resource_id': 'future',
            'action': 'future',
            'channel': 'invalid',
            'status': 'debited',
            'exempt': True,
            'charged_credits': 1,
            'created_at': 1,
            'updated_at': 1,
        }
        with engine.begin() as connection, pytest.raises(IntegrityError):
            connection.execute(tables['ext_credit_usage'].insert().values(**invalid_usage))
        invalid_ledgers = [
            {'id': 'bad-equation', 'amount': -1, 'balance_before': 10, 'balance_after': 10, 'request_source': 'api'},
            {'id': 'bad-source', 'amount': 0, 'balance_before': 10, 'balance_after': 10, 'request_source': 'bad'},
            {
                'id': 'bad-reason',
                'amount': 0,
                'balance_before': 10,
                'balance_after': 10,
                'request_source': 'api',
                'reason_code': 'bad',
            },
        ]
        for values in invalid_ledgers:
            with engine.begin() as connection, pytest.raises(IntegrityError):
                connection.execute(
                    tables['ext_credit_ledger']
                    .insert()
                    .values(
                        account_id='account',
                        user_id='user',
                        entry_type='system_adjustment',
                        request_id='request',
                        created_at=1,
                        **values,
                    )
                )

        with engine.connect() as connection:
            assert _schema_fingerprint(connection, 'public') == public_before
            connection.rollback()
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        engine.dispose()


def test_async_credit_session_uses_upstream_factory(monkeypatch):
    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    def factory():
        return FakeSession()

    monkeypatch.setattr('open_webui.extensions.credits.db.AsyncSessionLocal', factory)

    async def exercise():
        async with credit_session() as session:
            assert isinstance(session, FakeSession)

    asyncio.run(exercise())
