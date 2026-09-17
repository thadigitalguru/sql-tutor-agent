"""Schema inspection against the active dataset."""

from __future__ import annotations

import sqlite3

from app.domain import ColumnDef, QueryResult, SchemaPayload
from app.sandbox.executor import Sandbox, guarded_preview


def get_schema(
    dataset_id: str,
    *,
    tables: list[str] | None = None,
    sandbox: Sandbox | None = None,
) -> SchemaPayload:
    sandbox = sandbox or Sandbox()
    conn = sandbox.connect(dataset_id)
    try:
        visible = _visible_tables(conn, tables)
        payload: dict[str, list[ColumnDef]] = {}
        for table in visible:
            payload[table] = _table_columns(conn, table)
        return SchemaPayload(dataset_id=dataset_id, tables=payload)
    finally:
        conn.close()


def preview_table(
    dataset_id: str,
    table: str,
    *,
    limit: int = 5,
    allowed_tables: list[str] | None = None,
    sandbox: Sandbox | None = None,
) -> QueryResult:
    sandbox = sandbox or Sandbox()
    allowed = set(allowed_tables) if allowed_tables else sandbox.table_names(dataset_id)
    return guarded_preview(
        table,
        dataset_id=dataset_id,
        allowed_tables=allowed,
        limit=limit,
        sandbox=sandbox,
    )


def _visible_tables(conn: sqlite3.Connection, tables: list[str] | None) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    all_names = [row[0] if not isinstance(row, sqlite3.Row) else row["name"] for row in rows]
    if not tables:
        return all_names
    wanted = {name.lower() for name in tables}
    return [name for name in all_names if name.lower() in wanted]


def _table_columns(conn: sqlite3.Connection, table: str) -> list[ColumnDef]:
    quoted = '"' + table.replace('"', "") + '"'
    rows = conn.execute(f"PRAGMA table_info({quoted})").fetchall()
    columns: list[ColumnDef] = []
    for row in rows:
        columns.append(
            ColumnDef(
                name=row["name"],
                type=row["type"] or "TEXT",
                nullable=not bool(row["notnull"]),
                primary_key=bool(row["pk"]),
            )
        )
    return columns
