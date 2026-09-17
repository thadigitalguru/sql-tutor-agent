"""Heuristic diagnostic tags. The LLM may explain them; it does not invent them."""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

from app.domain import Evaluation, Exercise, QueryResult, SubmissionStatus

KNOWN_TAGS = {
    "syntax",
    "unsafe",
    "timeout",
    "wrong_table",
    "wrong_column",
    "join_condition",
    "missing_join",
    "aggregation",
    "grouping",
    "filtering",
    "having_vs_where",
    "ordering",
    "duplicate_rows",
    "null_handling",
    "subquery_logic",
    "window_logic",
    "date_logic",
    "type_mismatch",
    "dialect_difference",
    "performance",
    "misread_requirement",
    "left_join_filter",
    "hidden_case",
}


def diagnose(
    query: str,
    *,
    evaluation: Evaluation | None,
    exercise: Exercise | None,
    actual: QueryResult | None,
) -> list[str]:
    tags: list[str] = []
    source = actual
    if source is None and evaluation and not evaluation.execution_ok:
        source = QueryResult(
            ok=False,
            error_type=_error_type_from_status(evaluation.status),
            message=evaluation.engine_message,
        )

    if source and not source.ok:
        if source.error_type == "syntax":
            tags.append("syntax")
        elif source.error_type == "unsafe":
            tags.append("unsafe")
        elif source.error_type == "timeout":
            tags.append("timeout")
        else:
            tags.extend(_runtime_tags(source.message or "", query))
        return _unique(tags)

    tree = _try_parse(query)
    if tree is None:
        return ["syntax"] if not tags else tags

    if evaluation and evaluation.comparison:
        comp = evaluation.comparison
        if not comp.order_match:
            tags.append("ordering")
        if not comp.duplicate_match:
            tags.append("duplicate_rows")
        if "column_names" in comp.notes or "column_count" in comp.notes:
            tags.append("misread_requirement")

    if exercise:
        tags.extend(_skill_tags(tree, query, exercise, evaluation))

    tags.extend(_query_pattern_tags(tree, query))
    return _unique(tags)


def _skill_tags(
    tree: exp.Expression,
    query: str,
    exercise: Exercise,
    evaluation: Evaluation | None,
) -> list[str]:
    tags: list[str] = []
    skill = exercise.primary_skill
    has_group = tree.find(exp.Group) is not None
    has_having = tree.find(exp.Having) is not None
    has_join = tree.find(exp.Join) is not None
    failed = evaluation is None or evaluation.status not in {
        SubmissionStatus.CORRECT,
        SubmissionStatus.CORRECT_WITH_IMPROVEMENT,
    }

    if not failed:
        return tags

    if skill in {"group_by", "having", "aggregate_sum", "aggregate_count"} and not has_group:
        if _has_aggregate(tree):
            tags.extend(["aggregation", "grouping"])
    if skill == "having" and has_group and not has_having:
        tags.append("having_vs_where")
    if skill in {"inner_join", "left_join"} and not has_join:
        tags.append("missing_join")
    if skill == "left_join" and has_join and _where_filters_right_table(query):
        tags.append("left_join_filter")
    if skill == "order_by" and tree.find(exp.Order) is None:
        tags.append("ordering")
    if skill == "null_handling" and " = null" in query.lower():
        tags.append("null_handling")
    return tags


def _query_pattern_tags(tree: exp.Expression, query: str) -> list[str]:
    tags: list[str] = []
    lowered = query.lower()
    if re.search(r"where\s+[^;]*\b(sum|count|avg|min|max)\s*\(", lowered):
        tags.append("having_vs_where")
    if re.search(r"=\s*null\b", lowered) or re.search(r"<>\s*null\b", lowered):
        tags.append("null_handling")
    if _has_aggregate(tree) and tree.find(exp.Group) is None and _selects_non_aggregate(tree):
        tags.extend(["aggregation", "grouping"])
    return tags


def _runtime_tags(message: str, query: str) -> list[str]:
    lowered = message.lower()
    tags: list[str] = []
    if "group by" in lowered or "not a result of aggregate" in lowered:
        tags.extend(["aggregation", "grouping"])
    if "misuse of aggregate" in lowered:
        tags.append("having_vs_where")
    if "no such column" in lowered:
        tags.append("wrong_column")
    if "no such table" in lowered:
        tags.append("wrong_table")
    if "ambiguous" in lowered:
        tags.append("join_condition")
    if "datatype" in lowered or "type" in lowered:
        tags.append("type_mismatch")
    if " = null" in query.lower():
        tags.append("null_handling")
    if not tags:
        tags.append("runtime")
    return tags


def _has_aggregate(tree: exp.Expression) -> bool:
    return any(isinstance(node, exp.AggFunc) for node in tree.walk())


def _selects_non_aggregate(tree: exp.Expression) -> bool:
    select = tree.find(exp.Select)
    if select is None:
        return False
    for expr in select.expressions:
        if not any(isinstance(node, exp.AggFunc) for node in expr.walk()):
            return True
    return False


def _where_filters_right_table(query: str) -> bool:
    return bool(re.search(r"where\s+\w+\.(status|order_id|total_amount|order_date)\b", query.lower()))


def _try_parse(query: str) -> exp.Expression | None:
    try:
        return sqlglot.parse_one(query, dialect="sqlite")
    except sqlglot.errors.ParseError:
        return None


def _error_type_from_status(status: SubmissionStatus) -> str:
    if status == SubmissionStatus.SYNTAX_ERROR:
        return "syntax"
    if status == SubmissionStatus.UNSAFE:
        return "unsafe"
    return "runtime"


def _unique(tags: list[str]) -> list[str]:
    out: list[str] = []
    for tag in tags:
        if tag not in out:
            out.append(tag)
    return out
