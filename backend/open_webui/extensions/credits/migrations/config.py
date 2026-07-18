from __future__ import annotations

from typing import Any

from sqlalchemy import MetaData


def migration_context_options(schema: str | None, target_metadata: MetaData) -> dict[str, Any]:
    """Return schema-consistent Alembic configuration for the credit chain."""
    return {
        'target_metadata': target_metadata,
        'version_table': 'ext_credit_schema_version',
        'version_table_schema': schema,
        'include_schemas': schema is not None,
    }
