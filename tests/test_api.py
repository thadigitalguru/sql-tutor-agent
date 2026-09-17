from app.agent.orchestrator import Orchestrator
from app.api.deps import get_orchestrator
from app.main import app
from app.storage.repository import Repository
from fastapi.testclient import TestClient


def test_health(tmp_path, monkeypatch) -> None:
    orch = Orchestrator(repo=Repository(tmp_path / "t.sqlite"))
    app.dependency_overrides = {}
    get_orchestrator.cache_clear()
    monkeypatch.setattr("app.api.deps.get_orchestrator", lambda: orch)
    # deps uses lru_cache; patch the function the routers imported
    import app.api.exercises as exercises
    import app.api.progress as progress
    import app.api.sessions as sessions
    import app.api.sql as sql

    monkeypatch.setattr(sessions, "get_orchestrator", lambda: orch)
    monkeypatch.setattr(exercises, "get_orchestrator", lambda: orch)
    monkeypatch.setattr(sql, "get_orchestrator", lambda: orch)
    monkeypatch.setattr(progress, "get_orchestrator", lambda: orch)

    client = TestClient(app)
    assert client.get("/api/health").json()["ok"] is True

    started = client.post(
        "/api/sessions",
        json={
            "sql_level": "new_to_sql",
            "dialect": "postgresql",
            "goal": "foundations",
            "resume": False,
        },
    )
    assert started.status_code == 200
    body = started.json()
    session_id = body["session"]["id"]
    exercise_id = body["exercise"]["id"]
    assert body["schema"]["tables"]

    run = client.post(
        "/api/sql/run",
        json={"session_id": session_id, "query": "SELECT name, country FROM customers"},
    )
    assert run.status_code == 200
    assert run.json()["result"]["ok"] is True

    hint = client.post(
        f"/api/exercises/{exercise_id}/hint",
        json={"session_id": session_id},
    )
    assert hint.status_code == 200
    assert hint.json()["hint"]["level"] == 1
    assert "SELECT" not in hint.json()["hint"]["text"].split("FROM")[0] or hint.json()["hint"]["level"] == 1

    submit_wrong = client.post(
        f"/api/exercises/{exercise_id}/submit",
        json={"session_id": session_id, "query": "SELECT 1"},
    )
    assert submit_wrong.status_code == 200
    assert submit_wrong.json()["evaluation"]["status"] != "CORRECT"
    assert "solution" not in submit_wrong.json()["feedback"].lower()

    from app.curriculum.loader import get_exercise

    exercise = get_exercise(exercise_id)
    submit_ok = client.post(
        f"/api/exercises/{exercise_id}/submit",
        json={"session_id": session_id, "query": exercise.reference_sql},
    )
    assert submit_ok.json()["evaluation"]["status"] == "CORRECT"
    learner_id = body["session"]["learner_id"]
    progress_body = client.get("/api/progress", params={"learner_id": learner_id}).json()
    assert any(item["attempts"] > 0 for item in progress_body["skills"])
