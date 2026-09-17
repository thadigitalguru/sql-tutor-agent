# Architecture decisions

Recorded so parallel work stays consistent. Prefer the simplest choice that
matches the four product specs.

## AD-001 — One process, two SQLite roles

Tutor state lives in `data/tutor.sqlite`. Exercise data is loaded into a
throwaway in-memory SQLite connection per execution. This is enough isolation
for MVP and avoids running a database server.

## AD-002 — Result-set grading, never string diffs

Reference SQL is server-side only. The evaluator runs it, caches the expected
rows, and compares the learner's result as a multiset (or sequenced rows when
`order_matters`).

## AD-003 — sqlglot + DB permissions, not regex-only safety

The parser must accept a single SELECT / WITH-SELECT / UNION. The connection
is query-only after seed. Regex denylist is a backup, not the primary control.

## AD-004 — LLM is optional at runtime

If no API key is configured, the orchestrator still runs the full loop using
exercise hints and diagnostic templates. This keeps every commit runnable.

## AD-005 — `shipped_at` on `orders`

The curriculum spec uses `shipped_at` to teach NULL. The ecommerce dataset
adds this nullable column even though the short table sketch omitted it.

## AD-006 — Static SPA instead of Next.js or Streamlit

FastAPI serves `web/`. One install command, a real SQL editor, no extra
frontend toolchain in MVP. Revisit if the UI outgrows a single-page app.

## AD-007 — Mastery formula from the architecture spec

Use the documented deltas (+0.12 / +0.08 / +0.04 / +0.01 / -0.02) and clamp
to `[0, 1]`. A skill is not labeled mastered until multiple successes plus a
later review (see mastery engine).

## AD-008 — Teach PostgreSQL, execute SQLite in MVP

Default dialect is PostgreSQL when the learner is unsure. Sandbox limitations
are disclosed; we do not pretend SQLite syntax is portable.

## AD-009 — Hidden variants as extra seed files

Important join / NULL / aggregation exercises may declare `hidden_variants`.
Each variant is a second seed applied to the same schema. The learner query
must pass every variant.

## AD-010 — Prerequisite unlock after one independent success

A skill unlocks dependents after `successful_attempts >= 1` (or mastery ≥ 0.12).
Mastery still cannot be labeled "Mastered" until multiple exercises plus a review.
This keeps the beginner path moving without treating one success as competence.

