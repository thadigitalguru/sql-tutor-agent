"""SQLite persistence for learners, sessions, attempts, and mastery."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.domain import (
    Dialect,
    Goal,
    LessonState,
    SkillState,
    SqlLevel,
    SubmissionStatus,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS learners (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    sql_level TEXT NOT NULL,
    dialect TEXT NOT NULL,
    goal TEXT NOT NULL,
    preferences_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS learner_skills (
    learner_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    mastery REAL NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    successes INTEGER NOT NULL DEFAULT 0,
    recent_success_streak INTEGER NOT NULL DEFAULT 0,
    last_practiced_at TEXT,
    highest_hint_used_recently INTEGER NOT NULL DEFAULT 0,
    review_successes INTEGER NOT NULL DEFAULT 0,
    demonstrated_on_json TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (learner_id, skill_id),
    FOREIGN KEY (learner_id) REFERENCES learners(id)
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    summary TEXT,
    current_exercise_id TEXT,
    lesson_state TEXT NOT NULL DEFAULT 'intro',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    hint_level INTEGER NOT NULL DEFAULT 0,
    solution_revealed INTEGER NOT NULL DEFAULT 0,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    recent_summary TEXT,
    onboarding_complete INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (learner_id) REFERENCES learners(id)
);

CREATE TABLE IF NOT EXISTS attempts (
    id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    session_id TEXT,
    exercise_id TEXT NOT NULL,
    query TEXT NOT NULL,
    status TEXT NOT NULL,
    hint_level INTEGER NOT NULL DEFAULT 0,
    diagnostic_tags_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    elapsed_ms REAL,
    FOREIGN KEY (learner_id) REFERENCES learners(id)
);
"""


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


class Repository:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path or settings.tutor_db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def create_learner(
        self,
        *,
        sql_level: SqlLevel = SqlLevel.BEGINNER,
        dialect: Dialect = Dialect.POSTGRESQL,
        goal: Goal = Goal.FOUNDATIONS,
        preferences: dict | None = None,
        learner_id: str | None = None,
    ) -> str:
        learner_id = learner_id or str(uuid4())
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO learners (id, created_at, sql_level, dialect, goal, preferences_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    learner_id,
                    utcnow(),
                    sql_level.value,
                    dialect.value,
                    goal.value,
                    json.dumps(preferences or {}),
                ),
            )
        return learner_id

    def get_learner(self, learner_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM learners WHERE id = ?", (learner_id,)).fetchone()
        return dict(row) if row else None

    def update_learner(
        self,
        learner_id: str,
        *,
        sql_level: SqlLevel | None = None,
        dialect: Dialect | None = None,
        goal: Goal | None = None,
        preferences: dict | None = None,
    ) -> None:
        learner = self.get_learner(learner_id)
        if learner is None:
            raise KeyError(learner_id)
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE learners
                SET sql_level = ?, dialect = ?, goal = ?, preferences_json = ?
                WHERE id = ?
                """,
                (
                    (sql_level.value if sql_level else learner["sql_level"]),
                    (dialect.value if dialect else learner["dialect"]),
                    (goal.value if goal else learner["goal"]),
                    json.dumps(preferences) if preferences is not None else learner["preferences_json"],
                    learner_id,
                ),
            )

    def create_session(self, learner_id: str) -> str:
        session_id = str(uuid4())
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    id, learner_id, started_at, lesson_state
                ) VALUES (?, ?, ?, ?)
                """,
                (session_id, learner_id, utcnow(), LessonState.INTRO.value),
            )
        return session_id

    def get_session(self, session_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None

    def latest_session(self, learner_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM sessions
                WHERE learner_id = ?
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (learner_id,),
            ).fetchone()
        return dict(row) if row else None

    def save_session_state(
        self,
        session_id: str,
        *,
        current_exercise_id: str | None,
        lesson_state: LessonState,
        attempt_count: int,
        hint_level: int,
        solution_revealed: bool,
        failed_attempts: int,
        recent_summary: str | None = None,
        onboarding_complete: bool | None = None,
        summary: str | None = None,
        ended: bool = False,
    ) -> None:
        session = self.get_session(session_id)
        if session is None:
            raise KeyError(session_id)
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET current_exercise_id = ?,
                    lesson_state = ?,
                    attempt_count = ?,
                    hint_level = ?,
                    solution_revealed = ?,
                    failed_attempts = ?,
                    recent_summary = ?,
                    onboarding_complete = ?,
                    summary = COALESCE(?, summary),
                    ended_at = CASE WHEN ? THEN ? ELSE ended_at END
                WHERE id = ?
                """,
                (
                    current_exercise_id,
                    lesson_state.value,
                    attempt_count,
                    hint_level,
                    int(solution_revealed),
                    failed_attempts,
                    recent_summary if recent_summary is not None else session["recent_summary"],
                    int(session["onboarding_complete"] if onboarding_complete is None else onboarding_complete),
                    summary,
                    int(ended),
                    utcnow() if ended else None,
                    session_id,
                ),
            )

    def record_attempt(
        self,
        *,
        learner_id: str,
        session_id: str | None,
        exercise_id: str,
        query: str,
        status: SubmissionStatus,
        hint_level: int,
        diagnostic_tags: list[str],
        elapsed_ms: float | None = None,
    ) -> str:
        attempt_id = str(uuid4())
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO attempts (
                    id, learner_id, session_id, exercise_id, query, status,
                    hint_level, diagnostic_tags_json, created_at, elapsed_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    learner_id,
                    session_id,
                    exercise_id,
                    query,
                    status.value,
                    hint_level,
                    json.dumps(diagnostic_tags),
                    utcnow(),
                    elapsed_ms,
                ),
            )
        return attempt_id

    def completed_exercise_ids(self, learner_id: str) -> set[str]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT exercise_id
                FROM attempts
                WHERE learner_id = ? AND status IN ('CORRECT', 'CORRECT_WITH_IMPROVEMENT')
                """,
                (learner_id,),
            ).fetchall()
        return {row["exercise_id"] for row in rows}

    def recent_failure_count(self, learner_id: str, limit: int = 5) -> int:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT status FROM attempts
                WHERE learner_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (learner_id, limit),
            ).fetchall()
        return sum(1 for row in rows if row["status"] not in {"CORRECT", "CORRECT_WITH_IMPROVEMENT"})

    def get_skill(self, learner_id: str, skill_id: str) -> SkillState:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM learner_skills
                WHERE learner_id = ? AND skill_id = ?
                """,
                (learner_id, skill_id),
            ).fetchone()
        if row is None:
            return SkillState(skill_id=skill_id)
        return _row_to_skill(row)

    def list_skills(self, learner_id: str) -> dict[str, SkillState]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM learner_skills WHERE learner_id = ?",
                (learner_id,),
            ).fetchall()
        return {row["skill_id"]: _row_to_skill(row) for row in rows}

    def save_skill(self, learner_id: str, state: SkillState) -> None:
        last = state.last_practiced_at.isoformat() if state.last_practiced_at else None
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO learner_skills (
                    learner_id, skill_id, mastery, attempts, successes,
                    recent_success_streak, last_practiced_at,
                    highest_hint_used_recently, review_successes, demonstrated_on_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learner_id, skill_id) DO UPDATE SET
                    mastery = excluded.mastery,
                    attempts = excluded.attempts,
                    successes = excluded.successes,
                    recent_success_streak = excluded.recent_success_streak,
                    last_practiced_at = excluded.last_practiced_at,
                    highest_hint_used_recently = excluded.highest_hint_used_recently,
                    review_successes = excluded.review_successes,
                    demonstrated_on_json = excluded.demonstrated_on_json
                """,
                (
                    learner_id,
                    state.skill_id,
                    state.mastery,
                    state.attempts,
                    state.successful_attempts,
                    state.recent_success_streak,
                    last,
                    state.highest_hint_used_recently,
                    state.review_successes,
                    json.dumps(state.demonstrated_on),
                ),
            )

    def recent_attempts(self, learner_id: str, limit: int = 20) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM attempts
                WHERE learner_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (learner_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]


def _row_to_skill(row: sqlite3.Row) -> SkillState:
    last = row["last_practiced_at"]
    return SkillState(
        skill_id=row["skill_id"],
        mastery=row["mastery"],
        attempts=row["attempts"],
        successful_attempts=row["successes"],
        recent_success_streak=row["recent_success_streak"],
        last_practiced_at=datetime.fromisoformat(last) if last else None,
        highest_hint_used_recently=row["highest_hint_used_recently"],
        review_successes=row["review_successes"],
        demonstrated_on=json.loads(row["demonstrated_on_json"] or "[]"),
    )
