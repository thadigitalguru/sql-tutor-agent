import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.config import settings

app = FastAPI(
    title="SQL Tutor",
    description="Adaptive SQL tutor with a deterministic sandbox and evaluator.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "llm": settings.llm_enabled}


web_dir = settings.web_dir
if web_dir.is_dir():
    assets = web_dir / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(web_dir / "index.html")

    @app.get("/{path:path}")
    def spa_fallback(path: str) -> FileResponse:
        if path.startswith(("api", "docs", "redoc", "openapi.json")):
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not found")
        candidate = web_dir / path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(web_dir / "index.html")


def run() -> None:
    settings.app_data_dir.mkdir(parents=True, exist_ok=True)
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    run()
