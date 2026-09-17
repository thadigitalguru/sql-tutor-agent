from app.agent.orchestrator import Orchestrator
from app.curriculum.loader import get_exercise
from app.domain import SubmissionStatus
from app.storage.repository import Repository


def test_hint_ladder_does_not_reveal_solution_first(tmp_path) -> None:
    orch = Orchestrator(repo=Repository(tmp_path / "t.sqlite"))
    started = orch.start_session(
        sql_level="beginner",
        dialect="postgresql",
        goal="foundations",
        resume=False,
    )
    session_id = started.session["id"]
    first = orch.hint(session_id)
    assert first.hint["level"] == 1
    assert "SELECT" not in first.hint["text"] or "FROM ..." in first.hint["text"]
    assert first.hint["solution_revealed"] is False

    second = orch.hint(session_id)
    assert second.hint["level"] == 2
    third = orch.hint(session_id)
    assert third.hint["level"] == 3
    fourth = orch.hint(session_id)
    assert fourth.hint["level"] == 4
    fifth = orch.hint(session_id)
    # Not enough failed attempts yet, so solution stays closed.
    assert fifth.hint["level"] == 4
    assert fifth.hint["solution_revealed"] is False

    explicit = orch.hint(session_id, want_solution=True)
    assert explicit.hint["level"] == 5
    assert explicit.hint["solution_revealed"] is True
    assert "FROM" in explicit.hint["text"]


def test_submit_updates_mastery_and_allows_retry(tmp_path) -> None:
    orch = Orchestrator(repo=Repository(tmp_path / "t.sqlite"))
    started = orch.start_session(sql_level="beginner", dialect="sqlite", goal="foundations", resume=False)
    session_id = started.session["id"]
    exercise_id = started.exercise["id"]
    wrong = orch.submit(session_id, "SELECT 1")
    assert wrong.evaluation.status != SubmissionStatus.CORRECT
    assert wrong.session["attempt_count"] == 1
    exercise = get_exercise(exercise_id)
    ok = orch.submit(session_id, exercise.reference_sql)
    assert ok.evaluation.status == SubmissionStatus.CORRECT
    skill = next(s for s in ok.progress["skills"] if s["skill_id"] == exercise.primary_skill)
    assert skill["mastery"] > 0
    nxt = orch.next_exercise(session_id)
    assert nxt.exercise is not None
    assert nxt.exercise["id"] != exercise_id


def test_mid_senior_ai_track_skips_select_basics(tmp_path) -> None:
    orch = Orchestrator(repo=Repository(tmp_path / "t.sqlite"))
    started = orch.start_session(
        sql_level="mid_senior",
        dialect="postgresql",
        goal="ai_engineering",
        resume=False,
    )
    assert started.exercise is not None
    assert started.exercise["primary_skill"] in {
        "inference_ops",
        "feature_store",
        "train_eval_split",
        "eval_metrics",
        "rag_retrieval",
        "cost_attribution",
        "sessionization",
        "json_semi_structured",
        "window_functions",
    }
    assert started.exercise["difficulty"] >= 4
    assert started.schema is not None
    assert started.schema.dataset_id == "platform"
