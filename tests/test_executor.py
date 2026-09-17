from app.sandbox.executor import run_sql
from app.sandbox.schema import get_schema, preview_table


def test_run_selects_rows() -> None:
    result = run_sql("SELECT customer_id, name FROM customers ORDER BY customer_id", dataset_id="ecommerce")
    assert result.ok
    assert result.row_count == 8
    assert result.columns == ["customer_id", "name"]
    assert result.rows[0][1] == "Amina Ochieng"


def test_preview_whitelist() -> None:
    ok = preview_table("ecommerce", "orders", limit=3)
    assert ok.ok
    assert ok.row_count == 3
    blocked = preview_table("ecommerce", "sqlite_master", limit=3)
    assert blocked.ok is False


def test_schema_contains_shipped_at() -> None:
    schema = get_schema("ecommerce", tables=["orders"])
    names = [col.name for col in schema.tables["orders"]]
    assert "shipped_at" in names
    assert "total_amount" in names


def test_unknown_column_is_runtime() -> None:
    result = run_sql("SELECT missing FROM customers", dataset_id="ecommerce")
    assert result.ok is False
    assert result.error_type == "runtime"


def test_row_cap_truncates() -> None:
    result = run_sql("SELECT 1 FROM orders", dataset_id="ecommerce", max_rows=2)
    assert result.ok
    assert result.row_count == 2
    assert result.truncated is True
