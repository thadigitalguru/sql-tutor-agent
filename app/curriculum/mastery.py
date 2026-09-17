"""Simple clamped mastery updates. The LLM never assigns scores."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain import SkillState, SubmissionStatus

SUCCESS = {SubmissionStatus.CORRECT, SubmissionStatus.CORRECT_WITH_IMPROVEMENT}

# Architecture spec §11
DELTA_FIRST_TRY_NO_HINT = 0.12
DELTA_SMALL_HINT = 0.08
DELTA_STRONG_HINT = 0.04
DELTA_SOLUTION = 0.01
DELTA_INCORRECT = -0.02


def evidence_delta(
    *,
    status: SubmissionStatus,
    attempt_count: int,
    hint_level: int,
    solution_revealed: bool,
    is_review: bool = False,
) -> float:
    if status not in SUCCESS:
        return DELTA_INCORRECT
    if solution_revealed or hint_level >= 5:
        return DELTA_SOLUTION
    if hint_level >= 3:
        return DELTA_STRONG_HINT
    if hint_level >= 1:
        return DELTA_SMALL_HINT
    if attempt_count <= 1:
        bonus = 0.02 if is_review else 0.0
        return DELTA_FIRST_TRY_NO_HINT + bonus
    return DELTA_SMALL_HINT


def apply_mastery_delta(current: float, delta: float) -> float:
    return min(1.0, max(0.0, round(current + delta, 4)))


def update_skill_state(
    state: SkillState,
    *,
    status: SubmissionStatus,
    attempt_count: int,
    hint_level: int,
    solution_revealed: bool,
    exercise_id: str,
    is_review: bool = False,
    now: datetime | None = None,
) -> SkillState:
    now = now or datetime.now(UTC)
    delta = evidence_delta(
        status=status,
        attempt_count=attempt_count,
        hint_level=hint_level,
        solution_revealed=solution_revealed,
        is_review=is_review,
    )
    success = status in SUCCESS
    demonstrated = list(state.demonstrated_on)
    if success and exercise_id not in demonstrated:
        demonstrated.append(exercise_id)

    review_successes = state.review_successes + (1 if success and is_review else 0)
    return SkillState(
        skill_id=state.skill_id,
        mastery=apply_mastery_delta(state.mastery, delta),
        attempts=state.attempts + 1,
        successful_attempts=state.successful_attempts + (1 if success else 0),
        recent_success_streak=(state.recent_success_streak + 1) if success else 0,
        last_practiced_at=now,
        highest_hint_used_recently=max(state.highest_hint_used_recently, hint_level),
        review_successes=review_successes,
        demonstrated_on=demonstrated,
    )


def is_mastered(state: SkillState) -> bool:
    """Mastered requires high score, multiple exercises, and a later review."""
    return state.mastery >= 0.95 and len(state.demonstrated_on) >= 2 and state.review_successes >= 1
