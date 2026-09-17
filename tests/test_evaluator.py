from app.curriculum.loader import get_exercise
from app.domain import EvaluationSpec, QueryResult, SubmissionStatus
from app.sandbox.evaluator import compare_results, evaluate_exercise, evaluate_query


def _result(columns: list[str], rows: list[list[object]]) -> QueryResult:
    return QueryResult(ok=True, columns=columns, rows=rows, row_count=len(rows))


def test_multiset_ignores_order() -> None:
    spec = EvaluationSpec(order_matters=False)
    actual = _result(["id"], [[2], [1], [1]])
    expected = _result(["id"], [[1], [1], [2]])
    comparison = compare_results(actual, expected, spec)
    assert comparison.values_match
    assert comparison.order_match


def test_order_matters() -> None:
    spec = EvaluationSpec(order_matters=True)
    actual = _result(["id"], [[2], [1]])
    expected = _result(["id"], [[1], [2]])
    comparison = compare_results(actual, expected, spec)
    assert comparison.values_match is False
    assert comparison.order_match is False


def test_duplicates_preserved() -> None:
    spec = EvaluationSpec(order_matters=False, duplicates_matter=True)
    actual = _result(["id"], [[1], [1]])
    expected = _result(["id"], [[1]])
    assert compare_results(actual, expected, spec).values_match is False


def test_null_is_not_empty_string() -> None:
    spec = EvaluationSpec()
    actual = _result(["v"], [[None]])
    expected = _result(["v"], [[""]])
    assert compare_results(actual, expected, spec).values_match is False


def test_numeric_tolerance() -> None:
    spec = EvaluationSpec(numeric_tolerance=0.01)
    actual = _result(["n"], [[10.004]])
    expected = _result(["n"], [[10.0]])
    assert compare_results(actual, expected, spec).values_match


def test_alternate_group_by_passes() -> None:
    exercise = get_exercise("grp_001")
    evaluation = evaluate_exercise(
        exercise,
        """
        SELECT customer_id AS cid, SUM(total_amount) AS total
        FROM orders
        GROUP BY customer_id
        """,
    )
    assert evaluation.status == SubmissionStatus.CORRECT


def test_wrong_group_by_fails() -> None:
    exercise = get_exercise("grp_001")
    evaluation = evaluate_exercise(exercise, "SELECT customer_id, total_amount FROM orders")
    assert evaluation.status != SubmissionStatus.CORRECT


def test_having_where_mistake_is_runtime_or_incorrect() -> None:
    exercise = get_exercise("hav_001")
    evaluation = evaluate_exercise(
        exercise,
        """
        SELECT customer_id, SUM(total_amount)
        FROM orders
        WHERE SUM(total_amount) > 500
        GROUP BY customer_id
        """,
    )
    assert evaluation.status in {
        SubmissionStatus.RUNTIME_ERROR,
        SubmissionStatus.INCORRECT,
        SubmissionStatus.SYNTAX_ERROR,
    }
    assert "having_vs_where" in evaluation.diagnostic_tags or "grouping" in evaluation.diagnostic_tags


def test_null_equals_null_fails() -> None:
    exercise = get_exercise("nul_001")
    evaluation = evaluate_exercise(
        exercise,
        "SELECT order_id, status, shipped_at FROM orders WHERE shipped_at = NULL",
    )
    assert evaluation.status != SubmissionStatus.CORRECT
    assert "null_handling" in evaluation.diagnostic_tags


def test_hidden_variant_does_not_break_reference() -> None:
    exercise = get_exercise("nul_001")
    evaluation = evaluate_query(
        exercise.reference_sql,
        reference_sql=exercise.reference_sql,
        dataset_id=exercise.dataset,
        spec=exercise.evaluation,
        variant="hidden_nulls",
        sandbox=None,
    )
    assert evaluation.status == SubmissionStatus.CORRECT
