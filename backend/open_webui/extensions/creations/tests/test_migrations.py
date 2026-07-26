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
from open_webui.extensions.creations import db as creation_db
from open_webui.extensions.creations.db import CreationBase, creation_session
from open_webui.extensions.creations.migrations.config import migration_context_options
from open_webui.extensions.creations.migrations.runner import (
    _LOCK_NAMESPACE,
    _acquire_postgres_lock,
    _acquire_sqlite_lock,
    _postgres_lock_key,
    _release_postgres_lock,
    _run_postgres_migration,
    _validate_upstream_head,
    run_creation_migrations,
)
from open_webui.extensions.creations.models import CreationMediaItem
from open_webui.internal import db as upstream_db
from sqlalchemy import BigInteger, MetaData, Table, Text, create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError

TABLE_NAMES = {
    'ext_creation_media_item',
    'ext_creation_post',
    'ext_creation_post_media',
    'ext_creation_post_reaction',
}
EXPECTED_INDEXES = {
    'ext_creation_media_item': {
        'ix_ext_creation_media_user_visible_created',
        'ix_ext_creation_media_visible_created',
        'ix_ext_creation_media_batch',
    },
    'ext_creation_post': {
        'ix_ext_creation_post_status_published',
        'ix_ext_creation_post_status_popular',
        'ix_ext_creation_post_user_status',
    },
    'ext_creation_post_media': {'ix_ext_creation_post_media_creation'},
    'ext_creation_post_reaction': {'ix_ext_creation_post_reaction_user_kind'},
}
EXPECTED_CHECKS = {
    'ck_ext_creation_media_kind',
    'ck_ext_creation_media_task',
    'ck_ext_creation_media_source',
    'ck_ext_creation_post_status',
    'ck_ext_creation_post_like_count',
    'ck_ext_creation_post_favorite_count',
    'ck_ext_creation_post_reaction_kind',
}
BIGINT_COLUMNS = {
    'ext_creation_media_item': {'created_at', 'updated_at'},
    'ext_creation_post': {'published_at', 'created_at', 'updated_at'},
    'ext_creation_post_media': {'created_at'},
    'ext_creation_post_reaction': {'created_at'},
}
TEXT_COLUMNS = {'ext_creation_media_item': {'prompt', 'negative_prompt'}}


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
        run_creation_migrations(connection=connection, verify_upstream=False)
        assert not connection.in_transaction()


def _migration_config(schema: str | None = None) -> Config:
    config = Config()
    config.set_main_option('script_location', str(Path(__file__).parents[1] / 'migrations'))
    config.attributes['creation_schema'] = schema
    return config


def test_upgrade_creates_only_creation_objects_and_preserves_upstream_sentinel(sqlite_database):
    engine, database_path = sqlite_database
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE user (id VARCHAR(128) PRIMARY KEY, name VARCHAR(128) NOT NULL)'))
        connection.execute(text('CREATE UNIQUE INDEX ix_user_name ON user (name)'))
        before = _sqlite_fingerprint(connection)

    _upgrade_sqlite(engine)

    with engine.connect() as connection:
        assert _sqlite_fingerprint(connection) == before
        names = set(inspect(connection).get_table_names())
        assert names == {'user', *TABLE_NAMES, 'ext_creation_schema_version'}
        assert 'alembic_version' not in names
        assert connection.execute(text('SELECT version_num FROM ext_creation_schema_version')).scalar_one() == (
            '0002_create_discovery_tables'
        )
    assert not Path(f'{database_path}.creation-migrations.lock').exists()


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
        assert names == {'user', 'ext_creation_schema_version'}
        assert connection.execute(text('SELECT COUNT(*) FROM ext_creation_schema_version')).scalar_one() == 0


def test_revision_has_required_constraints_and_indexes(sqlite_database):
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)
    inspector = inspect(engine)

    assert set(inspector.get_table_names()) >= TABLE_NAMES
    for table_name in TABLE_NAMES:
        assert inspector.get_foreign_keys(table_name) == []

    unique_names = {constraint['name'] for constraint in inspector.get_unique_constraints('ext_creation_media_item')}
    assert unique_names >= {'uq_ext_creation_media_file'}

    media_unique = {constraint['name'] for constraint in inspector.get_unique_constraints('ext_creation_post_media')}
    assert media_unique >= {
        'uq_ext_creation_post_media_creation',
        'uq_ext_creation_post_media_position',
    }
    reaction_unique = {
        constraint['name'] for constraint in inspector.get_unique_constraints('ext_creation_post_reaction')
    }
    assert reaction_unique >= {'uq_ext_creation_post_reaction_actor_kind'}

    existing_checks = set()
    for table_name in TABLE_NAMES:
        existing_checks.update(constraint['name'] for constraint in inspector.get_check_constraints(table_name))
    assert existing_checks >= EXPECTED_CHECKS

    for table_name, expected in EXPECTED_INDEXES.items():
        assert {index['name'] for index in inspector.get_indexes(table_name)} >= expected


def test_orm_metadata_matches_the_revision_table(sqlite_database):
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)
    inspector = inspect(engine)

    assert set(CreationBase.metadata.tables) == TABLE_NAMES
    for table_name in TABLE_NAMES:
        model_table = CreationBase.metadata.tables[table_name]
        assert set(model_table.columns.keys()) == {column['name'] for column in inspector.get_columns(table_name)}
        assert {index.name for index in model_table.indexes} == EXPECTED_INDEXES[table_name]
        for name in BIGINT_COLUMNS[table_name]:
            assert isinstance(model_table.c[name].type, BigInteger)
    model_table = CreationBase.metadata.tables['ext_creation_media_item']
    for name in TEXT_COLUMNS['ext_creation_media_item']:
        assert isinstance(model_table.c[name].type, Text)


def test_jsonfield_roundtrip_and_enum_guardrails(sqlite_database):
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)
    with engine.begin() as connection:
        connection.execute(
            CreationMediaItem.__table__.insert().values(
                id='creation-1',
                user_id='user-1',
                kind='image',
                file_id='file-1',
                prompt='a calm river',
                task='text-to-image',
                source='web',
                batch_id='batch-1',
                params_json={'n': 1, 'size': '1024x1024'},
                reference_file_ids_json=['ref-1', 'ref-2'],
                created_at=10,
                updated_at=10,
            )
        )
        assert connection.execute(select(CreationMediaItem.params_json)).scalar_one() == {
            'n': 1,
            'size': '1024x1024',
        }
        assert connection.execute(select(CreationMediaItem.reference_file_ids_json)).scalar_one() == [
            'ref-1',
            'ref-2',
        ]

        with pytest.raises(IntegrityError):
            connection.execute(
                CreationMediaItem.__table__.insert().values(
                    id='creation-bad-kind',
                    user_id='user-1',
                    kind='video',
                    file_id='file-2',
                    prompt='p',
                    task='text-to-image',
                    source='web',
                    batch_id='batch-1',
                    created_at=10,
                    updated_at=10,
                )
            )


def test_server_defaults_apply_soft_deleted_false(sqlite_database):
    engine, _ = sqlite_database
    _upgrade_sqlite(engine)
    with engine.begin() as connection:
        connection.execute(
            CreationMediaItem.__table__.insert().values(
                id='creation-default',
                user_id='user-1',
                kind='image',
                file_id='file-default',
                prompt='p',
                task='text-to-image',
                source='web',
                batch_id='batch-1',
                created_at=1,
                updated_at=1,
            )
        )
        assert connection.execute(select(CreationMediaItem.soft_deleted)).scalar_one() is False


def test_production_adapter_identity():
    assert creation_db.engine is upstream_db.engine
    assert creation_db.async_engine is upstream_db.async_engine
    assert creation_db.AsyncSessionLocal is upstream_db.AsyncSessionLocal
    assert creation_db.JSONField is upstream_db.JSONField
    assert CreationBase.metadata.schema == upstream_env.DATABASE_SCHEMA


def test_upstream_head_missing_and_behind_fail_before_extension_ddl(sqlite_database):
    engine, _ = sqlite_database
    for revision in (None, 'not-current-head'):
        if revision:
            with engine.begin() as connection:
                connection.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)'))
                connection.execute(text('INSERT INTO alembic_version VALUES (:revision)'), {'revision': revision})
        with engine.connect() as connection, pytest.raises(RuntimeError, match='upstream Alembic'):
            run_creation_migrations(connection=connection, verify_upstream=True)
        with engine.connect() as connection:
            assert 'ext_creation_media_item' not in inspect(connection).get_table_names()
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

    monkeypatch.setattr('open_webui.extensions.creations.migrations.runner.MigrationContext', FakeMigrationContext)
    monkeypatch.setattr(
        'open_webui.extensions.creations.migrations.runner.ScriptDirectory.from_config',
        lambda config: SimpleNamespace(get_heads=lambda: ['head']),
    )
    monkeypatch.setattr('open_webui.extensions.creations.migrations.runner.DATABASE_SCHEMA', 'tenant')

    _validate_upstream_head(object())

    assert captured == {'version_table': 'alembic_version', 'version_table_schema': 'tenant'}


def test_external_transaction_is_rejected_before_lock(sqlite_database):
    engine, _ = sqlite_database
    with engine.connect() as connection:
        transaction = connection.begin()
        with pytest.raises(RuntimeError, match='active transaction'):
            run_creation_migrations(connection=connection, verify_upstream=False)
        transaction.rollback()


def test_sqlite_lock_timeout_without_sleeping(monkeypatch, sqlite_database):
    engine, database_path = sqlite_database
    lock_path = Path(f'{database_path}.creation-migrations.lock')
    lock_path.touch()
    ticks = iter([0.0, 0.0, 20.0])
    monkeypatch.setattr('open_webui.extensions.creations.migrations.runner.time.monotonic', lambda: next(ticks))
    monkeypatch.setattr('open_webui.extensions.creations.migrations.runner.time.sleep', lambda _: None)
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
    monkeypatch.setattr('open_webui.extensions.creations.migrations.runner.time.monotonic', lambda: next(ticks))
    monkeypatch.setattr('open_webui.extensions.creations.migrations.runner.time.sleep', lambda _: None)
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

    monkeypatch.setattr('open_webui.extensions.creations.migrations.runner._upgrade', upgrade)
    connection = FakeConnection()
    _run_postgres_migration(connection, verify_upstream=False, schema='tenant')

    assert events == ['acquire', 'commit', 'upgrade', 'commit', 'release', 'commit']
    assert not connection.in_transaction()


def test_migration_error_remains_primary_when_release_also_fails(monkeypatch, sqlite_database):
    engine, _ = sqlite_database
    monkeypatch.setattr(
        'open_webui.extensions.creations.migrations.runner._acquire_database_lock', lambda connection: object()
    )

    def fail_upgrade(*args, **kwargs):
        raise ValueError('migration failed')

    def fail_release(*args, **kwargs):
        raise RuntimeError('release failed')

    monkeypatch.setattr('open_webui.extensions.creations.migrations.runner._upgrade', fail_upgrade)
    monkeypatch.setattr('open_webui.extensions.creations.migrations.runner._release_database_lock', fail_release)
    with engine.connect() as connection, pytest.raises(ValueError, match='migration failed'):
        run_creation_migrations(connection=connection, verify_upstream=False)


def test_dynamic_schema_context_options_are_behavioral():
    tenant_options = migration_context_options('tenant', CreationBase.metadata)
    assert tenant_options == {
        'target_metadata': CreationBase.metadata,
        'version_table': 'ext_creation_schema_version',
        'version_table_schema': 'tenant',
        'include_schemas': True,
    }
    default_options = migration_context_options(None, CreationBase.metadata)
    assert default_options['version_table_schema'] is None
    assert default_options['include_schemas'] is False
    assert default_options['target_metadata'] is CreationBase.metadata


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
    return {table.name: table.to_metadata(metadata, schema=schema) for table in (CreationMediaItem.__table__,)}


@pytest.mark.skipif(
    not os.getenv('TEST_POSTGRES_DATABASE_URL'),
    reason='TEST_POSTGRES_DATABASE_URL is not set; PostgreSQL migration tests skipped',
)
def test_postgresql_non_public_schema_concurrent_migrations_and_constraints():
    engine = create_engine(os.environ['TEST_POSTGRES_DATABASE_URL'])
    schema = f'creation_test_{uuid4().hex}'
    try:
        with engine.connect() as connection:
            public_before = _schema_fingerprint(connection, 'public')
            connection.rollback()
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))

        def migrate() -> None:
            with engine.connect() as connection:
                run_creation_migrations(connection=connection, verify_upstream=False, schema=schema)
                assert not connection.in_transaction()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(migrate) for _ in range(2)]
            for future in futures:
                future.result()

        with engine.connect() as connection:
            inspector = inspect(connection)
            assert set(inspector.get_table_names(schema=schema)) == TABLE_NAMES | {'ext_creation_schema_version'}
            assert 'alembic_version' not in inspector.get_table_names(schema=schema)
            assert (
                connection.execute(text(f'SELECT version_num FROM "{schema}".ext_creation_schema_version')).scalar_one()
                == '0001_create_creation_media_item'
            )
            assert {
                index['name'] for index in inspector.get_indexes('ext_creation_media_item', schema=schema)
            } >= EXPECTED_INDEXES['ext_creation_media_item']
            for name in BIGINT_COLUMNS['ext_creation_media_item']:
                columns = {
                    column['name']: column for column in inspector.get_columns('ext_creation_media_item', schema=schema)
                }
                assert isinstance(columns[name]['type'], BigInteger)
            unique_names = {
                constraint['name']
                for constraint in inspector.get_unique_constraints('ext_creation_media_item', schema=schema)
            }
            assert unique_names >= {'uq_ext_creation_media_file'}
            assert inspector.get_foreign_keys('ext_creation_media_item', schema=schema) == []
            assert {
                constraint['name']
                for constraint in inspector.get_check_constraints('ext_creation_media_item', schema=schema)
            } >= EXPECTED_CHECKS
            defaults = {
                column['name']: str(column.get('default'))
                for column in inspector.get_columns('ext_creation_media_item', schema=schema)
            }
            assert defaults['soft_deleted'] not in {'None', ''}
            connection.rollback()

        tables = _postgres_tables(schema)
        with engine.begin() as connection:
            connection.execute(
                tables['ext_creation_media_item']
                .insert()
                .values(
                    id='creation',
                    user_id='user',
                    kind='image',
                    file_id='file',
                    prompt='p',
                    task='text-to-image',
                    source='web',
                    batch_id='batch',
                    created_at=1,
                    updated_at=1,
                )
            )
        with engine.connect() as connection:
            assert connection.execute(select(tables['ext_creation_media_item'].c.soft_deleted)).scalar_one() is False
            connection.rollback()

        invalid_rows = [
            {'id': 'bad-kind', 'kind': 'video'},
            {'id': 'bad-task', 'task': 'video-gen'},
            {'id': 'bad-source', 'source': 'mobile'},
        ]
        for values in invalid_rows:
            with engine.begin() as connection, pytest.raises(IntegrityError):
                connection.execute(
                    tables['ext_creation_media_item']
                    .insert()
                    .values(
                        user_id='user',
                        file_id=f'{values["id"]}-file',
                        prompt='p',
                        source='web',
                        task='text-to-image',
                        kind='image',
                        batch_id='batch',
                        created_at=1,
                        updated_at=1,
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


def test_async_creation_session_uses_upstream_factory(monkeypatch):
    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    def factory():
        return FakeSession()

    monkeypatch.setattr('open_webui.extensions.creations.db.AsyncSessionLocal', factory)

    async def exercise():
        async with creation_session() as session:
            assert isinstance(session, FakeSession)

    asyncio.run(exercise())
