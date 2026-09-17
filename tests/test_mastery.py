from datetime import UTC, datetime, timedelta

from app.curriculum.mastery import apply_mastery_delta, is_mastered, update_skill_state
from app.curriculum.selector import select_next_exercise
from app.domain import Goal, SkillState, SqlLevel, SubmissionStatus


def test_deltas_clamp() -> None:
    assert apply_mastery_delta(0.99, 0.12) == 1.0
    assert apply_mastery_delta(0.01, -0.02) == 0.0


def test_first_try_increases_more_than_hinted() -> None:
    base = SkillState(skill_id="group_by")
    first = update_skill_state(
        base,
        status=SubmissionStatus.CORRECT,
        attempt_count=1,
        hint_level=0,
        solution_revealed=False,
        exercise_id="a",
    )
    hinted = update_skill_state(
        base,
        status=SubmissionStatus.CORRECT,
        attempt_count=3,
        hint_level=4,
        solution_revealed=False,
        exercise_id="a",
    )
    assert first.mastery > hinted.mastery


def test_incorrect_does_not_crash_and_decreases_lightly() -> None:
    state = SkillState(skill_id="group_by", mastery=0.5)
    updated = update_skill_state(
        state,
        status=SubmissionStatus.INCORRECT,
        attempt_count=2,
        hint_level=1,
        solution_revealed=False,
        exercise_id="a",
    )
    assert updated.mastery == 0.48
    assert updated.recent_success_streak == 0


def test_not_mastered_after_one_success() -> None:
    state = update_skill_state(
        SkillState(skill_id="group_by", mastery=0.94),
        status=SubmissionStatus.CORRECT,
        attempt_count=1,
        hint_level=0,
        solution_revealed=False,
        exercise_id="only_one",
    )
    assert state.mastery == 1.0
    assert is_mastered(state) is False


def test_selector_starts_with_select() -> None:
    exercise = select_next_exercise(
        mastery={},
        goal=Goal.FOUNDATIONS,
        sql_level=SqlLevel.BEGINNER,
        completed_exercise_ids=set(),
    )
    assert exercise is not None
    assert exercise.primary_skill == "select_basic"


def test_selector_skips_completed_until_review() -> None:
    now = datetime.now(UTC)
    mastery = {
        "select_basic": SkillState(
            skill_id="select_basic",
            mastery=0.7,
            attempts=2,
            successful_attempts=2,
            last_practiced_at=now,
            demonstrated_on=["sel_001"],
        )
    }
    exercise = select_next_exercise(
        mastery=mastery,
        goal=Goal.FOUNDATIONS,
        sql_level=SqlLevel.BEGINNER,
        completed_exercise_ids={"sel_001"},
        now=now,
    )
    assert exercise is not None
    assert exercise.id != "sel_001"


def test_review_due_can_resurface() -> None:
    old = datetime.now(UTC) - timedelta(days=8)
    mastery = {
        "select_basic": SkillState(
            skill_id="select_basic",
            mastery=0.9,
            attempts=4,
            successful_attempts=4,
            last_practiced_at=old,
            demonstrated_on=["sel_001"],
        )
    }
    exercise = select_next_exercise(
        mastery=mastery,
        goal=Goal.FOUNDATIONS,
        sql_level=SqlLevel.BEGINNER,
        completed_exercise_ids={"sel_001"},
        prefer_review=True,
        now=datetime.now(UTC),
    )
    assert exercise is not None
