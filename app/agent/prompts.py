from app.config import ROOT_DIR

PROMPT_PATH = ROOT_DIR / "02_TUTOR_SYSTEM_PROMPT.md"


def system_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    marker = "## SYSTEM PROMPT"
    if marker in text:
        text = text.split(marker, 1)[1].strip()
    return text + "\n\n" + TOOL_POLICY


TOOL_POLICY = """
## Runtime contract for this deployment

You are SQL Coach inside a product with a deterministic sandbox.

- Never claim a query ran unless a tool result says it ran.
- Never decide correctness yourself when evaluate_submission is available.
- Never invent tables or columns. Call get_schema or preview_table.
- Never reveal reference SQL unless hint_level is 5 or the learner asked for the solution.
- Keep ordinary feedback to: diagnosis, why, next step.
- The sandbox engine is SQLite. Teach the learner's selected dialect.
  If they chose PostgreSQL, teach PostgreSQL and mention SQLite sandbox
  limits only when they matter.
- Do not request DROP, DELETE, TRUNCATE, or other destructive SQL in beginner lessons.
"""


def syntax_feedback(engine_message: str) -> str:
    lowered = (engine_message or "").lower()
    if "near" in lowered and "syntax" in lowered:
        return (
            "The database hit a syntax error before it could run the query. "
            "Look at the token mentioned in the engine message — often an extra comma, "
            "a missing keyword, or a name the parser did not expect. "
            f"Engine detail: {engine_message}"
        )
    return f"The query did not parse. Check keywords, commas, and quoting. Engine detail: {engine_message}"


def template_feedback(
    *,
    status: str,
    tags: list[str],
    comparison_notes: list[str],
    engine_message: str | None,
    hint_text: str | None,
    correct_explanation: str | None,
    quality_notes: list | None = None,
) -> str:
    if status in {"CORRECT", "CORRECT_WITH_IMPROVEMENT"}:
        why = correct_explanation or "The result set matches the required rows."
        body = f"Correct.\n\nWhy it works:\n{why}"
        if quality_notes:
            lines = []
            for note in quality_notes:
                kind = getattr(note, "kind", None) or note.get("kind")
                message = getattr(note, "message", None) or note.get("message")
                lines.append(f"- **{kind}:** {message}")
            body += "\n\nThe rows are right. A few quality notes (these do not change the grade):\n" + "\n".join(lines)
        return body
    if status == "SYNTAX_ERROR":
        return syntax_feedback(engine_message or "syntax error")
    if status == "UNSAFE":
        return "That statement is blocked in this learning sandbox. Use a single SELECT (WITH and UNION are fine)."
    if status == "RUNTIME_ERROR":
        body = _runtime_story(tags, engine_message)
        nxt = hint_text or "Fix the error, then run the query again."
        return f"Status: runtime error\n\nWhat happened:\n{body}\n\nNext step:\n{nxt}"

    what, why = _incorrect_story(tags, comparison_notes)
    nxt = hint_text or "Change one thing and submit again."
    return f"Status: {status.lower().replace('_', ' ')}\n\nWhat happened:\n{what}\n\nWhy:\n{why}\n\nNext step:\n{nxt}"


def _runtime_story(tags: list[str], engine_message: str | None) -> str:
    if "having_vs_where" in tags:
        return (
            "An aggregate was used where SQL only allows row-level conditions. "
            "WHERE runs before grouping, so SUM(...) is not available there yet."
        )
    if "grouping" in tags:
        return "The database expected either an aggregate or a GROUP BY for a non-aggregated column."
    if "wrong_column" in tags:
        return "A column name in the query is not in the current schema."
    if "wrong_table" in tags:
        return "A table name in the query is not in the current schema."
    return engine_message or "The database could not execute the query."


def _incorrect_story(tags: list[str], notes: list[str]) -> tuple[str, str]:
    if "grouping" in tags:
        return (
            "The query ran, but it does not summarize one row per group.",
            "An aggregate combines rows. GROUP BY tells SQL which rows belong together.",
        )
    if "having_vs_where" in tags:
        return (
            "The filter is being applied at the wrong stage of the query.",
            "WHERE filters individual rows before grouping. HAVING filters groups after aggregation.",
        )
    if "missing_join" in tags:
        return (
            "The result cannot come from a single table.",
            "The columns you need live in related tables, so the rows have to be matched.",
        )
    if "left_join_filter" in tags:
        return (
            "Unmatched left-side rows are being dropped after the outer join.",
            "A WHERE condition on the right-hand table turns a LEFT JOIN into an inner join.",
        )
    if "null_handling" in tags:
        return (
            "Missing values are not being tested the way SQL treats NULL.",
            "NULL means unknown. `= NULL` is never true; use IS NULL or IS NOT NULL.",
        )
    if "ordering" in tags or "order" in notes:
        return (
            "The rows are present, but not in the required order.",
            "ORDER BY defines the sequence. DESC puts larger values first.",
        )
    if "hidden_case" in tags or "hidden_variant" in notes:
        return (
            "The query works on the visible sample but fails a hidden edge case.",
            "Correct SQL has to handle missing matches, NULLs, and extra rows — not only the preview you can see.",
        )
    if "column_count" in notes:
        return (
            "The query returns a different number of columns than the task asks for.",
            "Return only the requested columns, in a comparable shape.",
        )
    if "values" in notes:
        return (
            "The query runs, but the rows do not match the required result.",
            "Compare the filters, joins, and grouping against the wording of the task.",
        )
    return (
        "The result is not correct yet.",
        "Look at which rows were kept or dropped compared with the task.",
    )
