"""Isolated SQLite sandbox for learner SQL."""

from __future__ import annotations

import sqlite3
import time
from functools import lru_cache
from pathlib import Path

from app.config import settings
from app.domain import QueryResult
from app.sandbox.safety import SqlSafetyError, is_table_name_allowed, validate_sql

PREVIEW_MAX = 20


class DatasetError(FileNotFoundError):
    pass


class Sandbox:
    def __init__(self, datasets_dir: Path | None = None) -> None:
        self.datasets_dir = datasets_dir or settings.datasets_dir

    def dataset_path(self, dataset_id: str) -> Path:
        path = self.datasets_dir / dataset_id
        if not path.is_dir():
            raise DatasetError(f"Unknown dataset: {dataset_id}")
        return path

    def connect(self, dataset_id: str, *, variant: str | None = None) -> sqlite3.Connection:
        schema_sql, seed_sql = load_dataset_sql(self.datasets_dir, dataset_id, variant)
        conn = sqlite3.connect(":memory:", isolation_level=None, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA trusted_schema = OFF")
        conn.execute("PRAGMA recursive_triggers = OFF")
        try:
            conn.enable_load_extension(False)
        except AttributeError:
            pass
        conn.executescript(schema_sql)
        conn.executescript(seed_sql)
        conn.execute("PRAGMA query_only = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def table_names(self, dataset_id: str) -> set[str]:
        schema, _ = load_dataset_sql(self.datasets_dir, dataset_id, None)
        names: set[str] = set()
        with sqlite3.connect(":memory:") as conn:
            conn.executescript(schema)
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            names = {row[0] for row in rows}
        return names


@lru_cache(maxsize=32)
def load_dataset_sql(datasets_dir: Path, dataset_id: str, variant: str | None) -> tuple[str, str]:
    base = datasets_dir / dataset_id
    schema_path = base / "schema.sql"
    seed_name = "seed.sql" if not variant else f"seed_{variant}.sql"
    seed_path = base / seed_name
    if not schema_path.is_file():
        raise DatasetError(f"Dataset {dataset_id} is missing schema.sql")
    if not seed_path.is_file():
        raise DatasetError(f"Dataset {dataset_id} is missing {seed_name}")
    return schema_path.read_text(encoding="utf-8"), seed_path.read_text(encoding="utf-8")


def run_sql(
    query: str,
    *,
    dataset_id: str,
    sandbox: Sandbox | None = None,
    variant: str | None = None,
    max_rows: int | None = None,
    timeout_seconds: float | None = None,
    max_chars: int | None = None,
    privileged: bool = False,
) -> QueryResult:
    sandbox = sandbox or Sandbox()
    max_rows = max_rows if max_rows is not None else settings.sql_max_rows
    timeout_seconds = timeout_seconds if timeout_seconds is not None else settings.sql_timeout_seconds
    max_chars = max_chars if max_chars is not None else settings.sql_max_query_chars

    if not privileged:
        try:
            validate_sql(query, max_chars=max_chars)
        except SqlSafetyError as exc:
            return QueryResult(
                ok=False,
                error_type=exc.error_type,
                message=str(exc),
            )

    conn = sandbox.connect(dataset_id, variant=variant)
    started = time.perf_counter()

    def _progress() -> int:
        if (time.perf_counter() - started) > timeout_seconds:
            return 1
        return 0

    conn.set_progress_handler(_progress, 1000)
    try:
        cursor = conn.execute(query)
        raw_rows = cursor.fetchmany(max_rows + 1)
        columns = [desc[0] for desc in (cursor.description or [])]
        truncated = len(raw_rows) > max_rows
        rows = [_serialize_row(row, columns) for row in raw_rows[:max_rows]]
        elapsed_ms = (time.perf_counter() - started) * 1000
        return QueryResult(
            ok=True,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            elapsed_ms=round(elapsed_ms, 2),
            truncated=truncated,
        )
    except sqlite3.OperationalError as exc:
        message = str(exc)
        error_type = _classify_engine_error(message)
        return QueryResult(
            ok=False,
            error_type=error_type,
            message=message,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
    except sqlite3.Error as exc:
        return QueryResult(
            ok=False,
            error_type="runtime",
            message=str(exc),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
    finally:
        conn.set_progress_handler(None, 0)
        conn.close()


def preview_table_sql(table: str, limit: int) -> str:
    quoted = '"' + table.replace('"', "") + '"'
    return f"SELECT * FROM {quoted} LIMIT {int(limit)}"


def guarded_preview(
    table: str,
    *,
    dataset_id: str,
    allowed_tables: set[str] | None = None,
    limit: int = 5,
    sandbox: Sandbox | None = None,
) -> QueryResult:
    sandbox = sandbox or Sandbox()
    allowed = allowed_tables or sandbox.table_names(dataset_id)
    if not is_table_name_allowed(table, allowed):
        return QueryResult(
            ok=False,
            error_type="unsafe",
            message="That table is not part of the current exercise.",
        )
    safe_limit = max(1, min(int(limit), PREVIEW_MAX))
    canonical = next(name for name in allowed if name.lower() == table.lower())
    return run_sql(
        preview_table_sql(canonical, safe_limit),
        dataset_id=dataset_id,
        sandbox=sandbox,
        privileged=True,
    )


def _serialize_row(row: sqlite3.Row, columns: list[str]) -> list[object]:
    values = []
    for col in columns:
        value = row[col]
        if isinstance(value, bytes):
            values.append(value.decode("utf-8", errors="replace"))
        else:
            values.append(value)
    return values


def _classify_engine_error(message: str) -> str:
    lowered = message.lower()
    if "syntax" in lowered or "parse" in lowered or "malformed" in lowered:
        return "syntax"
    if "interrupted" in lowered or "cancelled" in lowered:
        return "timeout"
    return "runtime"
