"""Defense-in-depth validation for untrusted learner SQL."""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

ALLOWED_ROOT_TYPES = (exp.Select, exp.Union, exp.Except, exp.Intersect, exp.With)

FORBIDDEN_NODE_TYPES = (
    exp.Drop,
    exp.Delete,
    exp.Insert,
    exp.Update,
    exp.Create,
    exp.Alter,
    exp.Command,
    exp.Transaction,
    exp.Grant,
    exp.Set,
    exp.Use,
    exp.Pragma,
    exp.Analyze,
    exp.Copy,
    exp.Merge,
    exp.TruncateTable if hasattr(exp, "TruncateTable") else exp.Drop,
)

FORBIDDEN_FUNCTIONS = {
    "load_extension",
    "readfile",
    "writefile",
    "eval",
    "sqlite_compileoption_get",
    "sqlite_compileoption_used",
    "sqlite_offset",
    "sqlite_source_id",
    "fullfsync",
    "charindex",
}

FORBIDDEN_TEXT = re.compile(
    r"\b(attach|detach|pragma|vacuum|reindex|load_extension|readfile|writefile|"
    r"into\s+outfile|copy\s+|exec\s+|xp_)\b",
    re.IGNORECASE,
)

MAX_RECURSIVE_CTES = 1
MAX_UNION_DEPTH = 8


class SqlSafetyError(ValueError):
    def __init__(self, message: str, *, error_type: str = "unsafe") -> None:
        super().__init__(message)
        self.error_type = error_type


def validate_sql(query: str, *, max_chars: int) -> exp.Expression:
    if query is None or not str(query).strip():
        raise SqlSafetyError("Write a SQL query first.", error_type="syntax")

    text = query.strip()
    if len(text) > max_chars:
        raise SqlSafetyError(
            f"Query exceeds the {max_chars} character limit.",
            error_type="unsafe",
        )

    if "\x00" in text:
        raise SqlSafetyError("Query contains a null byte.", error_type="unsafe")

    if FORBIDDEN_TEXT.search(_strip_strings(text)):
        raise SqlSafetyError(
            "That statement is not allowed in this learning sandbox.",
            error_type="unsafe",
        )

    try:
        statements = sqlglot.parse(text, dialect="sqlite")
    except sqlglot.errors.ParseError as exc:
        raise SqlSafetyError(
            "The query could not be parsed. Check SQL syntax.",
            error_type="syntax",
        ) from exc

    statements = [stmt for stmt in statements if stmt is not None]
    if not statements:
        raise SqlSafetyError("No SQL statement found.", error_type="syntax")
    if len(statements) != 1:
        raise SqlSafetyError(
            "Only one SQL statement is allowed. Remove extra semicolons.",
            error_type="unsafe",
        )

    tree = statements[0]
    _assert_read_only(tree)
    return tree


def _assert_read_only(tree: exp.Expression) -> None:
    if not isinstance(tree, ALLOWED_ROOT_TYPES):
        raise SqlSafetyError(
            "Only SELECT queries (including WITH / UNION) are allowed.",
            error_type="unsafe",
        )

    for node in tree.walk():
        if isinstance(node, FORBIDDEN_NODE_TYPES):
            raise SqlSafetyError(
                "Only SELECT queries (including WITH / UNION) are allowed.",
                error_type="unsafe",
            )
        if isinstance(node, exp.Anonymous):
            name = (node.this or "").lower()
            if name in FORBIDDEN_FUNCTIONS:
                raise SqlSafetyError(
                    f"Function {name} is not allowed in the sandbox.",
                    error_type="unsafe",
                )
        if isinstance(node, exp.Func):
            name = type(node).__name__.lower()
            sql_name = (node.sql_name() if hasattr(node, "sql_name") else name).lower()
            if sql_name in FORBIDDEN_FUNCTIONS or name in FORBIDDEN_FUNCTIONS:
                raise SqlSafetyError(
                    f"Function {sql_name} is not allowed in the sandbox.",
                    error_type="unsafe",
                )

    recursive_ctes = [
        cte
        for cte in tree.find_all(exp.CTE)
        if cte.args.get("recursive") or (cte.parent and getattr(cte.parent, "recursive", False))
    ]
    with_node = tree.find(exp.With) or (tree if isinstance(tree, exp.With) else None)
    if with_node and getattr(with_node, "recursive", False):
        recursive_ctes.append(with_node)
    if tree.args.get("with") and getattr(tree.args["with"], "recursive", False):
        # Recursive CTEs are allowed but will be bounded by the executor timeout.
        pass

    union_count = sum(1 for _ in tree.find_all(exp.Union))
    if union_count > MAX_UNION_DEPTH:
        raise SqlSafetyError(
            "This query is too complex for the learning sandbox.",
            error_type="unsafe",
        )


def _strip_strings(sql: str) -> str:
    """Remove quoted literals so keyword scans do not match string contents."""
    return re.sub(r"('([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\")", "''", sql)


def is_table_name_allowed(table: str, allowed: set[str]) -> bool:
    return table.lower() in {name.lower() for name in allowed}
