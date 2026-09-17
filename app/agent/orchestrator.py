"""Deterministic lesson loop. The LLM never owns correctness or mastery."""

from __future__ import annotations

from dataclasses import dataclass

from app.agent.prompts import template_feedback
from app.agent.tutor import TutorClient
from app.config import settings
from app.curriculum.loader import get_exercise, load_exercises
from app.curriculum.mastery import update_skill_state
from app.curriculum.selector import select_next_exercise
from app.curriculum.skills import SKILLS
from app.domain import (
    Dialect,
    Evaluation,
    Exercise,
    Goal,
    LessonState,
    SchemaPayload,
    SkillState,
    SqlLevel,
    SubmissionStatus,
    mastery_band,
)
from app.sandbox.evaluator import evaluate_exercise
from app.sandbox.executor import run_sql
from app.sandbox.schema import get_schema, preview_table
from app.storage.repository import Repository

SUCCESS = {SubmissionStatus.CORRECT, SubmissionStatus.CORRECT_WITH_IMPROVEMENT}

LEVEL_MAP = {
    "new_to_sql": SqlLevel.BEGINNER,
    "beginner": SqlLevel.BEGINNER,
    "select_where": SqlLevel.BEGINNER,
    "know_basic_select_where": SqlLevel.BEGINNER,
    "joins_grouping": SqlLevel.INTERMEDIATE,
    "intermediate": SqlLevel.INTERMEDIATE,
    "advanced": SqlLevel.ADVANCED,
}

DIALECT_MAP = {
    "postgresql": Dialect.POSTGRESQL,
    "postgres": Dialect.POSTGRESQL,
    "sqlite": Dialect.SQLITE,
    "mysql": Dialect.MYSQL,
    "sqlserver": Dialect.SQLSERVER,
    "sql_server": Dialect.SQLSERVER,
    "not_sure": Dialect.POSTGRESQL,
}

GOAL_MAP = {
    "learn_sql_from_scratch": Goal.FOUNDATIONS,
    "foundations": Goal.FOUNDATIONS,
    "data_analysis": Goal.ANALYTICS,
    "analytics": Goal.ANALYTICS,
    "interview_preparation": Goal.INTERVIEWS,
    "interviews": Goal.INTERVIEWS,
    "work_with_databases": Goal.DATABASE_WORK,
    "database_work": Goal.DATABASE_WORK,
    "refresh": Goal.REFRESH,
    "refresh_improve_sql": Goal.REFRESH,
}


@dataclass
class ActionResult:
    session: dict
    exercise: dict | None
    schema: SchemaPayload | None
    evaluation: Evaluation | None
    result: dict | None
    feedback: str
    hint: dict | None
    progress: dict | None
    onboarding: bool = False


class Orchestrator:
    def __init__(self, repo: Repository | None = None, tutor: TutorClient | None = None) -> None:
        self.repo = repo or Repository()
        self.tutor = tutor or TutorClient()

    def start_session(
        self,
        *,
        learner_id: str | None = None,
        sql_level: str | None = None,
        dialect: str | None = None,
        goal: str | None = None,
        resume: bool = True,
    ) -> ActionResult:
        if learner_id and self.repo.get_learner(learner_id):
            if sql_level or dialect or goal:
                self.repo.update_learner(
                    learner_id,
                    sql_level=LEVEL_MAP.get((sql_level or "").lower(), None),
                    dialect=DIALECT_MAP.get((dialect or "").lower(), None),
                    goal=GOAL_MAP.get((goal or "").lower(), None),
                )
        else:
            learner_id = self.repo.create_learner(
                sql_level=LEVEL_MAP.get((sql_level or "beginner").lower(), SqlLevel.BEGINNER),
                dialect=DIALECT_MAP.get((dialect or "not_sure").lower(), Dialect.POSTGRESQL),
                goal=GOAL_MAP.get((goal or "foundations").lower(), Goal.FOUNDATIONS),
            )

        existing = self.repo.latest_session(learner_id) if resume else None
        if existing and existing.get("current_exercise_id") and not existing.get("ended_at"):
            session_id = existing["id"]
            exercise = get_exercise(existing["current_exercise_id"])
            schema = self._schema_for(exercise)
            learner = self.repo.get_learner(learner_id)
            feedback = (
                f"Welcome back. Last time you were on **{exercise.title}** "
                f"({exercise.primary_skill.replace('_', ' ')}). "
                "Let's continue from this exercise."
            )
            if existing.get("lesson_state") in {LessonState.REVIEW.value, LessonState.INTRO.value}:
                feedback = (
                    f"Last time you practiced `{exercise.primary_skill}`. Start with this recall task before moving on."
                )
            return ActionResult(
                session=self._session_payload(session_id, learner_id),
                exercise=self._public_exercise(exercise, existing["hint_level"]),
                schema=schema,
                evaluation=None,
                result=None,
                feedback=feedback,
                hint=None,
                progress=self.progress(learner_id),
                onboarding=not bool(sql_level or dialect or goal or existing.get("onboarding_complete")),
            )

        session_id = self.repo.create_session(learner_id)
        learner = self.repo.get_learner(learner_id)
        assert learner is not None
        exercise = self._pick_exercise(learner_id, learner)
        self.repo.save_session_state(
            session_id,
            current_exercise_id=exercise.id if exercise else None,
            lesson_state=LessonState.TEACH if exercise else LessonState.COMPLETE,
            attempt_count=0,
            hint_level=0,
            solution_revealed=False,
            failed_attempts=0,
            onboarding_complete=bool(sql_level and dialect and goal),
            recent_summary="",
        )
        intro = self._intro_text(learner, exercise)
        return ActionResult(
            session=self._session_payload(session_id, learner_id),
            exercise=self._public_exercise(exercise, 0) if exercise else None,
            schema=self._schema_for(exercise) if exercise else None,
            evaluation=None,
            result=None,
            feedback=intro,
            hint=None,
            progress=self.progress(learner_id),
            onboarding=not bool(sql_level and dialect and goal),
        )

    def get_session(self, session_id: str) -> ActionResult:
        session = self.repo.get_session(session_id)
        if session is None:
            raise KeyError(session_id)
        exercise = get_exercise(session["current_exercise_id"]) if session.get("current_exercise_id") else None
        return ActionResult(
            session=self._session_payload(session_id, session["learner_id"]),
            exercise=self._public_exercise(exercise, session["hint_level"]) if exercise else None,
            schema=self._schema_for(exercise) if exercise else None,
            evaluation=None,
            result=None,
            feedback=session.get("recent_summary") or "",
            hint=None,
            progress=self.progress(session["learner_id"]),
        )

    def run_sql(self, session_id: str, query: str) -> ActionResult:
        session = self._require_session(session_id)
        exercise = get_exercise(session["current_exercise_id"])
        result = run_sql(query, dataset_id=exercise.dataset)
        feedback = ""
        if not result.ok:
            feedback = template_feedback(
                status="SYNTAX_ERROR" if result.error_type == "syntax" else "RUNTIME_ERROR",
                tags=[],
                comparison_notes=[],
                engine_message=result.message,
                hint_text=None,
                correct_explanation=None,
            )
        self.repo.save_session_state(
            session_id,
            current_exercise_id=exercise.id,
            lesson_state=LessonState.ATTEMPT,
            attempt_count=session["attempt_count"],
            hint_level=session["hint_level"],
            solution_revealed=bool(session["solution_revealed"]),
            failed_attempts=session["failed_attempts"],
        )
        return ActionResult(
            session=self._session_payload(session_id, session["learner_id"]),
            exercise=self._public_exercise(exercise, session["hint_level"]),
            schema=self._schema_for(exercise),
            evaluation=None,
            result=result.model_dump(),
            feedback=feedback,
            hint=None,
            progress=self.progress(session["learner_id"]),
        )

    def submit(self, session_id: str, query: str) -> ActionResult:
        session = self._require_session(session_id)
        exercise = get_exercise(session["current_exercise_id"])
        evaluation = evaluate_exercise(exercise, query)
        attempt_count = session["attempt_count"] + 1
        success = evaluation.status in SUCCESS
        failed_attempts = 0 if success else session["failed_attempts"] + 1
        hint_level = session["hint_level"]
        solution_revealed = bool(session["solution_revealed"])
        previously_completed = self.repo.completed_exercise_ids(session["learner_id"])

        self.repo.record_attempt(
            learner_id=session["learner_id"],
            session_id=session_id,
            exercise_id=exercise.id,
            query=query,
            status=evaluation.status,
            hint_level=hint_level,
            diagnostic_tags=evaluation.diagnostic_tags,
        )

        skill = self.repo.get_skill(session["learner_id"], exercise.primary_skill)
        updated = update_skill_state(
            skill,
            status=evaluation.status,
            attempt_count=attempt_count,
            hint_level=hint_level,
            solution_revealed=solution_revealed,
            exercise_id=exercise.id,
            is_review=exercise.id in previously_completed,
        )
        self.repo.save_skill(session["learner_id"], updated)

        hint_text = self._hint_text(exercise, hint_level) if not success else None
        feedback = template_feedback(
            status=evaluation.status.value,
            tags=evaluation.diagnostic_tags,
            comparison_notes=list(evaluation.comparison.notes) if evaluation.comparison else [],
            engine_message=evaluation.engine_message,
            hint_text=hint_text,
            correct_explanation=exercise.solution_notes or exercise.concept,
        )
        if settings.llm_enabled:
            feedback = self.tutor.feedback_for_evaluation(
                exercise=exercise,
                query=query,
                evaluation=evaluation,
                hint_text=hint_text,
                fallback=feedback,
            )

        state = LessonState.FEEDBACK if success else LessonState.RETRY
        self.repo.save_session_state(
            session_id,
            current_exercise_id=exercise.id,
            lesson_state=state,
            attempt_count=attempt_count,
            hint_level=hint_level,
            solution_revealed=solution_revealed,
            failed_attempts=failed_attempts,
            recent_summary=feedback[:500],
        )
        result = run_sql(query, dataset_id=exercise.dataset)
        return ActionResult(
            session=self._session_payload(session_id, session["learner_id"]),
            exercise=self._public_exercise(exercise, hint_level),
            schema=self._schema_for(exercise),
            evaluation=evaluation,
            result=result.model_dump(),
            feedback=feedback,
            hint=None,
            progress=self.progress(session["learner_id"]),
        )

    def hint(self, session_id: str, *, stronger: bool = False, want_solution: bool = False) -> ActionResult:
        session = self._require_session(session_id)
        exercise = get_exercise(session["current_exercise_id"])
        max_level = 5
        if want_solution:
            next_level = 5
        else:
            step = 2 if stronger else 1
            next_level = min(max_level, session["hint_level"] + step)
        solution_revealed = next_level >= 5 or bool(session["solution_revealed"])
        if (
            not want_solution
            and next_level >= 5
            and session["failed_attempts"] < settings.solution_after_failed_attempts
        ):
            next_level = 4
            solution_revealed = bool(session["solution_revealed"])
        text = self._hint_text(exercise, next_level, include_solution=solution_revealed)
        self.repo.save_session_state(
            session_id,
            current_exercise_id=exercise.id,
            lesson_state=LessonState.RETRY,
            attempt_count=session["attempt_count"],
            hint_level=next_level,
            solution_revealed=solution_revealed,
            failed_attempts=session["failed_attempts"],
            recent_summary=f"Hint {next_level}: {text[:240]}",
        )
        return ActionResult(
            session=self._session_payload(session_id, session["learner_id"]),
            exercise=self._public_exercise(exercise, next_level),
            schema=self._schema_for(exercise),
            evaluation=None,
            result=None,
            feedback=f"Hint {next_level}: {text}",
            hint={"level": next_level, "text": text, "solution_revealed": solution_revealed},
            progress=self.progress(session["learner_id"]),
        )

    def next_exercise(self, session_id: str) -> ActionResult:
        session = self._require_session(session_id)
        learner = self.repo.get_learner(session["learner_id"])
        assert learner is not None
        exercise = self._pick_exercise(session["learner_id"], learner)
        if exercise is None:
            summary = self._session_summary(session["learner_id"])
            self.repo.save_session_state(
                session_id,
                current_exercise_id=None,
                lesson_state=LessonState.COMPLETE,
                attempt_count=0,
                hint_level=0,
                solution_revealed=False,
                failed_attempts=0,
                summary=summary,
                ended=True,
            )
            return ActionResult(
                session=self._session_payload(session_id, session["learner_id"]),
                exercise=None,
                schema=None,
                evaluation=None,
                result=None,
                feedback=summary,
                hint=None,
                progress=self.progress(session["learner_id"]),
            )
        self.repo.save_session_state(
            session_id,
            current_exercise_id=exercise.id,
            lesson_state=LessonState.TEACH,
            attempt_count=0,
            hint_level=0,
            solution_revealed=False,
            failed_attempts=0,
        )
        teach = exercise.teach or exercise.concept
        feedback = f"{teach}\n\n{exercise.prompt}".strip()
        return ActionResult(
            session=self._session_payload(session_id, session["learner_id"]),
            exercise=self._public_exercise(exercise, 0),
            schema=self._schema_for(exercise),
            evaluation=None,
            result=None,
            feedback=feedback,
            hint=None,
            progress=self.progress(session["learner_id"]),
        )

    def schema(self, dataset_id: str, tables: list[str] | None = None) -> SchemaPayload:
        return get_schema(dataset_id, tables=tables)

    def preview(self, dataset_id: str, table: str, limit: int = 5) -> dict:
        return preview_table(dataset_id, table, limit=limit).model_dump()

    def progress(self, learner_id: str) -> dict:
        learner = self.repo.get_learner(learner_id)
        skills = self.repo.list_skills(learner_id)
        items = []
        for skill in SKILLS:
            state = skills.get(skill.id) or SkillState(skill_id=skill.id)
            items.append(
                {
                    "skill_id": skill.id,
                    "name": skill.name,
                    "mastery": state.mastery,
                    "band": mastery_band(state.mastery).value,
                    "attempts": state.attempts,
                    "successful_attempts": state.successful_attempts,
                    "last_practiced_at": state.last_practiced_at.isoformat() if state.last_practiced_at else None,
                }
            )
        weak = [item for item in items if item["attempts"] > 0 and item["mastery"] < 0.8]
        weak.sort(key=lambda item: item["mastery"])
        pattern = None
        tags = []
        for attempt in self.repo.recent_attempts(learner_id, 12):
            import json

            tags.extend(json.loads(attempt["diagnostic_tags_json"] or "[]"))
        if tags:
            top = max(set(tags), key=tags.count)
            pattern = f"Recent pattern: `{top}` has shown up often in recent attempts."
        return {
            "learner": learner,
            "skills": items,
            "suggested_next": weak[0]["name"] if weak else None,
            "pattern": pattern,
            "completed_exercises": sorted(self.repo.completed_exercise_ids(learner_id)),
        }

    def list_exercises(self) -> list[dict]:
        return [
            {
                "id": ex.id,
                "title": ex.title,
                "primary_skill": ex.primary_skill,
                "difficulty": ex.difficulty,
                "module": ex.module,
            }
            for ex in load_exercises()
        ]

    def public_exercise(self, exercise_id: str) -> dict:
        return self._public_exercise(get_exercise(exercise_id), 0)

    def _pick_exercise(self, learner_id: str, learner: dict) -> Exercise | None:
        return select_next_exercise(
            mastery=self.repo.list_skills(learner_id),
            goal=Goal(learner["goal"]),
            sql_level=SqlLevel(learner["sql_level"]),
            completed_exercise_ids=self.repo.completed_exercise_ids(learner_id),
            recent_failures=self.repo.recent_failure_count(learner_id),
        )

    def _require_session(self, session_id: str) -> dict:
        session = self.repo.get_session(session_id)
        if session is None:
            raise KeyError(session_id)
        if not session.get("current_exercise_id"):
            raise ValueError("No active exercise in this session.")
        return session

    def _schema_for(self, exercise: Exercise) -> SchemaPayload:
        return get_schema(exercise.dataset, tables=exercise.schema_tables or None)

    def _public_exercise(self, exercise: Exercise, hint_level: int) -> dict:
        return {
            "id": exercise.id,
            "title": exercise.title,
            "primary_skill": exercise.primary_skill,
            "difficulty": exercise.difficulty,
            "dataset": exercise.dataset,
            "prompt": exercise.prompt,
            "concept": exercise.concept,
            "teach": exercise.teach,
            "schema_tables": exercise.schema_tables,
            "evaluation": {
                "order_matters": exercise.evaluation.order_matters,
                "require_column_names": exercise.evaluation.require_column_names,
            },
            "hint_count": len(exercise.hints),
            "current_hint_level": hint_level,
        }

    def _hint_text(self, exercise: Exercise, level: int, include_solution: bool = False) -> str:
        if level <= 0:
            return "Try the exercise first. A hint will point at the idea, not the final query."
        if level >= 5 or include_solution:
            return f"One working solution:\n{exercise.reference_sql.strip()}"
        for hint in exercise.hints:
            if hint.level == level:
                return hint.text
        if exercise.hints:
            return exercise.hints[min(level, len(exercise.hints)) - 1].text
        return "Look at the schema and the wording of the task again."

    def _intro_text(self, learner: dict, exercise: Exercise | None) -> str:
        dialect_note = ""
        if learner["dialect"] != Dialect.SQLITE.value:
            dialect_note = (
                f" You selected {learner['dialect']}; this sandbox runs SQLite. "
                "I'll teach your dialect and call out differences when they matter."
            )
        if exercise is None:
            return "You're all caught up. Open Progress to review weak skills."
        teach = exercise.teach or exercise.concept
        return (
            f"We'll start with **{exercise.title}** ({exercise.primary_skill.replace('_', ' ')})."
            f"{dialect_note}\n\n{teach}"
        ).strip()

    def _session_summary(self, learner_id: str) -> str:
        skills = self.repo.list_skills(learner_id)
        practiced = [s for s in skills.values() if s.attempts]
        practiced.sort(key=lambda s: s.last_practiced_at or "", reverse=True)
        names = ", ".join(s.skill_id for s in practiced[:4]) or "the opening skills"
        weak = [s.skill_id for s in practiced if s.mastery < 0.6]
        watch = f"\n△ Watch {', '.join(weak)}" if weak else ""
        return f"Today:\n✓ {names}{watch}\n\nNext: keep practicing your weakest skill."

    def _session_payload(self, session_id: str, learner_id: str) -> dict:
        session = self.repo.get_session(session_id)
        learner = self.repo.get_learner(learner_id)
        return {
            "id": session_id,
            "learner_id": learner_id,
            "lesson_state": session["lesson_state"] if session else None,
            "attempt_count": session["attempt_count"] if session else 0,
            "hint_level": session["hint_level"] if session else 0,
            "failed_attempts": session["failed_attempts"] if session else 0,
            "learner": {
                "sql_level": learner["sql_level"] if learner else None,
                "dialect": learner["dialect"] if learner else None,
                "goal": learner["goal"] if learner else None,
            },
        }
