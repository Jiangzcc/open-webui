"""Add sync-run heartbeat and an atomic running guard.

Revision ID: 0004_add_sync_run_heartbeat_and_guard
Revises: 0003_add_authoritative_requests_and_billing
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0004_add_sync_run_heartbeat_and_guard'
down_revision: str | None = '0003_add_authoritative_requests_and_billing'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('provider_ops_schema')


def upgrade() -> None:
    schema = _current_schema()
    op.add_column(
        'ext_provider_sync_run',
        sa.Column('heartbeat_at', sa.BigInteger(), nullable=True),
        schema=schema,
    )

    sync_run = sa.table(
        'ext_provider_sync_run',
        sa.column('id', sa.String(128)),
        sa.column('provider', sa.String(64)),
        sa.column('status', sa.String(16)),
        sa.column('error_code', sa.String(64)),
        sa.column('started_at', sa.BigInteger()),
        sa.column('heartbeat_at', sa.BigInteger()),
        sa.column('completed_at', sa.BigInteger()),
        schema=schema,
    )
    ranked = (
        sa.select(
            sync_run.c.id,
            sa.func.row_number()
            .over(
                partition_by=sync_run.c.provider,
                order_by=(sync_run.c.started_at.desc(), sync_run.c.id.desc()),
            )
            .label('position'),
        )
        .where(sync_run.c.status == 'running')
        .subquery()
    )
    # 升级前若已存在重复 running 行，保留最新一条，其余标记失败后再创建唯一索引。
    op.execute(
        sa.update(sync_run)
        .where(sync_run.c.id.in_(sa.select(ranked.c.id).where(ranked.c.position > 1)))
        .values(
            status='failed',
            error_code='provider_sync_superseded',
            completed_at=sa.func.coalesce(sync_run.c.completed_at, sync_run.c.started_at),
        )
    )
    op.execute(sa.update(sync_run).where(sync_run.c.status == 'running').values(heartbeat_at=sync_run.c.started_at))
    op.create_index(
        'ux_ext_provider_sync_run_running',
        'ext_provider_sync_run',
        ['provider'],
        unique=True,
        schema=schema,
        postgresql_where=sa.text("status = 'running'"),
        sqlite_where=sa.text("status = 'running'"),
    )


def downgrade() -> None:
    schema = _current_schema()
    op.drop_index(
        'ux_ext_provider_sync_run_running',
        table_name='ext_provider_sync_run',
        schema=schema,
    )
    op.drop_column('ext_provider_sync_run', 'heartbeat_at', schema=schema)
