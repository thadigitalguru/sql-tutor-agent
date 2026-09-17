"""Layer 5 quality notes. Applied only after a query is already correct."""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

from app.domain import Exercise, QualityKind, QualityNote


def assess_quality(query: str, *, exercise: Exercise | None = None) -> list[QualityNote]:
    tree = _try_parse(query)
    if tree is None:
        return []
    notes = _notes_for(tree, query, exercise)
    if exercise:
        ref_tree = _try_parse(exercise.reference_sql)
        if ref_tree is not None:
            ref_tags = {item.tag for item in _notes_for(ref_tree, exercise.reference_sql, exercise)}
            notes = [item for item in notes if item.tag not in ref_tags]
    return _unique(notes)


def _notes_for(tree: exp.Expression, query: str, exercise: Exercise | None) -> list[QualityNote]:
    notes: list[QualityNote] = []
    skill = exercise.primary_skill if exercise else ""

    if tree.find(exp.Star):
        notes.append(
            QualityNote(
                kind=QualityKind.READABILITY,
                tag="select_star",
                message="SELECT * returns every column. Name only the columns the task needs.",
            )
        )

    select = tree.find(exp.Select)
    if select is not None and select.args.get("distinct"):
        notes.append(
            QualityNote(
                kind=QualityKind.PERFORMANCE,
                tag="select_distinct",
                message=(
                    "DISTINCT hides duplicate rows. If a join created extras, fix the join "
                    "instead of wrapping DISTINCT around the result."
                ),
            )
        )

    from_subqueries = [node for node in tree.find_all(exp.Subquery) if isinstance(node.parent, exp.From)]
    has_cte = tree.find(exp.CTE) is not None
    if from_subqueries and not has_cte:
        if skill == "cte":
            notes.append(
                QualityNote(
                    kind=QualityKind.READABILITY,
                    tag="missing_cte",
                    message=(
                        "This nested FROM subquery returns the right rows. Naming that step "
                        "with WITH ... AS (...) keeps the final SELECT easier to read."
                    ),
                )
            )
        elif len(from_subqueries) >= 2:
            notes.append(
                QualityNote(
                    kind=QualityKind.READABILITY,
                    tag="nested_subquery",
                    message="Stacked FROM (SELECT ...) subqueries are hard to follow. A CTE names each step.",
                )
            )

    if skill == "cte" and not has_cte:
        if not any(item.tag == "missing_cte" for item in notes):
            notes.append(
                QualityNote(
                    kind=QualityKind.READABILITY,
                    tag="missing_cte",
                    message=(
                        "The result is correct without a CTE. WITH ... AS (...) would match the "
                        "lesson and make the grouped step easier to reuse."
                    ),
                )
            )

    for select_node in tree.find_all(exp.Select):
        for expr in select_node.expressions:
            if isinstance(expr, exp.AggFunc):
                notes.append(
                    QualityNote(
                        kind=QualityKind.READABILITY,
                        tag="unaliased_aggregate",
                        message="Give aggregates an alias (SUM(amount) AS total) so the output is self-explanatory.",
                    )
                )
                break

    for join in tree.find_all(exp.Join):
        kind = str(join.args.get("kind") or "").upper()
        if kind == "CROSS":
            notes.append(
                QualityNote(
                    kind=QualityKind.PERFORMANCE,
                    tag="cartesian_join",
                    message=(
                        "This query uses a CROSS JOIN (including the old FROM a, b form). "
                        "Prefer an explicit JOIN ... ON so the match condition is visible and row explosion is avoided."
                    ),
                )
            )
            break

    if re.search(r"\bjoin\b", query, re.I) and not re.search(r"\bon\b", query, re.I):
        if not re.search(r"\bcross\s+join\b", query, re.I) and not any(item.tag == "cartesian_join" for item in notes):
            notes.append(
                QualityNote(
                    kind=QualityKind.PERFORMANCE,
                    tag="join_without_on",
                    message="A JOIN without ON is a cartesian product. Spell out the matching columns.",
                )
            )

    if re.search(r"like\s+['\"]%", query, re.I):
        notes.append(
            QualityNote(
                kind=QualityKind.PERFORMANCE,
                tag="leading_wildcard",
                message=(
                    "LIKE with a leading wildcard cannot use a normal index. Prefer a suffix "
                    "match or equality when the data allows it."
                ),
            )
        )

    if _or_equality_chain(query):
        notes.append(
            QualityNote(
                kind=QualityKind.READABILITY,
                tag="or_vs_in",
                message="A chain of OR equalities on one column is clearer as IN (...).",
            )
        )

    if _has_correlated_subquery(tree) and tree.find(exp.Exists) is None:
        notes.append(
            QualityNote(
                kind=QualityKind.PERFORMANCE,
                tag="correlated_subquery",
                message=(
                    "A correlated subquery runs once per outer row. A join or grouped CTE is "
                    "usually cheaper and easier to read."
                ),
            )
        )

    return notes


def _or_equality_chain(query: str) -> bool:
    return bool(re.search(r"(\b\w+\s*=\s*(?:'[^']*'|\d+)\s+or\s+){2,}\b\w+\s*=", query, re.I))


def _has_correlated_subquery(tree: exp.Expression) -> bool:
    outer_names = _table_names(tree, skip_subqueries=True)
    if not outer_names:
        return False
    for sub in tree.find_all(exp.Subquery):
        inner_names = _table_names(sub)
        for col in sub.find_all(exp.Column):
            table = (col.table or "").lower()
            if table and table in outer_names and table not in inner_names:
                return True
    return False


def _table_names(tree: exp.Expression, *, skip_subqueries: bool = False) -> set[str]:
    names: set[str] = set()
    for table in tree.find_all(exp.Table):
        if skip_subqueries and table.find_ancestor(exp.Subquery):
            continue
        if table.name:
            names.add(table.name.lower())
        if table.alias:
            names.add(str(table.alias).lower())
    return names


def _try_parse(query: str) -> exp.Expression | None:
    try:
        return sqlglot.parse_one(query, dialect="sqlite")
    except sqlglot.errors.ParseError:
        return None


def _unique(notes: list[QualityNote]) -> list[QualityNote]:
    seen: set[str] = set()
    out: list[QualityNote] = []
    for note in notes:
        if note.tag in seen:
            continue
        seen.add(note.tag)
        out.append(note)
    return out
