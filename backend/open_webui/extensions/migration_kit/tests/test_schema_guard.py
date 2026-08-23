"""共享 SchemaGuard 的机制与端到端校验测试（注册表收敛）。

机制部分（缺表/版本漂移/缺约束/外键漂移）用 mock 驱动；端到端部分对 5 个
扩展在真实迁移后的 SQLite 库上跑各自的 guard，确保声明与迁移建出的对象
（含外键映射）完全一致。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from open_webui.extensions.migration_kit import schema_guard as guard_module
from open_webui.extensions.migration_kit.schema_guard import SchemaGuard, validate_schema
from open_webui.extensions.migration_kit.spec import MigrationSpec
from sqlalchemy import MetaData, create_engine


def _test_spec(engine) -> MigrationSpec:
    return MigrationSpec(
        label='kit-test',
        migrations_dir=Path(__file__).parent,
        metadata=MetaData(),
        engine=engine,
        version_table='ext_kit_test_schema_version',
        schema_attribute='kit_test_schema',
        lock_namespace='open-webui-kit-test-migrations',
        sqlite_lock_suffix='kit-test-migrations.lock',
    )


def _mock_inspector(monkeypatch, *, tables, checks=(), uniques=(), indexes=(), foreign_keys=None):
    inspector = MagicMock()
    inspector.get_table_names.return_value = list(tables)
    inspector.get_check_constraints.return_value = [{'name': name} for name in checks]
    inspector.get_unique_constraints.return_value = [{'name': name} for name in uniques]
    inspector.get_indexes.return_value = [{'name': name} for name in indexes]
    inspector.get_foreign_keys.return_value = foreign_keys or []
    connection = MagicMock()
    connection.__enter__.return_value = connection
    engine = MagicMock()
    engine.connect.return_value = connection
    monkeypatch.setattr(guard_module, 'inspect', lambda _connection: inspector)
    return engine


def test_guard_rejects_missing_tables_before_version_lookup(monkeypatch):
    engine = _mock_inspector(monkeypatch, tables=['ext_one'])
    guard = SchemaGuard(spec=_test_spec(engine), required_tables=frozenset({'ext_one', 'ext_two'}))

    with pytest.raises(RuntimeError, match='missing tables'):
        validate_schema(guard)


def test_guard_rejects_wrong_version_and_missing_named_objects(monkeypatch):
    engine = _mock_inspector(
        monkeypatch,
        tables=['ext_one'],
        checks=['ck_a'],
        uniques=['uq_a'],
        indexes=['ix_a'],
    )
    migration_context = MagicMock()
    migration_context.get_current_heads.return_value = ('old-version',)
    monkeypatch.setattr(guard_module.MigrationContext, 'configure', lambda *_a, **_k: migration_context)
    monkeypatch.setattr(guard_module, 'script_heads', lambda _spec: {'current-version'})

    guard = SchemaGuard(
        spec=_test_spec(engine),
        required_tables=frozenset({'ext_one'}),
        required_unique={'ext_one': frozenset({'uq_a', 'uq_missing'})},
        required_checks={'ext_one': frozenset({'ck_a'})},
        required_indexes={'ext_one': frozenset({'ix_a'})},
    )
    with pytest.raises(RuntimeError, match='expected version'):
        validate_schema(guard)

    migration_context.get_current_heads.return_value = ('current-version',)
    with pytest.raises(RuntimeError, match='missing unique constraints'):
        validate_schema(guard)


def test_guard_rejects_foreign_key_drift(monkeypatch):
    engine = _mock_inspector(monkeypatch, tables=['ext_one'], foreign_keys=[{'referred_table': 'ext_other'}])
    migration_context = MagicMock()
    migration_context.get_current_heads.return_value = ('current-version',)
    monkeypatch.setattr(guard_module.MigrationContext, 'configure', lambda *_a, **_k: migration_context)
    monkeypatch.setattr(guard_module, 'script_heads', lambda _spec: {'current-version'})
    guard = SchemaGuard(spec=_test_spec(engine), required_tables=frozenset({'ext_one'}), expected_foreign_keys={})

    with pytest.raises(RuntimeError, match='foreign keys'):
        validate_schema(guard)


def test_guard_skips_foreign_key_check_when_not_configured(monkeypatch):
    engine = _mock_inspector(monkeypatch, tables=['ext_one'], foreign_keys=[{'referred_table': 'ext_other'}])
    migration_context = MagicMock()
    migration_context.get_current_heads.return_value = ('current-version',)
    monkeypatch.setattr(guard_module.MigrationContext, 'configure', lambda *_a, **_k: migration_context)
    monkeypatch.setattr(guard_module, 'script_heads', lambda _spec: {'current-version'})
    guard = SchemaGuard(spec=_test_spec(engine), required_tables=frozenset({'ext_one'}))

    validate_schema(guard)


# --- 端到端：每个扩展的真实迁移链必须满足自己的 guard ------------------------


def _load_extension_cases():
    from open_webui.extensions.creations.migrations.runner import run_creation_migrations
    from open_webui.extensions.creations.registration import _SCHEMA_GUARD as creations_guard
    from open_webui.extensions.credits.migrations.runner import run_credit_migrations
    from open_webui.extensions.credits.registration import _SCHEMA_GUARD as credits_guard
    from open_webui.extensions.model_ops.migrations.runner import run_model_ops_migrations
    from open_webui.extensions.model_ops.registration import _SCHEMA_GUARD as model_ops_guard
    from open_webui.extensions.prompt_tags.migrations.runner import run_prompt_tag_migrations
    from open_webui.extensions.prompt_tags.registration import _SCHEMA_GUARD as prompt_tags_guard
    from open_webui.extensions.provider_ops.migrations.runner import run_provider_ops_migrations
    from open_webui.extensions.provider_ops.registration import _SCHEMA_GUARD as provider_ops_guard

    return [
        ('creations', run_creation_migrations, creations_guard),
        ('credits', run_credit_migrations, credits_guard),
        ('model_ops', run_model_ops_migrations, model_ops_guard),
        ('prompt_tags', run_prompt_tag_migrations, prompt_tags_guard),
        ('provider_ops', run_provider_ops_migrations, provider_ops_guard),
    ]


@pytest.mark.parametrize('label,migrate,guard', _load_extension_cases())
def test_real_migration_chain_satisfies_its_guard(label, migrate, guard, tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / f"{label}.sqlite"}')
    try:
        with engine.connect() as connection:
            migrate(connection, verify_upstream=False)
        test_guard = replace(
            guard,
            spec=replace(guard.spec, engine=engine),
        )
        validate_schema(test_guard)
    finally:
        engine.dispose()
