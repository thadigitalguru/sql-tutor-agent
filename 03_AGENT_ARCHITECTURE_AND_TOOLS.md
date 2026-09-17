# SQL Tutor Agent — Architecture & Tool Specification

## 1. Recommended Architecture

Start with a small deterministic system around the LLM.

```text
┌───────────────────┐
│ Web / Chat UI     │
└─────────┬─────────┘
          │
          ▼
┌────────────────────────────┐
│ Tutor Orchestrator         │
│                            │
│ - session state            │
│ - prompt assembly          │
│ - tool routing             │
│ - lesson state machine     │
└───────┬─────────┬──────────┘
        │         │
        │         └───────────────────────┐
        ▼                                 ▼
┌───────────────────┐            ┌────────────────────┐
│ LLM Tutor         │            │ Progress Store     │
│                   │            │ SQLite/Postgres    │
└─────────┬─────────┘            └────────────────────┘
          │
          ▼
┌────────────────────────────┐
│ SQL Sandbox + Evaluator    │
│                            │
│ - schema inspection        │
│ - query execution          │
│ - result comparison        │
│ - reset dataset            │
└────────────────────────────┘
```

The LLM should not own correctness.

The deterministic evaluator should decide whether an exercise result is correct whenever possible.

---

## 2. Recommended MVP Stack

### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy or direct database driver
- Pydantic
- SQLite for tutor state and/or sandbox
- PostgreSQL later for production

### Frontend
Choose one:
- Next.js / React for a polished app,
- Streamlit for a fast prototype,
- simple server-rendered UI for the smallest build.

### LLM
Any tool-capable model that can:
- follow a system prompt,
- call functions/tools,
- reason over database feedback.

### SQL editor
Use a proper code editor component when using a browser UI:
- Monaco Editor, or
- CodeMirror.

---

## 3. Suggested Repository Structure

```text
sql-tutor/
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── agent/
│   │   ├── orchestrator.py
│   │   ├── prompts.py
│   │   ├── tutor.py
│   │   └── state.py
│   │
│   ├── sandbox/
│   │   ├── executor.py
│   │   ├── evaluator.py
│   │   ├── safety.py
│   │   ├── schema.py
│   │   └── reset.py
│   │
│   ├── curriculum/
│   │   ├── loader.py
│   │   ├── selector.py
│   │   └── mastery.py
│   │
│   ├── storage/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── database.py
│   │
│   └── api/
│       ├── sessions.py
│       ├── exercises.py
│       ├── sql.py
│       └── progress.py
│
├── curriculum/
│   ├── foundations/
│   ├── joins/
│   ├── aggregation/
│   └── advanced/
│
├── datasets/
│   ├── ecommerce/
│   └── employees/
│
├── tests/
│   ├── test_executor.py
│   ├── test_evaluator.py
│   ├── test_mastery.py
│   └── test_curriculum.py
│
├── scripts/
│   └── seed_data.py
│
├── .env.example
├── pyproject.toml
└── README.md
```

Keep exercise content outside the Python code.

---

## 4. Agent State Machine

The agent should have explicit states.

```python
from enum import Enum

class LessonState(str, Enum):
    INTRO = "intro"
    TEACH = "teach"
    EXERCISE = "exercise"
    ATTEMPT = "attempt"
    FEEDBACK = "feedback"
    RETRY = "retry"
    REVIEW = "review"
    COMPLETE = "complete"
```

Do not rely on the LLM to infer every transition from conversation history.

A deterministic orchestrator should know:
- current exercise,
- attempt count,
- hint level,
- learner mastery,
- whether a submission was graded,
- what should happen next.

---

## 5. Tool Interface

The tutor should receive a small set of tools.

### `get_schema`

Purpose:
Return the schema visible in the active exercise.

Input:

```json
{
  "dataset_id": "ecommerce"
}
```

Output:

```json
{
  "tables": {
    "customers": [
      {"name": "customer_id", "type": "INTEGER"},
      {"name": "name", "type": "TEXT"}
    ],
    "orders": [
      {"name": "order_id", "type": "INTEGER"},
      {"name": "customer_id", "type": "INTEGER"},
      {"name": "amount", "type": "DECIMAL"}
    ]
  }
}
```

---

### `preview_table`

Purpose:
Show a small number of rows.

Input:

```json
{
  "table": "orders",
  "limit": 5
}
```

Rules:
- cap limit,
- only allow tables in active dataset,
- never construct SQL from unvalidated table names.

---

### `run_sql`

Purpose:
Allow experimentation.

Input:

```json
{
  "query": "SELECT * FROM orders LIMIT 5"
}
```

Output:

```json
{
  "ok": true,
  "columns": ["order_id", "customer_id", "amount"],
  "rows": [
    [1, 3, 49.99]
  ],
  "row_count": 1,
  "elapsed_ms": 2
}
```

On error:

```json
{
  "ok": false,
  "error_type": "syntax",
  "message": "near FROM: syntax error"
}
```

Do not leak server internals.

---

### `evaluate_submission`

Purpose:
Grade an exercise.

Input:

```json
{
  "exercise_id": "grp_001",
  "query": "SELECT customer_id, SUM(amount) ..."
}
```

Output:

```json
{
  "status": "INCORRECT",
  "execution_ok": true,
  "comparison": {
    "row_count_expected": 5,
    "row_count_actual": 20,
    "columns_match": true,
    "values_match": false,
    "order_match": true
  },
  "diagnostic_tags": ["aggregation", "grouping"]
}
```

Important:
Do not include the reference SQL in ordinary evaluator output.

---

### `get_progress`

Purpose:
Retrieve learner mastery and recent history.

---

### `record_attempt`

Purpose:
Store:
- query,
- exercise id,
- success/failure,
- diagnostic tags,
- hint level,
- timestamp,
- execution metadata.

---

### `update_mastery`

Prefer making this deterministic rather than letting the LLM directly assign arbitrary scores.

---

## 6. SQL Sandbox Safety

Never execute unrestricted learner SQL against application or production databases.

Use an isolated database.

### Minimum safety

For beginner read-only lessons:
- permit `SELECT`,
- permit `WITH ... SELECT`,
- reject multiple statements,
- reject DDL,
- reject DML,
- set execution timeout,
- cap returned rows.

Block:
- `DROP`
- `ALTER`
- `ATTACH`
- `DETACH`
- `PRAGMA` where unsafe
- extension loading
- filesystem functions
- network-capable extensions
- multiple statements

Do not rely on regex alone.

Use:
- a SQL parser when practical,
- database permissions,
- isolated database/container,
- timeouts,
- query cancellation,
- memory/resource limits.

Defense in depth matters.

---

## 7. Execution Limits

Recommended defaults:

```text
timeout:           2 seconds
max returned rows: 200
max query length:  20,000 chars
statements:        1
write access:      disabled
```

For advanced performance lessons, use a separate environment with higher limits.

---

## 8. Result-Set Evaluation

The evaluator should compare results, not query strings.

### Case A — Order does not matter

Normalize rows as a multiset.

This preserves duplicates while ignoring row order.

Conceptually:

```python
Counter(normalize(row) for row in actual) == \
Counter(normalize(row) for row in expected)
```

### Case B — Order matters

Compare rows in sequence.

### Column names

Decide per exercise whether aliases matter.

Example:

```json
{
  "require_column_names": false
}
```

### Numeric tolerance

For floating-point results:

```text
abs(actual - expected) <= tolerance
```

Prefer fixed decimal types in financial datasets.

### NULL

Treat SQL NULL explicitly.

Do not convert it to an empty string.

---

## 9. Hidden Test Cases

A learner may accidentally produce the right result on one tiny dataset with incorrect logic.

For important exercises, evaluate against multiple seeded variants.

Example:

Exercise:
> Return customers with no orders.

A fragile query may appear correct when every customer has an order.

Use hidden dataset variants containing:
- zero matches,
- duplicate relationships,
- NULL values,
- tied values,
- multiple rows per group.

This is especially useful for:
- joins,
- aggregation,
- NULL logic,
- `NOT IN`,
- window functions,
- top-N queries.

---

## 10. Exercise Definition Format

Store exercises as YAML or JSON.

Example YAML:

```yaml
id: join_003
title: Orders with customer names

primary_skill: inner_join
difficulty: 2

prerequisites:
  - select_basic
  - table_aliases

dataset: ecommerce

prompt: >
  Return order_id, customer name, and amount for every order.

schema:
  - customers
  - orders

evaluation:
  mode: result_set
  order_matters: false
  require_column_names: false

reference:
  sql: |
    SELECT
      o.order_id,
      c.name,
      o.amount
    FROM orders o
    JOIN customers c
      ON c.customer_id = o.customer_id

hints:
  - The required columns come from two different tables.
  - Match rows using customer_id.
  - Use JOIN ... ON ...

diagnostic_rules:
  - tag: missing_join
  - tag: join_condition
```

The `reference.sql` should be server-side only.

---

## 11. Mastery Algorithm

Use a simple understandable model first.

For each submission calculate evidence:

```text
correct first try, no hints      +0.12
correct after small hint         +0.08
correct after stronger hints     +0.04
solution revealed                +0.01
incorrect                        -0.02
```

Then clamp:

```python
mastery = min(1.0, max(0.0, mastery + delta))
```

This is intentionally simple.

Later, replace with:
- Bayesian Knowledge Tracing,
- Elo-style skill models,
- Item Response Theory,
- spaced-repetition models.

Do not start there unless needed.

### Important
A skill should not become "mastered" until it has been demonstrated across multiple exercises and at least one later review.

---

## 12. Exercise Selection

A practical scoring formula:

```text
priority =
    prerequisite_ready
  * goal_relevance
  * weakness
  * review_due
  * difficulty_fit
```

Conceptually:

```python
weakness = 1 - mastery
review_due = f(days_since_practice)
difficulty_fit = closeness(exercise_level, learner_level)
```

Include occasional mastered-skill review so old knowledge is not forgotten.

---

## 13. Conversation Memory

Do not send the entire conversation to the model forever.

Maintain structured state:

```json
{
  "session_id": "...",
  "learner_id": "...",
  "current_exercise_id": "join_003",
  "lesson_state": "retry",
  "attempt_count": 2,
  "hint_level": 1,
  "recent_summary": "Learner understands INNER JOIN concept but has twice used the wrong ON columns."
}
```

Keep a short recent transcript plus structured history.

This reduces:
- token cost,
- latency,
- context drift.

---

## 14. Data Model

Minimal tables:

### learners

```text
id
created_at
sql_level
dialect
goal
preferences_json
```

### skills

```text
id
name
prerequisites_json
```

### learner_skills

```text
learner_id
skill_id
mastery
attempts
successes
last_practiced_at
```

### exercises

```text
id
primary_skill
difficulty
dataset_id
content_path
```

### attempts

```text
id
learner_id
exercise_id
query
status
hint_level
diagnostic_tags_json
created_at
```

### sessions

```text
id
learner_id
started_at
ended_at
summary
```

---

## 15. API Shape

Suggested endpoints:

```text
POST /sessions
GET  /sessions/{id}

GET  /lessons/next
GET  /exercises/{id}

POST /sql/run
POST /exercises/{id}/submit
POST /exercises/{id}/hint

GET  /progress
GET  /schema/{dataset_id}
GET  /tables/{table}/preview
```

Keep LLM calls behind the backend.

Never expose model or database secrets to the frontend.

---

## 16. LLM Responsibilities vs Deterministic Responsibilities

### Let the LLM do
- explanation,
- hints,
- conversational diagnosis,
- alternate explanations,
- exercise wording,
- session summaries.

### Do not let the LLM alone decide
- whether the SQL executed,
- whether result rows match,
- whether a table exists,
- whether the learner used a hint,
- current mastery values,
- sandbox access permissions.

This separation is one of the most important design decisions.

---

## 17. Latency Optimization

A user-friendly tutor should feel immediate.

Use this order:

1. execute learner SQL,
2. run deterministic comparison,
3. send compact evaluator output to LLM,
4. generate feedback.

Do not send the full database to the model.

Cache:
- schemas,
- exercise definitions,
- expected results.

Stream tutor text if supported.

---

## 18. Testing Strategy

### Unit tests
- SQL safety rules,
- evaluator normalization,
- order-sensitive comparison,
- duplicate handling,
- NULL handling,
- numeric tolerance,
- mastery updates.

### Golden tests
For each exercise:
- reference solution passes,
- known wrong solution fails,
- alternate correct solution passes.

### Adversarial tests
Try:
- multiple statements,
- comments hiding destructive statements,
- very expensive queries,
- recursive CTE abuse,
- invalid identifiers,
- dialect-specific syntax,
- result sets with duplicate rows.

### Tutor behavior tests
Check that the agent:
- does not reveal answers on first failure,
- uses schema correctly,
- calls evaluator before grading,
- respects selected dialect,
- increases hint specificity gradually.

---

## 19. Build Order

Build in this sequence:

### Phase 1 — Deterministic SQL core
1. dataset,
2. sandbox,
3. schema reader,
4. execution,
5. result comparison.

### Phase 2 — Curriculum
6. exercise format,
7. 20–30 curated exercises,
8. mastery tracking,
9. next-exercise selector.

### Phase 3 — Tutor
10. system prompt,
11. tool calling,
12. error diagnosis,
13. hint ladder,
14. session summaries.

### Phase 4 — Interface
15. SQL editor,
16. schema panel,
17. results panel,
18. progress screen.

### Phase 5 — Refinement
19. hidden test datasets,
20. spaced review,
21. performance lessons,
22. more dialects.

Do not begin with a complex autonomous-agent framework. A deterministic orchestrator plus tool-capable LLM is enough.

---

## 20. MVP Acceptance Criteria

The MVP is ready when a learner can:

1. start a session,
2. receive an appropriate exercise,
3. inspect the schema,
4. write SQL,
5. run it safely,
6. submit it,
7. receive correct evaluation,
8. receive a useful hint after failure,
9. retry,
10. finish an exercise,
11. see mastery update,
12. return later and resume.

If these twelve things work reliably, you have a real SQL tutor rather than a chat demo.
