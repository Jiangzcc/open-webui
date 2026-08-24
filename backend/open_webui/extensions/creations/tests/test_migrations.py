from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from open_webui import env as upstream_env
from open_webui.extensions.creations import db as creation_db
from open_webui.extensions.creations.db import CreationBase
from open_webui.extensions.creations.migrations.runner import run_creation_migrations
from open_webui.extensions.creations.models import CreationMediaItem
from open_webui.extensions.tests.migration_assertions import schema_fingerprint, sqlite_upstream_fingerprint
from open_webui.internal import db as upstream_db
from sqlalchemy import BigInteger, CheckConstraint, MetaData, Table, Text, create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError

TABLE_NAMES = {
    'ext_creation_media_item',
    'ext_creation_post',
    'ext_creation_post_media',
    'ext_creation_post_reaction',
    'ext_image_generation_task',
    'ext_video_generation_task',
    'ext_creation_category',
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
        'ix_ext_creation_post_status_category',
        'ix_ext_creation_post_status_featured',
    },
    'ext_creation_post_media': {'ix_ext_creation_post_media_creation'},
    'ext_creation_post_reaction': {'ix_ext_creation_post_reaction_user_kind'},
    'ext_image_generation_task': {
        'ix_ext_image_task_user_created',
        'ix_ext_image_task_status_updated',
    },
    'ext_video_generation_task': {
        'ix_ext_video_task_user_created',
        'ix_ext_video_task_status_updated',
    },
    'ext_creation_category': {'ix_ext_creation_category_enabled_order'},
}
EXPECTED_CHECKS = {
    'ck_ext_creation_media_kind',
    'ck_ext_creation_media_task',
    'ck_ext_creation_media_source',
    'ck_ext_creation_media_duration',
    'ck_ext_creation_post_status',
    'ck_ext_creation_post_like_count',
    'ck_ext_creation_post_favorite_count',
    'ck_ext_creation_post_featured_rank',
    'ck_ext_creation_post_reaction_kind',
    'ck_ext_image_task_status',
    'ck_ext_image_task_kind',
    'ck_ext_image_task_expected_count',
    'ck_ext_video_task_status',
    'ck_ext_video_task_kind',
    'ck_ext_video_task_execution_mode',
    'ck_ext_video_task_delivery_attempts',
    'ck_ext_creation_category_sort_order',
}
BIGINT_COLUMNS = {
    'ext_creation_media_item': {'created_at', 'updated_at'},
    'ext_creation_post': {'published_at', 'featured_at', 'created_at', 'updated_at'},
    'ext_creation_post_media': {'created_at'},
    'ext_creation_post_reaction': {'created_at'},
    'ext_image_generation_task': {'created_at', 'started_at', 'completed_at', 'updated_at'},
    'ext_video_generation_task': {'created_at', 'started_at', 'completed_at', 'updated_at'},
    'ext_creation_category': {'updated_at'},
}
TEXT_COLUMNS = {'ext_creation_media_item': {'prompt', 'negative_prompt'}}


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
        before = sqlite_upstream_fingerprint(connection)

    _upgrade_sqlite(engine)

    with engine.connect() as connection:
        assert sqlite_upstream_fingerprint(connection) == before
        names = set(inspect(connection).get_table_names())
        assert names == {'user', *TABLE_NAMES, 'ext_creation_schema_version'}
        assert 'alembic_version' not in names
        assert connection.execute(text('SELECT version_num FROM ext_creation_schema_version')).scalar_one() == (
            '0001_create_creation_tables'
        )
        assert connection.execute(
            text('SELECT id, display_name, enabled, sort_order FROM ext_creation_category ORDER BY sort_order')
        ).fetchall() == [
            ('portrait', 'Portrait', 1, 10),
            ('product', 'Product', 1, 20),
            ('poster', 'Poster', 1, 30),
            ('illustration', 'Illustration', 1, 40),
            ('anime', 'Anime', 1, 50),
            ('landscape', 'Landscape', 1, 60),
            ('other', 'Other', 1, 999),
        ]
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
    assert media_unique >= {'uq_ext_creation_post_media_creation'}
    # post_media(post_id,position) 与 reaction(post_id,user_id,kind) 的唯一性
    # 由复合主键保证；不再声明同列 UNIQUE（PostgreSQL 渲染时会与 PK 合并）。
    assert inspector.get_pk_constraint('ext_creation_post_media')['constrained_columns'] == [
        'post_id',
        'position',
    ]
    assert inspector.get_pk_constraint('ext_creation_post_reaction')['constrained_columns'] == [
        'post_id',
        'user_id',
        'kind',
    ]
    task_unique = {constraint['name'] for constraint in inspector.get_unique_constraints('ext_image_generation_task')}
    assert task_unique >= {'uq_ext_image_task_user_key'}
    image_task_columns = {
        column['name']: column for column in inspector.get_columns('ext_image_generation_task')
    }
    assert image_task_columns['payload_sha256']['nullable'] is False
    video_task_unique = {
        constraint['name'] for constraint in inspector.get_unique_constraints('ext_video_generation_task')
    }
    assert video_task_unique >= {'uq_ext_video_task_user_key'}

    existing_checks = set()
    for table_name in TABLE_NAMES:
        existing_checks.update(constraint['name'] for constraint in inspector.get_check_constraints(table_name))
    assert existing_checks >= EXPECTED_CHECKS
    assert 'ck_ext_creation_post_category' not in existing_checks

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
        # 复盘 P1 回归守卫：ORM 与迁移的 CHECK 约束名称集合必须一致——
        # 此前 ck_ext_video_task_execution_mode/delivery_attempts 只存在于
        # 迁移（ORM 建表路径漏掉，create_all 与生产 schema 分叉）。
        orm_checks = {
            constraint.name for constraint in model_table.constraints if isinstance(constraint, CheckConstraint)
        }
        migrated_checks = {constraint['name'] for constraint in inspector.get_check_constraints(table_name)}
        assert orm_checks == migrated_checks, (table_name, orm_checks, migrated_checks)
        for name in BIGINT_COLUMNS[table_name]:
            assert isinstance(model_table.c[name].type, BigInteger)
        migrated_columns = {column['name']: column['type'] for column in inspector.get_columns(table_name)}
        for name, column in model_table.c.items():
            if isinstance(column.type, upstream_db.JSONField):
                # 复盘 P0-1 回归守卫：ORM 的 JSONField 是 TEXT 打底的 TypeDecorator，
                # 迁移若误用 sa.JSON 建列，PostgreSQL 上 psycopg3 会把 json 列解析成
                # dict，JSONField.process_result_value 对 dict 调 json.loads 即抛
                # TypeError（视频任务任何读取 500）。单测用 create_all 按 ORM 建表，
                # 与迁移建表的生产 schema 分叉，此前测不到——这里以迁移产物为准，
                # 断言所有 ORM JSON 列必须落成 TEXT。
                assert str(migrated_columns[name]).upper() == 'TEXT', (
                    table_name,
                    name,
                    str(migrated_columns[name]),
                )
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
    assert creation_db.creation_session is upstream_db.get_async_db
    assert creation_db.get_creation_session is upstream_db.get_async_session
    assert CreationBase.metadata.schema == upstream_env.DATABASE_SCHEMA


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
            public_before = schema_fingerprint(connection, 'public')
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
                == '0001_create_creation_tables'
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
            assert schema_fingerprint(connection, 'public') == public_before
            connection.rollback()
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        engine.dispose()
