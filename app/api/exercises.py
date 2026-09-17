from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import get_orchestrator
from app.api.sessions import serialize
from app.curriculum.loader import CurriculumError

router = APIRouter(tags=["exercises"])


class QueryBody(BaseModel):
    query: str
    session_id: str


class HintBody(BaseModel):
    session_id: str
    stronger: bool = False
    want_solution: bool = False


class NextBody(BaseModel):
    session_id: str


@router.get("/lessons/next")
def next_lesson(session_id: str) -> dict:
    orch = get_orchestrator()
    try:
        return serialize(orch.next_exercise(session_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc


@router.post("/lessons/next")
def next_lesson_post(body: NextBody) -> dict:
    return next_lesson(body.session_id)


@router.get("/exercises")
def list_exercises() -> dict:
    return {"exercises": get_orchestrator().list_exercises()}


@router.get("/exercises/{exercise_id}")
def read_exercise(exercise_id: str) -> dict:
    try:
        return get_orchestrator().public_exercise(exercise_id)
    except CurriculumError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/exercises/{exercise_id}/submit")
def submit_exercise(exercise_id: str, body: QueryBody) -> dict:
    orch = get_orchestrator()
    try:
        current = orch.get_session(body.session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    if current.exercise and current.exercise["id"] != exercise_id:
        raise HTTPException(status_code=409, detail="This is not the active exercise.")
    try:
        return serialize(orch.submit(body.session_id, body.query))
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/exercises/{exercise_id}/hint")
def hint_exercise(exercise_id: str, body: HintBody) -> dict:
    orch = get_orchestrator()
    try:
        return serialize(orch.hint(body.session_id, stronger=body.stronger, want_solution=body.want_solution))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
