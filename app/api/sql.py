from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_orchestrator
from app.api.sessions import serialize

router = APIRouter(tags=["sql"])


class RunSqlBody(BaseModel):
    session_id: str
    query: str


class PreviewQuery(BaseModel):
    limit: int = Field(default=5, ge=1, le=20)


@router.post("/sql/run")
def run_sql(body: RunSqlBody) -> dict:
    orch = get_orchestrator()
    try:
        return serialize(orch.run_sql(body.session_id, body.query))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/schema/{dataset_id}")
def read_schema(dataset_id: str) -> dict:
    try:
        return get_orchestrator().schema(dataset_id).model_dump()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tables/{table}/preview")
def preview(table: str, dataset_id: str, limit: int = 5) -> dict:
    return get_orchestrator().preview(dataset_id, table, limit=limit)
