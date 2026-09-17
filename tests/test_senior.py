from app.curriculum.loader import get_exercise, load_exercises
from app.domain import SubmissionStatus
from app.sandbox.evaluator import evaluate_exercise
from app.sandbox.executor import run_sql

SENIOR_IDS = [
    "ai_001",
    "ai_002",
    "ai_003",
    "ai_004",
    "ai_005",
    "ai_006",
    "arch_001",
    "arch_002",
    "arch_003",
    "arch_004",
    "dbe_001",
    "dbe_002",
    "dbe_003",
    "dbe_004",
    "model_001",
    "model_002",
    "model_003",
    "set_001",
]


def test_platform_schema_loads() -> None:
    result = run_sql("SELECT COUNT(*) FROM predictions", dataset_id="platform")
    assert result.ok
    assert result.rows[0][0] == 7


def test_senior_references_and_known_wrongs() -> None:
    ids = {ex.id for ex in load_exercises()}
    assert set(SENIOR_IDS) <= ids
    for exercise_id in SENIOR_IDS:
        exercise = get_exercise(exercise_id)
        ok = evaluate_exercise(exercise, exercise.reference_sql)
        assert ok.status == SubmissionStatus.CORRECT, (
            exercise_id,
            ok.status,
            ok.engine_message,
            ok.comparison,
        )


def test_scd_current_row_fails_point_in_time() -> None:
    exercise = get_exercise("arch_003")
    wrong = evaluate_exercise(
        exercise,
        """
        SELECT f.order_id, d.country
        FROM fact_orders f
        JOIN dim_customer d
          ON d.customer_id = f.customer_id
         AND d.is_current = 1
        GROUP BY f.order_id, d.country
        """,
    )
    assert wrong.status != SubmissionStatus.CORRECT


def test_feature_leakage_query_fails() -> None:
    exercise = get_exercise("ai_002")
    wrong = evaluate_exercise(
        exercise,
        """
        WITH ranked AS (
          SELECT
            l.entity_id,
            f.orders_7d,
            f.spend_7d,
            ROW_NUMBER() OVER (
              PARTITION BY l.entity_id
              ORDER BY f.computed_at DESC
            ) AS rn
          FROM labels l
          JOIN user_features f
            ON f.user_id = l.entity_id
        )
        SELECT entity_id, orders_7d, spend_7d
        FROM ranked
        WHERE rn = 1
        """,
    )
    assert wrong.status != SubmissionStatus.CORRECT


def test_recursive_cte_is_allowed() -> None:
    result = run_sql(
        """
        WITH RECURSIVE reports AS (
          SELECT employee_id, manager_id, 0 AS depth
          FROM employees
          WHERE employee_id = 2
          UNION ALL
          SELECT e.employee_id, e.manager_id, r.depth + 1
          FROM employees e
          JOIN reports r ON e.manager_id = r.employee_id
        )
        SELECT employee_id FROM reports WHERE depth > 0
        """,
        dataset_id="platform",
    )
    assert result.ok
    assert sorted(row[0] for row in result.rows) == [3, 4]
