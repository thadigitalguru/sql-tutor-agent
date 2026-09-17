from app.sandbox.executor import run_sql
from app.sandbox.safety import SqlSafetyError, validate_sql


def test_rejects_empty_query() -> None:
    try:
        validate_sql("   ", max_chars=100)
        raise AssertionError("expected safety error")
    except SqlSafetyError as exc:
        assert exc.error_type == "syntax"


def test_rejects_multiple_statements() -> None:
    try:
        validate_sql("SELECT 1; DROP TABLE customers", max_chars=10_000)
        raise AssertionError("expected safety error")
    except SqlSafetyError:
        pass


def test_rejects_drop_as_primary() -> None:
    try:
        validate_sql("DROP TABLE customers", max_chars=10_000)
        raise AssertionError("expected safety error")
    except SqlSafetyError:
        pass


def test_rejects_attach() -> None:
    result = run_sql("ATTACH DATABASE 'evil.db' AS e", dataset_id="ecommerce")
    assert result.ok is False
    assert result.error_type in {"unsafe", "syntax"}


def test_rejects_pragma() -> None:
    result = run_sql("PRAGMA query_only = OFF", dataset_id="ecommerce")
    assert result.ok is False


def test_rejects_load_extension() -> None:
    result = run_sql("SELECT load_extension('x')", dataset_id="ecommerce")
    assert result.ok is False


def test_rejects_comment_hidden_second_statement() -> None:
    result = run_sql("SELECT 1; -- ok\nDELETE FROM customers", dataset_id="ecommerce")
    assert result.ok is False


def test_allows_select_and_with() -> None:
    validate_sql("SELECT name FROM customers", max_chars=10_000)
    validate_sql(
        "WITH paid AS (SELECT * FROM orders WHERE status = 'paid') SELECT COUNT(*) FROM paid",
        max_chars=10_000,
    )


def test_query_only_blocks_writes() -> None:
    result = run_sql("SELECT * FROM customers", dataset_id="ecommerce")
    assert result.ok
    # Even if parser slipped, the connection is query-only.
    sneaky = run_sql(
        "INSERT INTO customers (customer_id, name, country, signup_date) VALUES (99, 'x', 'x', '2024-01-01')",
        dataset_id="ecommerce",
    )
    assert sneaky.ok is False
