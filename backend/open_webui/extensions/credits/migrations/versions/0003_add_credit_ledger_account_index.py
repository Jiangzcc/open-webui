"""Add account_id index to ext_credit_ledger.

Revision ID: 0003_add_credit_ledger_account_index
Revises: 0002_add_reconciliation_guard
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0003_add_credit_ledger_account_index'
down_revision: str | None = '0002_add_reconciliation_guard'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('credit_schema')


def upgrade() -> None:
    op.create_index(
        'ix_ext_credit_ledger_account',
        'ext_credit_ledger',
        ['account_id'],
        schema=_current_schema(),
    )


def downgrade() -> None:
    op.drop_index(
        'ix_ext_credit_ledger_account',
        table_name='ext_credit_ledger',
        schema=_current_schema(),
    )
