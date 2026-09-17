from app.curriculum.loader import get_exercise
from app.domain import QualityKind, SubmissionStatus
from app.sandbox.evaluator import evaluate_exercise
from app.sandbox.quality import assess_quality


def test_clean_select_has_no_quality_notes() -> None:
    exercise = get_exercise("sel_001")
    notes = assess_quality("SELECT name, country FROM customers", exercise=exercise)
    assert notes == []


def test_select_star_is_readability_note() -> None:
    notes = assess_quality("SELECT * FROM customers")
    assert any(note.tag == "select_star" for note in notes)
    assert notes[0].kind == QualityKind.READABILITY


def test_cte_equivalent_without_with_is_quality_not_failure() -> None:
    exercise = get_exercise("cte_001")
    query = """
        SELECT customer_id, SUM(total_amount) AS total
        FROM orders
        GROUP BY customer_id
        HAVING SUM(total_amount) > 500
    """
    evaluation = evaluate_exercise(exercise, query)
    assert evaluation.status == SubmissionStatus.CORRECT_WITH_IMPROVEMENT
    assert any(note.tag == "missing_cte" for note in evaluation.quality_notes)


def test_reference_sql_stays_correct() -> None:
    exercise = get_exercise("sel_001")
    evaluation = evaluate_exercise(exercise, exercise.reference_sql)
    assert evaluation.status == SubmissionStatus.CORRECT
    assert evaluation.quality_notes == []


def test_distinct_note_skipped_when_reference_also_uses_it() -> None:
    notes = assess_quality("SELECT DISTINCT name FROM customers")
    assert any(note.tag == "select_distinct" for note in notes)


def test_or_chain_suggests_in() -> None:
    notes = assess_quality(
        "SELECT name FROM customers WHERE country = 'US' OR country = 'UK' OR country = 'KE'"
    )
    assert any(note.tag == "or_vs_in" for note in notes)
