# SQL Tutor Agent — Product & UX Specification

## 1. Product Goal

Build a personal SQL tutor that helps a learner become independently competent at writing SQL.

The agent should not behave like a normal chatbot that immediately gives answers. Its default behavior should be:

> Teach briefly → ask the learner to try → execute the learner's SQL → diagnose the result → give the smallest useful hint → let the learner retry → explain after success → update mastery.

The product should feel like a patient interactive coach with a real SQL sandbox, not a textbook and not an autocomplete tool.

---

## 2. Core Design Principles

### 2.1 Learning by doing
The learner should write SQL in almost every session.

Prefer:
- short explanations,
- concrete tables,
- one task at a time,
- immediate feedback,
- retries.

Avoid:
- long lectures before practice,
- showing the final query too early,
- testing syntax without context,
- progressing only because the learner says "I understand."

### 2.2 Evaluate execution, not resemblance
Do not grade a query by comparing its text to a reference answer.

A correct SQL query may look very different from the expected solution.

The evaluator should primarily compare:
- whether the query executes,
- whether the returned rows are correct,
- whether values are correct,
- whether ordering matters for the task,
- whether duplicates are correct,
- whether NULL behavior is correct.

Only use query structure as a secondary teaching signal.

### 2.3 Progressive disclosure
Do not show every feature or explanation at once.

A beginner should initially see:
- the problem,
- the relevant schema,
- a small data preview,
- an SQL input box,
- Run / Submit,
- Hint.

Advanced controls can appear later:
- query plan,
- performance notes,
- alternate solutions,
- dialect notes,
- optimization challenges.

### 2.4 Hints before answers
Use a hint ladder.

1. Conceptual nudge
2. Point to the relevant table/column
3. Point to the relevant SQL construct
4. Show a partial query skeleton
5. Show the full solution only after repeated failure or explicit request

### 2.5 One primary objective per exercise
An exercise may depend on previously learned skills, but should normally introduce or assess one main concept.

Example:

Main concept:
- `LEFT JOIN`

Supporting concepts:
- `SELECT`
- aliases
- `ON`

This makes diagnosis and mastery tracking much more reliable.

---

## 3. Target User Experience

### First launch

The agent should ask only the questions necessary to begin:

1. What is your current SQL level?
   - New to SQL
   - Know basic SELECT/WHERE
   - Comfortable with joins/grouping
   - Advanced

2. What SQL dialect do you want?
   - PostgreSQL
   - SQLite
   - MySQL
   - SQL Server
   - Not sure

3. What is your main goal?
   - Learn SQL from scratch
   - Data analysis
   - Interview preparation
   - Work with databases
   - Refresh/improve SQL

If the learner selects "Not sure" for dialect, default the teaching environment to PostgreSQL-style SQL while using a local compatible sandbox where practical.

Do not block learning on onboarding completeness.

---

## 4. Primary Session Loop

Every exercise session should follow this state machine:

```text
INTRODUCE
   ↓
EXPLAIN BRIEFLY
   ↓
PRESENT EXERCISE
   ↓
LEARNER WRITES SQL
   ↓
EXECUTE
   ↓
┌──────────────────────┐
│ correct?             │
├──────────┬───────────┤
│ YES      │ NO        │
↓          ↓
EXPLAIN    DIAGNOSE
WHY        ↓
↓          HINT
MASTERY    ↓
UPDATE     RETRY
↓          ↺
NEXT TASK
```

The agent should rarely jump from an incorrect answer directly to the full solution.

---

## 5. Exercise Screen

A useful exercise view contains:

```text
┌─────────────────────────────────────────────┐
│ Lesson: GROUP BY                            │
│ Goal: Summarize rows by category            │
├─────────────────────────────────────────────┤
│ Schema                                      │
│                                             │
│ orders                                      │
│ - order_id INTEGER                          │
│ - customer_id INTEGER                       │
│ - amount DECIMAL                            │
│ - order_date DATE                           │
├─────────────────────────────────────────────┤
│ Task                                        │
│ Return each customer_id and total amount    │
│ they have spent.                            │
├─────────────────────────────────────────────┤
│ SQL editor                                  │
│                                             │
│ SELECT ...                                  │
│                                             │
├─────────────────────────────────────────────┤
│ [Run] [Submit] [Hint]                       │
├─────────────────────────────────────────────┤
│ Result / feedback                           │
└─────────────────────────────────────────────┘
```

### Run vs Submit

**Run**
- execute SQL,
- show raw result,
- show database errors,
- do not update mastery.

**Submit**
- execute SQL,
- evaluate correctness,
- give teaching feedback,
- update attempt history,
- update mastery if appropriate.

This distinction lets the learner experiment without every query being graded.

---

## 6. Feedback Rules

Feedback should answer three questions:

1. What happened?
2. Why did it happen?
3. What should I try next?

Bad feedback:

> Incorrect. Try again.

Better feedback:

> Your query runs, but it returns one row per order instead of one row per customer. You are calculating `SUM(amount)`, but the result is not grouped by customer yet. Which column should define each group?

### Syntax error feedback

Do not merely repeat the database error.

Transform:

```text
near "FROM": syntax error
```

into:

> The database reached `FROM` while it was still expecting a valid expression in your `SELECT` list. Check the item immediately before `FROM`, especially for an extra comma or missing column.

Show the raw engine error underneath as an optional detail.

---

## 7. Hint Ladder

Each exercise should have hints at increasing specificity.

Example for a JOIN task:

### Hint 1 — Concept
> The data you need is split across two tables.

### Hint 2 — Relationship
> `orders.customer_id` refers to `customers.customer_id`.

### Hint 3 — Construct
> Use a `JOIN` with an `ON` condition connecting those columns.

### Hint 4 — Skeleton
```sql
SELECT ...
FROM orders
JOIN customers
  ON ...
```

### Hint 5 — Solution
Only show after:
- explicit "show solution",
- or configurable number of failed attempts.

The system must record the highest hint level used because successful completion after Hint 4 means something different from solving with no hint.

---

## 8. Mastery Model

Track mastery by skill, not only by lesson completion.

Example skills:

```text
select_basic
filter_where
comparison_operators
boolean_logic
order_by
limit
aggregate_count
aggregate_sum
group_by
having
inner_join
left_join
subquery
cte
case_expression
window_functions
date_operations
null_handling
set_operations
```

For each skill store:

```json
{
  "skill_id": "group_by",
  "mastery": 0.72,
  "attempts": 9,
  "successful_attempts": 7,
  "recent_success_streak": 2,
  "last_practiced_at": "2026-09-17T12:00:00Z",
  "highest_hint_used_recently": 1
}
```

### Suggested interpretation

```text
0.00–0.29  New
0.30–0.59  Learning
0.60–0.79  Practicing
0.80–0.94  Strong
0.95–1.00  Mastered
```

Do not permanently mark a concept mastered after one successful exercise.

---

## 9. Adaptive Difficulty

The next exercise should be selected using:

1. learner goal,
2. prerequisite completion,
3. weakest relevant skills,
4. recency,
5. recent frustration,
6. recent hint dependence.

### Difficulty should increase when
- learner solves several exercises without hints,
- solution is correct on the first attempt,
- learner can explain the reasoning.

### Difficulty should decrease when
- repeated syntax failures occur,
- the learner asks for fundamentals,
- the same conceptual error repeats,
- the learner uses high-level hints repeatedly.

Do not interpret one mistake as lack of ability.

---

## 10. Recommended Lesson Rhythm

A good 20–30 minute session:

```text
2 min   Recall question
5 min   New concept
12 min  2–4 exercises
5 min   Mixed review
2 min   Summary + next step
```

Short sessions should still end with a meaningful checkpoint.

---

## 11. Dataset Strategy

Use small realistic datasets.

Good themes:
- ecommerce,
- music streaming,
- employees/departments,
- food delivery,
- subscriptions,
- movies,
- transport,
- SaaS analytics.

Keep beginner datasets small enough to inspect manually.

Example:

```text
customers: 8 rows
orders: 20 rows
products: 12 rows
order_items: 35 rows
```

Larger datasets can be introduced for performance and analytics lessons.

---

## 12. User-Friendly Behaviors

The tutor should:

- remember the learner's current level,
- remember the chosen SQL dialect,
- resume where the previous session ended,
- allow "give me an easier example",
- allow "explain this differently",
- allow "show me the data",
- allow "why is my query wrong?",
- allow free exploration of the database,
- celebrate progress briefly without becoming repetitive,
- never shame incorrect attempts.

Useful commands:

```text
/hint
/solution
/schema
/data customers
/progress
/review
/easier
/harder
/explain
/reset-exercise
```

These can be UI buttons rather than literal slash commands.

---

## 13. Minimum Viable Product

The MVP should contain only what is required for a strong learning loop.

### Required
- learner profile,
- lesson selection,
- schema display,
- SQL editor,
- sandbox database,
- SQL execution,
- correctness evaluator,
- hint generation,
- progress tracking,
- session resume.

### Not required for MVP
- voice mode,
- multiplayer,
- certificates,
- elaborate gamification,
- multiple database servers,
- code completion,
- AI-generated datasets every session,
- query visualization,
- leaderboards.

Build the learning loop first.

---

## 14. Success Metrics

Measure whether the learner is becoming more independent.

Useful metrics:

- first-attempt correctness,
- attempts per exercise,
- hints used per successful exercise,
- repeated error frequency,
- time to successful solution,
- retention after 1/7/30 days,
- mastery by concept,
- percentage of exercises solved without solution reveal.

Avoid optimizing primarily for:
- messages sent,
- session length,
- number of lessons completed.

The goal is competence, not engagement for its own sake.

---

## 15. Definition of "Good"

The agent is working well when a learner can:

1. understand the problem,
2. inspect the schema,
3. decide which SQL concepts apply,
4. write and debug the query,
5. explain why the result is correct,
6. solve a similar problem later without help.

That is the product's north star.
