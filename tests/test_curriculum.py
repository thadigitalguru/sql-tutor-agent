from app.curriculum.loader import get_exercise, load_exercises
from app.domain import SubmissionStatus
from app.sandbox.evaluator import evaluate_exercise

ALTERNATES = {
    "sel_001": "SELECT name, country FROM customers AS c",
    "whr_001": "SELECT name, country FROM customers WHERE country IN ('Kenya')",
    "whr_002": """
        SELECT order_id, status, total_amount
        FROM orders
        WHERE status = 'paid' AND total_amount > 99.999
    """,
    "ord_001": """
        SELECT product_name, price
        FROM products
        ORDER BY price DESC, product_name
    """,
    "nul_001": """
        SELECT order_id, status, shipped_at
        FROM orders
        WHERE shipped_at IS NULL
    """,
    "agg_001": "SELECT COUNT(order_id) FROM orders",
    "agg_002": "SELECT SUM(total_amount) AS revenue FROM orders WHERE status = 'paid'",
    "grp_001": """
        SELECT customer_id, SUM(total_amount) AS spent
        FROM orders
        GROUP BY 1
    """,
    "hav_001": """
        SELECT customer_id, SUM(total_amount) AS total
        FROM orders
        GROUP BY customer_id
        HAVING total > 500
    """,
    "join_001": """
        SELECT orders.order_id, customers.name, orders.total_amount
        FROM orders
        INNER JOIN customers
          ON orders.customer_id = customers.customer_id
    """,
    "left_002": """
        SELECT c.customer_id, c.name
        FROM customers c
        WHERE NOT EXISTS (
          SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id
        )
    """,
    "sub_001": """
        SELECT product_name, price
        FROM products
        WHERE price > (SELECT AVG(price) FROM products)
    """,
    "cte_001": """
        SELECT customer_id, SUM(total_amount) AS total
        FROM orders
        GROUP BY customer_id
        HAVING SUM(total_amount) > 500
    """,
}

WRONG = {
    "sel_001": "SELECT name FROM customers",
    "whr_001": "SELECT name, country FROM customers",
    "whr_002": "SELECT order_id, status, total_amount FROM orders WHERE status = 'paid'",
    "ord_001": "SELECT product_name, price FROM products ORDER BY price ASC",
    "nul_001": "SELECT order_id, status, shipped_at FROM orders WHERE shipped_at = NULL",
    "agg_001": "SELECT * FROM orders",
    "agg_002": "SELECT SUM(total_amount) FROM orders",
    "grp_001": "SELECT customer_id, SUM(total_amount) FROM orders",
    "hav_001": """
        SELECT customer_id, SUM(total_amount)
        FROM orders
        GROUP BY customer_id
    """,
    "join_001": "SELECT order_id, customer_id, total_amount FROM orders",
    "left_002": """
        SELECT c.customer_id, c.name
        FROM customers c
        JOIN orders o
          ON o.customer_id = c.customer_id
    """,
    "sub_001": "SELECT product_name, price FROM products WHERE price > 50",
    "cte_001": "SELECT customer_id, total_amount FROM orders",
}


def test_curriculum_loads_foundations_set() -> None:
    exercises = load_exercises()
    assert len(exercises) >= 30
    ids = {ex.id for ex in exercises}
    assert ids >= set(ALTERNATES)


def test_every_reference_passes() -> None:
    for exercise in load_exercises():
        evaluation = evaluate_exercise(exercise, exercise.reference_sql)
        assert evaluation.status == SubmissionStatus.CORRECT, (
            exercise.id,
            evaluation.status,
            evaluation.engine_message,
            evaluation.diagnostic_tags,
        )


def test_alternates_pass_and_wrong_fail() -> None:
    for exercise_id, sql in ALTERNATES.items():
        exercise = get_exercise(exercise_id)
        evaluation = evaluate_exercise(exercise, sql)
        assert evaluation.status == SubmissionStatus.CORRECT, (
            exercise_id,
            evaluation.status,
            evaluation.engine_message,
            evaluation.comparison,
        )
        wrong = evaluate_exercise(exercise, WRONG[exercise_id])
        assert wrong.status != SubmissionStatus.CORRECT, exercise_id
