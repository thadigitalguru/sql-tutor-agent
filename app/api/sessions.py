from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agent.orchestrator import ActionResult
from app.api.deps import get_orchestrator

router = APIRouter(tags=["sessions"])


class StartSessionRequest(BaseModel):
    learner_id: str | None = None
    sql_level: str | None = None
    dialect: str | None = None
    goal: str | None = None
    resume: bool = True


def serialize(result: ActionResult) -> dict:
    payload = {
        "session": result.session,
        "exercise": result.exercise,
        "schema": result.schema.model_dump() if result.schema else None,
        "evaluation": result.evaluation.model_dump() if result.evaluation else None,
        "result": result.result,
        "feedback": result.feedback,
        "hint": result.hint,
        "progress": result.progress,
        "onboarding": result.onboarding,
    }
    return payload


@router.post("/sessions")
def create_session(body: StartSessionRequest) -> dict:
    orch = get_orchestrator()
    result = orch.start_session(
        learner_id=body.learner_id,
        sql_level=body.sql_level,
        dialect=body.dialect,
        goal=body.goal,
        resume=body.resume,
    )
    return serialize(result)


@router.get("/sessions/{session_id}")
def read_session(session_id: str) -> dict:
    orch = get_orchestrator()
    try:
        return serialize(orch.get_session(session_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
