from fastapi import APIRouter, HTTPException

from app.api.deps import get_orchestrator

router = APIRouter(tags=["progress"])


@router.get("/progress")
def read_progress(learner_id: str) -> dict:
    orch = get_orchestrator()
    if orch.repo.get_learner(learner_id) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return orch.progress(learner_id)
