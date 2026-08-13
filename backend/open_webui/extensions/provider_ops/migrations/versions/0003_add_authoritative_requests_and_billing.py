"""Add authoritative provider request records and billing events.

Revision ID: 0003_add_authoritative_requests_and_billing
Revises: 0002_add_platform_sync_tables
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0003_add_authoritative_requests_and_billing'
down_revision: str | None = '0002_add_platform_sync_tables'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('provider_ops_schema')


def upgrade() -> None:
    schema = _current_schema()
    op.create_table(
        'ext_provider_billing_event',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('provider_request_id', sa.String(128), nullable=False),
        sa.Column('provider_model_id', sa.String(256), nullable=False),
        sa.Column('event_timestamp', sa.String(64), nullable=False),
        sa.Column('event_at', sa.BigInteger(), nullable=False),
        sa.Column('api_key_id', sa.String(128), nullable=True),
        sa.Column('output_units', sa.String(64), nullable=True),
        sa.Column('unit_price', sa.String(64), nullable=True),
        sa.Column('percent_discount', sa.String(64), nullable=True),
        sa.Column('cost_subtotal', sa.String(64), nullable=False),
        sa.Column('cost_discount', sa.String(64), nullable=False),
        sa.Column('cost_total', sa.String(64), nullable=False),
        sa.Column('cost_nano_usd', sa.String(64), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('synced_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_request_id', name='uq_ext_provider_billing_event_request'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_billing_event_time',
        'ext_provider_billing_event',
        ['provider', 'event_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_billing_event_model_time',
        'ext_provider_billing_event',
        ['provider', 'provider_model_id', 'event_at', 'id'],
        schema=schema,
    )
    op.create_table(
        'ext_provider_request_record',
        sa.Column('id', sa.String(128), nullable=False),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('provider_request_id', sa.String(128), nullable=False),
        sa.Column('provider_model_id', sa.String(256), nullable=False),
        sa.Column('sent_at', sa.BigInteger(), nullable=False),
        sa.Column('started_at', sa.BigInteger(), nullable=False),
        sa.Column('ended_at', sa.BigInteger(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.BigInteger(), nullable=True),
        sa.Column('synced_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_request_id', name='uq_ext_provider_request_record_request'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_request_record_ended',
        'ext_provider_request_record',
        ['provider', 'ended_at', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_provider_request_record_model_ended',
        'ext_provider_request_record',
        ['provider', 'provider_model_id', 'ended_at', 'id'],
        schema=schema,
    )


def downgrade() -> None:
    schema = _current_schema()
    for table_name, indexes in (
        (
            'ext_provider_request_record',
            ('ix_ext_provider_request_record_model_ended', 'ix_ext_provider_request_record_ended'),
        ),
        (
            'ext_provider_billing_event',
            ('ix_ext_provider_billing_event_model_time', 'ix_ext_provider_billing_event_time'),
        ),
    ):
        for index_name in indexes:
            op.drop_index(index_name, table_name=table_name, schema=schema)
        op.drop_table(table_name, schema=schema)
