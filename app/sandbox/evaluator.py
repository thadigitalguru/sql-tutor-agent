"""Compare learner result sets to reference results. Never compare SQL text."""

from __future__ import annotations

from collections import Counter
from math import isfinite
from typing import Any

from app.domain import (
    Comparison,
    Evaluation,
    EvaluationSpec,
    Exercise,
    QueryResult,
    SubmissionStatus,
)
from app.sandbox.diagnostics import diagnose
from app.sandbox.executor import Sandbox, run_sql
from app.sandbox.quality import assess_quality

_NULL = object()


def evaluate_exercise(
    exercise: Exercise,
    query: str,
    *,
    sandbox: Sandbox | None = None,
) -> Evaluation:
    sandbox = sandbox or Sandbox()
    primary = evaluate_query(
        query,
        reference_sql=exercise.reference_sql,
        dataset_id=exercise.dataset,
        spec=exercise.evaluation,
        sandbox=sandbox,
    )

    variant_results: list[Evaluation] = []
    for variant in exercise.hidden_variants:
        variant_results.append(
            evaluate_query(
                query,
                reference_sql=exercise.reference_sql,
                dataset_id=exercise.dataset,
                spec=exercise.evaluation,
                sandbox=sandbox,
                variant=variant,
            )
        )

    hidden_total = len(variant_results)
    hidden_passed = sum(1 for item in variant_results if item.status in _SUCCESS)
    combined = _combine(primary, variant_results)
    combined.hidden_variants_total = hidden_total
    combined.hidden_variants_passed = hidden_passed
    combined.diagnostic_tags = diagnose(
        query,
        evaluation=combined,
        exercise=exercise,
        actual=None,
    )
    if combined.status in _SUCCESS:
        notes = assess_quality(query, exercise=exercise)
        combined.quality_notes = notes
        if notes:
            combined.status = SubmissionStatus.CORRECT_WITH_IMPROVEMENT
    return combined


def evaluate_query(
    query: str,
    *,
    reference_sql: str,
    dataset_id: str,
    spec: EvaluationSpec,
    sandbox: Sandbox | None = None,
    variant: str | None = None,
) -> Evaluation:
    sandbox = sandbox or Sandbox()
    actual = run_sql(query, dataset_id=dataset_id, sandbox=sandbox, variant=variant)
    if not actual.ok:
        status = (
            SubmissionStatus.SYNTAX_ERROR
            if actual.error_type == "syntax"
            else SubmissionStatus.UNSAFE
            if actual.error_type == "unsafe"
            else SubmissionStatus.RUNTIME_ERROR
        )
        return Evaluation(
            status=status,
            execution_ok=False,
            diagnostic_tags=diagnose(query, evaluation=None, exercise=None, actual=actual),
            engine_message=actual.message,
        )

    expected = run_sql(
        reference_sql,
        dataset_id=dataset_id,
        sandbox=sandbox,
        variant=variant,
        privileged=True,
        max_rows=10_000,
        timeout_seconds=5,
    )
    if not expected.ok:
        return Evaluation(
            status=SubmissionStatus.RUNTIME_ERROR,
            execution_ok=False,
            engine_message="Reference query failed. This is an instructor error.",
            diagnostic_tags=["reference_failure"],
        )

    comparison = compare_results(actual, expected, spec)
    status = _status_from_comparison(comparison, spec)
    return Evaluation(
        status=status,
        execution_ok=True,
        comparison=comparison,
        diagnostic_tags=[],
        engine_message=None,
    )


def compare_results(
    actual: QueryResult,
    expected: QueryResult,
    spec: EvaluationSpec,
) -> Comparison:
    notes: list[str] = []
    actual_cols = actual.columns
    expected_cols = expected.columns

    columns_match = True
    if spec.require_column_names:
        columns_match = [c.lower() for c in actual_cols] == [c.lower() for c in expected_cols]
        if not columns_match:
            notes.append("column_names")
    elif len(actual_cols) != len(expected_cols):
        columns_match = False
        notes.append("column_count")

    actual_rows = [_normalize_row(row, spec) for row in actual.rows]
    expected_rows = [_normalize_row(row, spec) for row in expected.rows]

    if not spec.duplicates_matter:
        actual_rows = _unique(actual_rows)
        expected_rows = _unique(expected_rows)

    duplicate_match = Counter(actual_rows) == Counter(expected_rows) or (not spec.duplicates_matter)
    values_match = Counter(actual_rows) == Counter(expected_rows)
    if spec.order_matters:
        order_match = actual_rows == expected_rows
        values_match = order_match
    else:
        order_match = True

    if not values_match:
        notes.append("values")
    if spec.order_matters and actual_rows != expected_rows and Counter(actual_rows) == Counter(expected_rows):
        notes.append("order")
        order_match = False

    return Comparison(
        row_count_expected=len(expected.rows),
        row_count_actual=len(actual.rows),
        columns_match=columns_match,
        values_match=values_match and columns_match
        if spec.require_column_names
        else values_match and (len(actual_cols) == len(expected_cols)),
        order_match=order_match,
        duplicate_match=duplicate_match,
        notes=notes,
    )


_SUCCESS = {SubmissionStatus.CORRECT, SubmissionStatus.CORRECT_WITH_IMPROVEMENT}


def _status_from_comparison(comparison: Comparison, spec: EvaluationSpec) -> SubmissionStatus:
    if comparison.values_match and comparison.columns_match and comparison.order_match:
        return SubmissionStatus.CORRECT
    if comparison.values_match and not comparison.columns_match and spec.require_column_names:
        return SubmissionStatus.PARTIALLY_CORRECT
    if (
        comparison.row_count_actual == comparison.row_count_expected
        and comparison.columns_match
        and not comparison.values_match
    ):
        return SubmissionStatus.INCORRECT
    if comparison.row_count_actual == 0 and comparison.row_count_expected > 0:
        return SubmissionStatus.INCORRECT
    if comparison.columns_match and comparison.row_count_actual != comparison.row_count_expected:
        return SubmissionStatus.PARTIALLY_CORRECT
    return SubmissionStatus.INCORRECT


def _combine(primary: Evaluation, variants: list[Evaluation]) -> Evaluation:
    if not variants:
        return primary
    if primary.status not in _SUCCESS:
        return primary
    failed = next((item for item in variants if item.status not in _SUCCESS), None)
    if failed is None:
        return primary
    failed.diagnostic_tags = list(dict.fromkeys([*primary.diagnostic_tags, "hidden_case", *failed.diagnostic_tags]))
    if failed.status in _SUCCESS:
        return primary
    if failed.status == SubmissionStatus.CORRECT:
        return primary
    # Learner passed the visible dataset but failed a hidden variant.
    failed.status = SubmissionStatus.INCORRECT
    notes = []
    if failed.comparison:
        notes = list(failed.comparison.notes)
        notes.append("hidden_variant")
        failed.comparison.notes = notes
    return failed


def _normalize_row(row: list[Any], spec: EvaluationSpec) -> tuple[Any, ...]:
    return tuple(_normalize_value(value, spec) for value in row)


def _normalize_value(value: Any, spec: EvaluationSpec) -> Any:
    if value is None:
        return _NULL
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            return value
        # Bucket floats into the configured tolerance so 10.0 == 10.0001.
        tick = spec.numeric_tolerance if spec.numeric_tolerance > 0 else 0.005
        return round(value / tick) * tick
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _unique(rows: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    seen: set[tuple[Any, ...]] = set()
    out: list[tuple[Any, ...]] = []
    for row in rows:
        if row not in seen:
            seen.add(row)
            out.append(row)
    return out
