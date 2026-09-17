# Architecture

The SQL Tutor is a **deterministic learning system with an LLM teacher**.
The model explains, hints, and diagnoses in language. Code owns execution,
correctness, safety, mastery, and lesson state.

```text
Web UI  →  FastAPI orchestrator  →  LLM tutor (optional)
                 │
                 ├── SQLite progress store
                 └── Isolated SQLite sandbox + result evaluator
```

## Responsibilities

| Concern | Owner |
|---|---|
| Teach, hint, explain, summarize | LLM tutor, with template fallback |
| Parse/execute learner SQL | `app/sandbox` |
| Decide correctness | Result-set evaluator |
| Hint level, attempts, lesson state | Orchestrator |
| Mastery scores | Deterministic mastery engine |
| Next exercise | Curriculum selector |
| Sandbox permissions | Safety layer (parser + allowlist + DB flags) |

## Stack (MVP)

- Python 3.12+ / FastAPI / Pydantic
- SQLite for tutor state **and** per-request sandbox clones
- sqlglot for SQL parsing and safety
- YAML curriculum outside Python
- Static SPA (`web/`) with CodeMirror
- OpenAI-compatible Chat Completions when `LLM_API_KEY` is set

## Key flows

**Run:** validate → execute → return rows. No mastery change.

**Submit:** validate → execute → compare to reference result (and hidden
variants) → diagnose → record attempt → update mastery → generate feedback.

**Hint:** increment `hint_level` by one → return that ladder step.

## Sandbox isolation

Each execution opens a fresh in-memory SQLite database, applies the dataset
schema/seed, then sets `PRAGMA query_only = ON`. Learner SQL never touches
the tutor state database.

## Dialect decision

The product teaches the learner's chosen dialect. The MVP sandbox is SQLite.
When the learner selects PostgreSQL (the default for "Not sure"), the tutor
teaches PostgreSQL-style SQL and notes SQLite compatibility limits instead of
silently teaching engine-specific syntax as universal.
