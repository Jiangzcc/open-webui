"""ORM ↔ 迁移一致性测试（审查发现 #8）。

prompt_tags 的服务测试用 ``PromptTagBase.metadata.create_all`` 建表、绕过
真实迁移链；本文件通过真实 ``run_prompt_tag_migrations`` 升级 SQLite 库，
对照 ORM metadata 与迁移产物（表、列、索引、唯一约束、CHECK），防止
「测试全绿但 registration.py 启动校验直接拒绝启动」的漂移。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from open_webui.extensions.prompt_tags import models as _models  # noqa: F401 - 注册 ORM 表
from open_webui.extensions.prompt_tags import registration
from open_webui.extensions.prompt_tags.db import PromptTagBase
from open_webui.extensions.prompt_tags.migrations.runner import run_prompt_tag_migrations
from sqlalchemy import create_engine, inspect, text

TABLE_NAMES = set(PromptTagBase.metadata.tables)


@pytest.fixture
def sqlite_engine(tmp_path: Path):
    engine = create_engine(f'sqlite:///{tmp_path / "prompt-tags.sqlite"}')
    try:
        yield engine
    finally:
        engine.dispose()


def _upgrade(engine) -> None:
    with engine.connect() as connection:
        run_prompt_tag_migrations(connection=connection, verify_upstream=False)
        assert not connection.in_transaction()


def test_migration_creates_exactly_the_orm_tables(sqlite_engine) -> None:
    _upgrade(sqlite_engine)
    inspector = inspect(sqlite_engine)

    assert set(inspector.get_table_names()) == TABLE_NAMES | {'ext_prompt_tag_schema_version'}
    with sqlite_engine.connect() as connection:
        assert connection.execute(
            text('SELECT version_num FROM ext_prompt_tag_schema_version')
        ).scalar_one() == '0001_create_prompt_tag_library'


def test_orm_metadata_matches_migrated_schema(sqlite_engine) -> None:
    _upgrade(sqlite_engine)
    inspector = inspect(sqlite_engine)

    for table_name in TABLE_NAMES:
        model_table = PromptTagBase.metadata.tables[table_name]
        assert set(model_table.columns.keys()) == {
            column['name'] for column in inspector.get_columns(table_name)
        }, table_name
        assert {index.name for index in model_table.indexes} == {
            index['name'] for index in inspector.get_indexes(table_name)
        }, table_name
        assert {constraint.name for constraint in model_table.constraints if constraint.name} >= {
            constraint['name']
            for constraint in inspector.get_unique_constraints(table_name)
        }, table_name


def test_migration_registers_every_runtime_guard(sqlite_engine) -> None:
    """registration.py 的启动校验清单必须覆盖迁移实际建出的对象。"""
    _upgrade(sqlite_engine)
    inspector = inspect(sqlite_engine)

    unique_names = {
        table_name: {constraint['name'] for constraint in inspector.get_unique_constraints(table_name)}
        for table_name in TABLE_NAMES
    }
    index_names = {
        table_name: {index['name'] for index in inspector.get_indexes(table_name)}
        for table_name in TABLE_NAMES
    }
    check_names = {
        table_name: {constraint['name'] for constraint in inspector.get_check_constraints(table_name)}
        for table_name in TABLE_NAMES
    }

    for table_name, required in registration._REQUIRED_UNIQUE.items():
        assert required <= unique_names[table_name], table_name
    for table_name, required in registration._REQUIRED_INDEXES.items():
        assert required <= index_names[table_name], table_name
    for table_name, required in registration._REQUIRED_CHECKS.items():
        assert required <= check_names[table_name], table_name
    assert registration._REQUIRED_TABLES == frozenset(TABLE_NAMES)


def test_migration_seeds_builtin_catalog(sqlite_engine) -> None:
    _upgrade(sqlite_engine)

    with sqlite_engine.connect() as connection:
        categories = connection.execute(text('SELECT COUNT(*) FROM ext_prompt_tag_category')).scalar_one()
        tags = connection.execute(text('SELECT COUNT(*) FROM ext_prompt_tag')).scalar_one()

    assert categories >= 9
    assert tags >= 40
