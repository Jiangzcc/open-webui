"""Add idempotent reconciliation compensation guard.

Revision ID: 0002_add_reconciliation_guard
Revises: 0001_create_credit_tables
"""

from collections.abc import Sequence

from alembic import op

revision: str = '0002_add_reconciliation_guard'
down_revision: str | None = '0001_create_credit_tables'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('credit_schema')


def upgrade() -> None:
    op.create_index(
        'ux_ext_credit_ledger_related_refund',
        'ext_credit_ledger',
        ['related_ledger_id'],
        unique=True,
        schema=_current_schema(),
    )


def downgrade() -> None:
    op.drop_index(
        'ux_ext_credit_ledger_related_refund',
        table_name='ext_credit_ledger',
        schema=_current_schema(),
    )
