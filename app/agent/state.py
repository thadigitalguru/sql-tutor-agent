from __future__ import annotations

from dataclasses import dataclass, field

from app.domain import LessonState


@dataclass
class SessionRuntime:
    session_id: str
    learner_id: str
    lesson_state: LessonState = LessonState.INTRO
    current_exercise_id: str | None = None
    attempt_count: int = 0
    hint_level: int = 0
    solution_revealed: bool = False
    failed_attempts: int = 0
    onboarding_complete: bool = False
    recent_summary: str = ""
    messages: list[dict[str, str]] = field(default_factory=list)
