# SQL Coach

A personal SQL tutor that teaches by doing: **explain briefly → you write SQL →
the sandbox executes it → a deterministic grader checks the rows → you get the
smallest useful hint → retry → mastery updates**.

The LLM (optional) teaches. Code executes SQL, evaluates results, enforces
safety, and tracks state.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # optional; the app runs without an LLM key
sql-tutor
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Alternatively:

```bash
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
pytest
ruff check app tests
```

## Tracks

- **Foundations** — SELECT through joins on the ecommerce dataset.
- **SQL for AI / ML engineering** — point-in-time features, inference logs,
  temporal train/eval splits, offline eval, RAG metadata filters, token cost.
- **Data architecture & modeling** — star schema, fact grain, SCD Type 2,
  bridge tables, effective-dated memberships, org hierarchies, sessionization.
- **Database engineering** — anti-joins, keyset pagination, JSON, recursive CTEs.

Pick **Mid-level / senior practitioner** at onboarding to skip keyword drills
and start on the `platform` warehouse dataset.

## How it works

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and
[docs/DECISIONS.md](docs/DECISIONS.md).

- Learner SQL runs in an isolated in-memory SQLite clone of the exercise dataset.
- Only a single `SELECT` / `WITH` / `UNION` is allowed.
- Correctness is result-set comparison, not string matching against the reference query.
- Hint levels increase one step at a time. The full solution is not shown on the first failure.
- Mastery is a clamped numeric model from the architecture spec.

## Configuration

Copy `.env.example` to `.env`. Leave `LLM_API_KEY` empty to use deterministic
tutor feedback. Any OpenAI-compatible Chat Completions endpoint works when set.

Never commit `.env`.

## Current status

See [docs/PROGRESS.md](docs/PROGRESS.md).
