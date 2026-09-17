"""Pick the next exercise from mastery, prerequisites, goal, and recency."""

from __future__ import annotations

from datetime import UTC, datetime

from app.curriculum.loader import load_exercises
from app.curriculum.mastery import is_mastered
from app.curriculum.skills import skill_prerequisites
from app.domain import Exercise, Goal, SkillState, SqlLevel

LEVEL_TO_DIFFICULTY = {
    SqlLevel.BEGINNER: 2,
    SqlLevel.INTERMEDIATE: 3,
    SqlLevel.ADVANCED: 5,
}

GOAL_SKILLS: dict[Goal, set[str]] = {
    Goal.FOUNDATIONS: {
        "select_basic",
        "filter_where",
        "boolean_logic",
        "order_by",
        "null_handling",
        "aggregate_count",
        "aggregate_sum",
        "group_by",
        "having",
        "inner_join",
        "left_join",
    },
    Goal.ANALYTICS: {
        "group_by",
        "having",
        "inner_join",
        "left_join",
        "subquery",
        "cte",
        "case_expression",
        "date_operations",
        "window_functions",
        "sessionization",
        "data_grain",
    },
    Goal.INTERVIEWS: {
        "group_by",
        "having",
        "inner_join",
        "left_join",
        "subquery",
        "window_functions",
        "anti_join",
        "recursive_cte",
        "scd_point_in_time",
        "sessionization",
    },
    Goal.DATABASE_WORK: {
        "anti_join",
        "recursive_cte",
        "json_semi_structured",
        "keyset_pagination",
        "cte",
        "window_functions",
        "effective_dated",
        "data_grain",
    },
    Goal.AI_ENGINEERING: {
        "inference_ops",
        "feature_store",
        "train_eval_split",
        "eval_metrics",
        "rag_retrieval",
        "cost_attribution",
        "sessionization",
        "json_semi_structured",
        "window_functions",
    },
    Goal.DATA_ARCHITECTURE: {
        "star_schema",
        "data_grain",
        "scd_point_in_time",
        "bridge_tables",
        "effective_dated",
        "recursive_cte",
        "window_functions",
    },
    Goal.REFRESH: set(),
}


def select_next_exercise(
    *,
    mastery: dict[str, SkillState],
    goal: Goal,
    sql_level: SqlLevel,
    completed_exercise_ids: set[str],
    recent_failures: int = 0,
    prefer_review: bool = False,
    now: datetime | None = None,
) -> Exercise | None:
    now = now or datetime.now(UTC)
    target_difficulty = LEVEL_TO_DIFFICULTY[sql_level]
    if recent_failures >= 3:
        target_difficulty = max(1, target_difficulty - 1)

    candidates = []
    for exercise in load_exercises():
        if not _prerequisites_ready(exercise, mastery):
            continue
        score = _priority(
            exercise,
            mastery=mastery,
            goal=goal,
            target_difficulty=target_difficulty,
            completed_exercise_ids=completed_exercise_ids,
            prefer_review=prefer_review,
            now=now,
        )
        if score <= 0:
            continue
        candidates.append((score, exercise.id, exercise))

    if not candidates:
        remaining = [
            ex for ex in load_exercises() if ex.id not in completed_exercise_ids and _prerequisites_ready(ex, mastery)
        ]
        return remaining[0] if remaining else None

    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2]


def _prerequisites_ready(exercise: Exercise, mastery: dict[str, SkillState]) -> bool:
    needed = list(exercise.prerequisites) + list(skill_prerequisites(exercise.primary_skill))
    for skill_id in needed:
        if skill_id == exercise.primary_skill:
            continue
        state = mastery.get(skill_id)
        if _skill_unlocked(state):
            continue
        if skill_id == "select_basic" and exercise.primary_skill == "select_basic":
            continue
        return False
    return True


def _skill_unlocked(state: SkillState | None) -> bool:
    if state is None:
        return False
    return state.successful_attempts >= 1 or state.mastery >= 0.12


def _priority(
    exercise: Exercise,
    *,
    mastery: dict[str, SkillState],
    goal: Goal,
    target_difficulty: int,
    completed_exercise_ids: set[str],
    prefer_review: bool,
    now: datetime,
) -> float:
    state = mastery.get(exercise.primary_skill) or SkillState(skill_id=exercise.primary_skill)
    completed = exercise.id in completed_exercise_ids
    if completed and not prefer_review and not _review_due(state, now):
        return 0.0

    goal_skills = GOAL_SKILLS.get(goal, set())
    goal_relevance = 1.0 if not goal_skills or exercise.primary_skill in goal_skills else 0.55
    weakness = 1.0 - state.mastery
    review_due = _review_due_score(state, now)
    difficulty_fit = 1.0 - min(1.0, abs(exercise.difficulty - target_difficulty) / 4)
    novelty = 0.35 if completed else 1.0
    hint_penalty = 0.85 if state.highest_hint_used_recently >= 4 else 1.0
    mastered_skip = 0.15 if is_mastered(state) and not _review_due(state, now) else 1.0
    return (
        goal_relevance
        * max(weakness, 0.15)
        * max(review_due, 0.4 if not completed else review_due)
        * difficulty_fit
        * novelty
        * hint_penalty
        * mastered_skip
    )


def _review_due(state: SkillState, now: datetime) -> bool:
    return _review_due_score(state, now) >= 0.8


def _review_due_score(state: SkillState, now: datetime) -> float:
    if state.last_practiced_at is None:
        return 0.5
    practiced = state.last_practiced_at
    if practiced.tzinfo is None:
        practiced = practiced.replace(tzinfo=UTC)
    days = max(0.0, (now - practiced).total_seconds() / 86400)
    if state.mastery >= 0.8:
        schedule = (1, 3, 7, 14, 30)
        closest = min(schedule, key=lambda d: abs(d - days))
        return max(0.2, 1.0 - abs(closest - days) / 10) if days >= 1 else 0.2
    if days >= 1:
        return min(1.0, 0.4 + days / 7)
    return 0.3
