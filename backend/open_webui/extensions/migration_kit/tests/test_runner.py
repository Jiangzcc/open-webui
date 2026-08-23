"""共享迁移 runner 的机制测试（复盘 #13/#15）。

此前锁超时、PostgreSQL 事务顺序、上游 head 校验等行为分散在 credits 与
creations 两份近似拷贝的测试里（model_ops / provider_ops / prompt_tags 则
完全没有覆盖）；runner 收敛到 migration_kit 后机制测试统一在此维护，
各扩展仅保留 schema 形态测试。
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from open_webui.extensions.creations.migrations.runner import SPEC as CREATIONS_SPEC
from open_webui.extensions.credits.migrations.runner import SPEC as CREDITS_SPEC
from open_webui.extensions.migration_kit import migration_context_options, script_heads
from open_webui.extensions.migration_kit import runner as kit_runner
from open_webui.extensions.migration_kit.runner import (
    _acquire_postgres_lock,
    _acquire_sqlite_lock,
    _postgres_lock_key,
    _release_postgres_lock,
    _run_postgres_migration,
    _validate_upstream_head,
    run_extension_migrations,
)
from open_webui.extensions.migration_kit.spec import MigrationSpec
from open_webui.extensions.model_ops.migrations.runner import SPEC as MODEL_OPS_SPEC
from open_webui.extensions.prompt_tags.migrations.runner import SPEC as PROMPT_TAG_SPEC
from open_webui.extensions.provider_ops.migrations.runner import SPEC as PROVIDER_OPS_SPEC
from sqlalchemy import MetaData, create_engine, inspect

ALL_SPECS = [CREATIONS_SPEC, CREDITS_SPEC, PROVIDER_OPS_SPEC, MODEL_OPS_SPEC, PROMPT_TAG_SPEC]
EXPECTED_HEADS = {
    'creation': '0001_create_creation_tables',
    'credit': '0001_create_credit_tables',
    'provider ops': '0001_create_provider_ops_tables',
    'model ops': '0001_create_image_model_operations',
    'prompt tag': '0001_create_prompt_tag_library',
}


@pytest.fixture
def sqlite_database(tmp_path: Path):
    database_path = tmp_path / 'kit.sqlite'
    engine = create_engine(f'sqlite:///{database_path}')
    try:
        yield engine, database_path
    finally:
        engine.dispose()


def _synthetic_spec(engine, **overrides) -> MigrationSpec:
    defaults = dict(
        label='kit-test',
        migrations_dir=Path(__file__).parent,
        metadata=MetaData(),
        engine=engine,
        version_table='ext_kit_test_schema_version',
        schema_attribute='kit_test_schema',
        lock_namespace='open-webui-kit-test-migrations',
        sqlite_lock_suffix='kit-test-migrations.lock',
    )
    defaults.update(overrides)
    return MigrationSpec(**defaults)


def test_every_extension_chain_is_a_single_squashed_revision():
    """五个扩展的迁移链必须各自只有一个 0001 基线（复盘 #13 squash）。"""
    for spec in ALL_SPECS:
        heads = script_heads(spec)
        assert heads == {EXPECTED_HEADS[spec.label]}, spec.label


def test_stale_version_table_raises_actionable_error(sqlite_database):
    """squash 后存量库的版本表指向已删除 revision 时，报错须可自诊断。

    裸 Alembic CommandError（"Can't locate revision"）会让启动失败难以排查；
    _upgrade 需将其包装为带处置指引的 RuntimeError（审查发现 #3）。

    注：各扩展 env.py 绑定自己模块的 SPEC 常量，因此必须用真实 CREDITS_SPEC
    （其 version_table/metadata 才与 env.py 一致），不能用 synthetic spec。
    """
    engine, _ = sqlite_database
    from sqlalchemy import text

    with engine.connect() as connection:
        connection.execute(
            text(f'CREATE TABLE {CREDITS_SPEC.version_table} (version_num VARCHAR(32) NOT NULL)')
        )
        connection.execute(
            text(f"INSERT INTO {CREDITS_SPEC.version_table} (version_num) VALUES ('0009_stale_pre_squash_revision')")
        )
        connection.commit()
        try:
            run_extension_migrations(CREDITS_SPEC, connection=connection, verify_upstream=False)
        except RuntimeError as error:
            message = str(error)
            assert 'no longer exists' in message
            assert CREDITS_SPEC.version_table in message
            assert '0009_stale_pre_squash_revision' in message
        else:
            pytest.fail('expected RuntimeError for stale version table')
        finally:
            connection.rollback()


def test_lock_namespaces_are_distinct_across_extensions():
    """不同扩展的迁移锁必须互不冲突（Postgres advisory key / SQLite 文件名）。"""
    keys = [_postgres_lock_key(spec) for spec in ALL_SPECS]
    suffixes = {spec.sqlite_lock_suffix for spec in ALL_SPECS}
    assert len(set(keys)) == len(keys)
    assert len(suffixes) == len(ALL_SPECS)


def test_sqlite_lock_path_uses_extension_suffix_and_skips_memory(sqlite_database):
    engine, database_path = sqlite_database
    with engine.connect() as connection:
        spec = _synthetic_spec(engine)
        lock_path = kit_runner._sqlite_lock_path(spec, connection)
    assert lock_path.name.endswith('kit-test-migrations.lock')
    assert lock_path.parent == database_path.parent

    memory_engine = create_engine('sqlite://')
    try:
        with memory_engine.connect() as connection:
            assert kit_runner._sqlite_lock_path(_synthetic_spec(memory_engine), connection) is None
    finally:
        memory_engine.dispose()


def test_sqlite_lock_timeout_without_sleeping(monkeypatch, sqlite_database):
    engine, database_path = sqlite_database
    lock_path = Path(f'{database_path}.kit-test-migrations.lock')
    lock_path.touch()
    ticks = iter([0.0, 0.0, 20.0])
    monkeypatch.setattr('open_webui.extensions.migration_kit.runner.time.monotonic', lambda: next(ticks))
    monkeypatch.setattr('open_webui.extensions.migration_kit.runner.time.sleep', lambda _: None)
    try:
        with engine.connect() as connection, pytest.raises(TimeoutError, match='SQLite migration lock'):
            _acquire_sqlite_lock(_synthetic_spec(engine), connection)
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
    monkeypatch.setattr('open_webui.extensions.migration_kit.runner.time.monotonic', lambda: next(ticks))
    monkeypatch.setattr('open_webui.extensions.migration_kit.runner.time.sleep', lambda _: None)
    spec = _synthetic_spec(None)
    with pytest.raises(TimeoutError, match='PostgreSQL kit-test'):
        _acquire_postgres_lock(spec, FakeConnection([False, False]))

    release_connection = FakeConnection([True])
    _release_postgres_lock(release_connection, _postgres_lock_key(spec))
    assert _postgres_lock_key(spec) == int.from_bytes(
        __import__('hashlib').sha256(spec.lock_namespace.encode()).digest()[:8], 'big', signed=True
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

    def upgrade(spec, connection, verify_upstream, schema):
        events.append('upgrade')
        connection.active = True

    monkeypatch.setattr('open_webui.extensions.migration_kit.runner._upgrade', upgrade)
    connection = FakeConnection()
    _run_postgres_migration(_synthetic_spec(None), connection, verify_upstream=False, schema='tenant')

    assert events == ['acquire', 'commit', 'upgrade', 'commit', 'release', 'commit']
    assert not connection.in_transaction()


def test_migration_error_remains_primary_when_release_also_fails(monkeypatch, sqlite_database):
    engine, _ = sqlite_database
    spec = _synthetic_spec(engine)
    monkeypatch.setattr(
        'open_webui.extensions.migration_kit.runner._acquire_database_lock',
        lambda spec, connection: object(),
    )

    def fail_upgrade(*args, **kwargs):
        raise ValueError('migration failed')

    def fail_release(*args, **kwargs):
        raise RuntimeError('release failed')

    monkeypatch.setattr('open_webui.extensions.migration_kit.runner._upgrade', fail_upgrade)
    monkeypatch.setattr('open_webui.extensions.migration_kit.runner._release_database_lock', fail_release)
    with engine.connect() as connection, pytest.raises(ValueError, match='migration failed'):
        run_extension_migrations(spec, connection, verify_upstream=False)


def test_external_transaction_is_rejected_before_lock(sqlite_database):
    engine, _ = sqlite_database
    spec = _synthetic_spec(engine)
    with engine.connect() as connection:
        transaction = connection.begin()
        with pytest.raises(RuntimeError, match='active transaction'):
            run_extension_migrations(spec, connection, verify_upstream=False)
        transaction.rollback()


def test_upstream_head_missing_fails_before_extension_ddl(sqlite_database):
    """上游未到 head 时必须在执行任何扩展 DDL 前失败（对齐漂移修复 #15）。"""
    engine, _ = sqlite_database
    with engine.connect() as connection, pytest.raises(RuntimeError, match='upstream Alembic'):
        run_extension_migrations(MODEL_OPS_SPEC, connection, verify_upstream=True)
    with engine.connect() as connection:
        assert 'ext_image_model_operation' not in inspect(connection).get_table_names()
        assert 'alembic_version' not in inspect(connection).get_table_names()


def test_upstream_head_uses_upstream_version_table_and_schema(monkeypatch):
    captured = {}

    class FakeMigrationContext:
        @classmethod
        def configure(cls, connection, opts):
            captured.update(opts)
            return SimpleNamespace(get_current_heads=lambda: ('head',))

    monkeypatch.setattr('open_webui.extensions.migration_kit.runner.MigrationContext', FakeMigrationContext)
    monkeypatch.setattr(
        'open_webui.extensions.migration_kit.runner.ScriptDirectory.from_config',
        lambda config: SimpleNamespace(get_heads=lambda: ['head']),
    )
    monkeypatch.setattr('open_webui.extensions.migration_kit.runner.DATABASE_SCHEMA', 'tenant')

    _validate_upstream_head(object())

    assert captured == {'version_table': 'alembic_version', 'version_table_schema': 'tenant'}


def test_dynamic_schema_context_options_are_behavioral():
    metadata = MetaData()
    tenant_options = migration_context_options('ext_tenant_version', 'tenant', metadata)
    assert tenant_options == {
        'target_metadata': metadata,
        'version_table': 'ext_tenant_version',
        'version_table_schema': 'tenant',
        'include_schemas': True,
    }
    default_options = migration_context_options('ext_tenant_version', None, metadata)
    assert default_options['version_table_schema'] is None
    assert default_options['include_schemas'] is False
    assert default_options['target_metadata'] is metadata


def test_script_heads_reads_the_extension_versions_directory():
    assert script_heads(CREDITS_SPEC) == {'0001_create_credit_tables'}
