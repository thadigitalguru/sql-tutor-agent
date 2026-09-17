from functools import lru_cache

from app.agent.orchestrator import Orchestrator
from app.storage.repository import Repository


@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:
    return Orchestrator(repo=Repository())
