from fastapi import APIRouter

from app.api import exercises, progress, sessions, sql

api_router = APIRouter()
api_router.include_router(sessions.router)
api_router.include_router(exercises.router)
api_router.include_router(sql.router)
api_router.include_router(progress.router)
