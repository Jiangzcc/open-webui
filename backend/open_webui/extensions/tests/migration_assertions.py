from __future__ import annotations

from sqlalchemy import inspect, text


def sqlite_upstream_fingerprint(connection) -> list[tuple[object, ...]]:
    rows = connection.execute(
        text(
            'SELECT type, name, tbl_name, sql FROM sqlite_master '
            "WHERE name = 'user' OR tbl_name = 'user' ORDER BY type, name"
        )
    ).fetchall()
    return [(row.type, row.name, row.tbl_name, row.sql) for row in rows]


def schema_fingerprint(connection, schema: str) -> dict[str, object]:
    """Capture non-extension schema structure before an isolated migration run."""
    inspector = inspect(connection)
    fingerprint: dict[str, object] = {}
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


__all__ = ['schema_fingerprint', 'sqlite_upstream_fingerprint']
