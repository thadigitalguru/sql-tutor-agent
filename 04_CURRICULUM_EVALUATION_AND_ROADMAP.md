# SQL Tutor Agent — Curriculum, Evaluation & Build Roadmap

## 1. Curriculum Philosophy

The curriculum should teach SQL as a problem-solving language, not as a list of keywords.

Each concept should follow:

```text
See it
→ understand it
→ write it
→ debug it
→ combine it
→ recall it later
```

Every major skill needs:
- explanation,
- worked example,
- guided exercise,
- independent exercise,
- mixed review,
- delayed review.

---

## 2. Skill Dependency Graph

Recommended sequence:

```text
SELECT
├── columns
├── aliases
└── expressions
     ↓
WHERE
├── comparisons
├── AND / OR / NOT
├── IN
├── BETWEEN
└── LIKE
     ↓
ORDER BY
LIMIT
     ↓
NULL
├── IS NULL
└── COALESCE
     ↓
AGGREGATES
├── COUNT
├── SUM
├── AVG
├── MIN
└── MAX
     ↓
GROUP BY
     ↓
HAVING
     ↓
JOINS
├── INNER JOIN
├── LEFT JOIN
└── multi-table joins
     ↓
SUBQUERIES
├── scalar
├── IN
└── EXISTS
     ↓
CTEs
     ↓
CASE
     ↓
DATE / TIME
     ↓
SET OPERATIONS
├── UNION
├── INTERSECT
└── EXCEPT
     ↓
WINDOW FUNCTIONS
├── ROW_NUMBER
├── RANK
├── SUM OVER
├── LAG / LEAD
└── partitions
     ↓
ADVANCED QUERY DESIGN
├── multi-stage analysis
├── deduplication
├── funnels
├── cohorts
└── performance basics
```

Not every learner needs every branch immediately.

---

## 3. Recommended Curriculum

## Module 1 — Query Fundamentals

### Skills
- `SELECT`
- choosing columns
- `SELECT *`
- aliases
- expressions
- `DISTINCT`

### Learner outcome
Can retrieve and shape basic rows from one table.

### Example exercise
> From `products`, return product name and price. Rename `price` to `unit_price`.

---

## Module 2 — Filtering

### Skills
- `WHERE`
- comparison operators
- `AND`
- `OR`
- `NOT`
- `IN`
- `BETWEEN`
- `LIKE`

### Learner outcome
Can translate business conditions into row filters.

### Common misconception
Confusing:
```sql
A AND B OR C
```
with:
```sql
A AND (B OR C)
```

Teach parentheses explicitly.

---

## Module 3 — Sorting & Limiting

### Skills
- `ORDER BY`
- ascending/descending
- multiple sort keys
- `LIMIT` / dialect equivalent

### Example exercise
> Return the five most expensive products, highest price first.

Include tie-handling discussions later.

---

## Module 4 — NULL

Teach NULL early enough to prevent bad mental models.

### Skills
- `IS NULL`
- `IS NOT NULL`
- `COALESCE`
- three-valued logic basics

### Critical misconception
This is wrong:

```sql
WHERE shipped_at = NULL
```

Teach why:

```sql
WHERE shipped_at IS NULL
```

works differently.

---

## Module 5 — Aggregation

### Skills
- `COUNT`
- `COUNT(*)`
- `COUNT(column)`
- `SUM`
- `AVG`
- `MIN`
- `MAX`

### Important distinction
Teach that:

```sql
COUNT(*)
```

counts rows, while:

```sql
COUNT(column)
```

does not count NULL values.

---

## Module 6 — GROUP BY & HAVING

### Skills
- grouping
- aggregate per group
- grouping multiple columns
- `HAVING`

### Key conceptual model

```text
WHERE  → filters rows before grouping
HAVING → filters groups after aggregation
```

Do not teach this only as a syntax rule.

---

## Module 7 — Joins

Use visual row examples.

### INNER JOIN
Teach:
> Keep rows where a relationship exists.

### LEFT JOIN
Teach:
> Keep every left-side row, even if no right-side row matches.

### Skills
- join keys
- aliases
- one-to-many relationships
- multiple joins
- duplicate multiplication

### Critical exercise
> Find customers who have never placed an order.

This exposes whether the learner understands outer joins and NULL filtering.

---

## Module 8 — Subqueries

### Skills
- scalar subqueries
- `IN`
- correlated `EXISTS`
- derived tables

Teach use cases, not only syntax.

Example:
> Return products priced above the average product price.

---

## Module 9 — CTEs

Teach CTEs as a readability and query-structuring tool.

```sql
WITH customer_spend AS (
    ...
)
SELECT ...
FROM customer_spend
```

Learner outcome:
Can split a multi-step analytical problem into named stages.

---

## Module 10 — CASE

### Skills
- categorization
- conditional aggregation

Example:

```sql
SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END)
```

---

## Module 11 — Dates

Make this dialect-aware.

Concepts:
- current date,
- date extraction,
- date truncation,
- date difference,
- intervals,
- monthly grouping.

Avoid pretending date syntax is portable across all databases.

---

## Module 12 — Set Operations

Teach:
- `UNION`
- `UNION ALL`
- `INTERSECT`
- `EXCEPT`

Key distinction:
`UNION` removes duplicates; `UNION ALL` does not.

---

## Module 13 — Window Functions

Start only after aggregation and joins are comfortable.

### Sequence
1. `OVER()`
2. `PARTITION BY`
3. `ORDER BY` inside window
4. `ROW_NUMBER`
5. `RANK`
6. running totals
7. `LAG` / `LEAD`

Key conceptual distinction:

```text
GROUP BY collapses rows.
Window functions usually keep rows.
```

---

## Module 14 — Analytical SQL

Combine skills into realistic tasks:

- monthly revenue,
- top products per category,
- repeat customers,
- retention,
- conversion funnels,
- first/last events,
- rolling metrics,
- deduplication.

At this stage, tasks should resemble real analyst work.

---

## 4. Exercise Difficulty Scale

### Level 1 — Direct
One table, one obvious concept.

Example:
> Return customers from Kenya.

### Level 2 — Combined basics
One table, two concepts.

Example:
> Return the five highest-value paid orders.

### Level 3 — Relational
Join or grouping required.

### Level 4 — Multi-step
Several concepts, possibly CTE/subquery.

### Level 5 — Open analytical problem
Multiple valid approaches.

Difficulty should measure reasoning complexity, not query length.

---

## 5. Exercise Template

Every exercise should define:

```yaml
id:
title:
primary_skill:
secondary_skills:
difficulty:
dataset:
prerequisites:

prompt:

schema_visibility:
  tables:

evaluation:
  mode:
  order_matters:
  duplicates_matter:
  require_column_names:
  numeric_tolerance:

reference_solution:

hints:
  - level: 1
    text:
  - level: 2
    text:
  - level: 3
    text:
  - level: 4
    text:

common_errors:
  - tag:
    explanation:
```

This standardization improves both UX and evaluation quality.

---

## 6. Starter Exercise Set

Create at least 30 curated exercises before relying heavily on generated exercises.

Recommended distribution:

```text
SELECT / aliases           3
WHERE                      4
ORDER / LIMIT              2
NULL                       2
aggregates                 3
GROUP BY / HAVING          4
INNER JOIN                 3
LEFT JOIN                  3
subqueries                 2
CTEs                       1
CASE                       1
dates                      1
mixed review               1
-----------------------------
Total                     30
```

Curated exercises give you reliable baseline quality.

Use LLM-generated exercises later for variety.

---

## 7. Example Dataset

Use one coherent dataset across early modules so the learner does not spend time repeatedly learning new schemas.

### ecommerce dataset

#### customers

```text
customer_id
name
country
signup_date
```

#### orders

```text
order_id
customer_id
order_date
status
total_amount
```

#### products

```text
product_id
product_name
category
price
```

#### order_items

```text
order_item_id
order_id
product_id
quantity
unit_price
```

This dataset supports:
- filtering,
- aggregation,
- joins,
- subqueries,
- CTEs,
- windows,
- analytical tasks.

Introduce other datasets later to test transfer of learning.

---

## 8. Evaluation Framework

Correctness evaluation should have layers.

### Layer 1 — Execution
Did SQL run?

```text
yes / no
```

### Layer 2 — Shape
Check:
- column count,
- row count,
- required aliases if relevant.

### Layer 3 — Values
Compare result sets.

### Layer 4 — Edge cases
Run hidden variants when needed.

### Layer 5 — Quality
Only after correctness:
- readability,
- unnecessary complexity,
- performance,
- dialect idioms.

Do not mix "style" failure with "wrong answer."

---

## 9. Diagnostic Examples

### Missing GROUP BY

Learner:

```sql
SELECT customer_id, SUM(total_amount)
FROM orders;
```

Likely tag:

```text
aggregation
grouping
```

Teaching feedback:

> You want one total for each customer, but the query currently asks SQL for one overall aggregate while also selecting `customer_id`. Group the rows by the value that should define each total.

---

### WHERE instead of HAVING

Learner:

```sql
SELECT customer_id, SUM(total_amount) AS total
FROM orders
WHERE SUM(total_amount) > 500
GROUP BY customer_id;
```

Tag:

```text
having_vs_where
```

Feedback:

> `WHERE` filters individual rows before grouping, so the aggregate does not exist yet at that stage. Which clause filters the grouped result?

---

### LEFT JOIN accidentally turned into INNER JOIN

Learner:

```sql
SELECT c.customer_id
FROM customers c
LEFT JOIN orders o
  ON c.customer_id = o.customer_id
WHERE o.status = 'paid';
```

If task requires all customers, including those without orders:

Tag:

```text
left_join_filter
```

Feedback:

> Your `LEFT JOIN` keeps unmatched customers initially, but the `WHERE o.status = 'paid'` condition removes rows where `o` is NULL. Think about whether that condition belongs in the join condition or whether NULL should be handled explicitly.

---

## 10. Retention & Spaced Review

Do not teach a concept once and move on forever.

Suggested review schedule after initial competence:

```text
same session
1 day
3 days
7 days
14 days
30 days
```

The actual schedule should adapt to performance.

Review exercises should use:
- different wording,
- slightly different schemas,
- mixed skills.

Do not repeat identical questions unless useful for error correction.

---

## 11. Mastery Evidence

Strong evidence:
- first-try correct,
- no hint,
- delayed recall,
- transfer to a new schema,
- correct explanation of reasoning.

Weak evidence:
- correct after full solution,
- copied query,
- same exercise repeated immediately.

The mastery model should weight evidence accordingly.

---

## 12. Progress View

A useful progress page:

```text
SQL Foundations

SELECT               96%  Mastered
WHERE                91%  Strong
ORDER BY             88%  Strong
NULL                 71%  Practicing
GROUP BY             78%  Practicing
HAVING               62%  Learning
INNER JOIN           54%  Learning
LEFT JOIN            31%  New
```

Also show:

```text
Recent pattern:
You often use WHERE when a grouped result requires HAVING.

Suggested next practice:
2 HAVING exercises
```

This is more actionable than "12 lessons completed."

---

## 13. Learner-Controlled Modes

Offer optional modes.

### Learn
New concept + guided exercises.

### Practice
Exercises with minimal teaching.

### Review
Spaced repetition of old skills.

### Challenge
Mixed problems without hints unless requested.

### Explain
Learner can paste SQL and ask for an explanation.

### Debug
Learner can paste broken SQL and work through it interactively.

These modes can all use the same core tools.

---

## 14. Personalization

Useful preferences:

```json
{
  "dialect": "postgresql",
  "session_length_minutes": 25,
  "explanation_depth": "concise",
  "practice_style": "guided",
  "goal": "data_analysis"
}
```

Do not over-personalize too early.

Infer preferences gradually or let the learner change them.

---

## 15. Build Roadmap

### Milestone 1 — Working SQL grader
Deliver:
- SQLite/Postgres dataset,
- safe executor,
- schema API,
- result evaluator,
- 10 exercises.

Success:
Alternate correct SQL passes.

---

### Milestone 2 — Tutor loop
Deliver:
- system prompt,
- exercise presentation,
- graded submission,
- progressive hints,
- retries.

Success:
The tutor does not reveal solutions prematurely and gives useful feedback.

---

### Milestone 3 — Progress
Deliver:
- learner account/state,
- attempts,
- mastery,
- next-exercise selection.

Success:
Returning learner resumes at a sensible point.

---

### Milestone 4 — Full foundations course
Deliver:
- 30+ exercises,
- modules through joins/subqueries,
- spaced review,
- progress UI.

Success:
Learner can complete a structured beginner path.

---

### Milestone 5 — Advanced analytics
Deliver:
- CTEs,
- dates,
- windows,
- realistic analytics datasets,
- performance/readability feedback.

---

## 16. What Not to Build First

Avoid spending early effort on:

- autonomous multi-agent teams,
- vector databases for a tiny curriculum,
- complicated RAG pipelines,
- full gamification systems,
- avatars,
- voice,
- badges,
- leaderboards,
- dozens of SQL dialects,
- arbitrary production database connections.

These may be useful later, but they do not improve the core learning loop as much as reliable execution, evaluation, and feedback.

---

## 17. Recommended First 10 Exercises

1. Select specific columns from `customers`.
2. Filter customers by country.
3. Filter orders by status and amount.
4. Sort products by price.
5. Find rows with NULL values.
6. Count all orders.
7. Calculate total revenue.
8. Calculate revenue by customer.
9. Filter grouped customer totals with `HAVING`.
10. Join orders to customers.

After these, review before introducing more.

---

## 18. Quality Checklist for Every Exercise

Before shipping an exercise, verify:

- [ ] prompt is unambiguous,
- [ ] referenced tables exist,
- [ ] referenced columns exist,
- [ ] prerequisites were taught,
- [ ] reference solution executes,
- [ ] at least one alternate correct query passes,
- [ ] at least one known wrong query fails,
- [ ] ordering rule is explicit,
- [ ] NULL behavior is intentional,
- [ ] duplicate behavior is intentional,
- [ ] hints become progressively more specific,
- [ ] diagnostic feedback is useful,
- [ ] hidden edge cases exist when appropriate.

---

## 19. Final Product Standard

The finished agent should be able to handle this interaction well:

```text
Tutor:
Return each customer and the total amount they spent.
Include only customers whose total exceeds 500.

Learner:
SELECT customer_id, SUM(total_amount)
FROM orders
WHERE SUM(total_amount) > 500
GROUP BY customer_id;

Evaluator:
runtime error / aggregate used in WHERE

Tutor:
You're grouping correctly, but the total doesn't exist yet when WHERE is evaluated.
WHERE filters individual order rows before GROUP BY.

Which clause filters groups after aggregation?

Learner:
SELECT customer_id, SUM(total_amount)
FROM orders
GROUP BY customer_id
HAVING SUM(total_amount) > 500;

Evaluator:
correct

Tutor:
Correct. HAVING is the key here because you're filtering an aggregate after grouping.

Next, let's join those customer IDs to customer names.
```

That interaction demonstrates the core product:

- real execution,
- precise diagnosis,
- minimal hint,
- learner retry,
- conceptual explanation,
- adaptive progression.

Build everything else around making this loop excellent.
