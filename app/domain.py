"""Shared domain types used by sandbox, curriculum, storage, and API."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class LessonState(StrEnum):
    INTRO = "intro"
    TEACH = "teach"
    EXERCISE = "exercise"
    ATTEMPT = "attempt"
    FEEDBACK = "feedback"
    RETRY = "retry"
    REVIEW = "review"
    COMPLETE = "complete"


class SubmissionStatus(StrEnum):
    CORRECT = "CORRECT"
    CORRECT_WITH_IMPROVEMENT = "CORRECT_WITH_IMPROVEMENT"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"
    INCORRECT = "INCORRECT"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    UNSAFE = "UNSAFE"


class SqlLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Dialect(StrEnum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"


class Goal(StrEnum):
    FOUNDATIONS = "foundations"
    ANALYTICS = "analytics"
    INTERVIEWS = "interviews"
    DATABASE_WORK = "database_work"
    AI_ENGINEERING = "ai_engineering"
    DATA_ARCHITECTURE = "data_architecture"
    REFRESH = "refresh"


class MasteryBand(StrEnum):
    NEW = "New"
    LEARNING = "Learning"
    PRACTICING = "Practicing"
    STRONG = "Strong"
    MASTERED = "Mastered"


class ColumnDef(BaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False


class SchemaTable(BaseModel):
    name: str
    columns: list[ColumnDef]


class SchemaPayload(BaseModel):
    dataset_id: str
    tables: dict[str, list[ColumnDef]]


class QueryResult(BaseModel):
    ok: bool
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    row_count: int = 0
    elapsed_ms: float = 0
    truncated: bool = False
    error_type: str | None = None
    message: str | None = None


class Comparison(BaseModel):
    row_count_expected: int
    row_count_actual: int
    columns_match: bool
    values_match: bool
    order_match: bool
    duplicate_match: bool = True
    notes: list[str] = Field(default_factory=list)


class QualityKind(StrEnum):
    READABILITY = "readability"
    PERFORMANCE = "performance"
    COMPLEXITY = "complexity"
    DIALECT = "dialect"


class QualityNote(BaseModel):
    kind: QualityKind
    tag: str
    message: str


class Evaluation(BaseModel):
    status: SubmissionStatus
    execution_ok: bool
    comparison: Comparison | None = None
    diagnostic_tags: list[str] = Field(default_factory=list)
    engine_message: str | None = None
    hidden_variants_passed: int = 0
    hidden_variants_total: int = 0
    quality_notes: list[QualityNote] = Field(default_factory=list)


class Hint(BaseModel):
    level: int
    text: str


class EvaluationSpec(BaseModel):
    mode: str = "result_set"
    order_matters: bool = False
    duplicates_matter: bool = True
    require_column_names: bool = False
    numeric_tolerance: float = 0.005


class CommonError(BaseModel):
    tag: str
    explanation: str = ""


class Exercise(BaseModel):
    id: str
    title: str
    primary_skill: str
    secondary_skills: list[str] = Field(default_factory=list)
    difficulty: int = 1
    dataset: str
    prerequisites: list[str] = Field(default_factory=list)
    prompt: str
    concept: str = ""
    schema_tables: list[str] = Field(default_factory=list)
    evaluation: EvaluationSpec = Field(default_factory=EvaluationSpec)
    reference_sql: str
    hints: list[Hint] = Field(default_factory=list)
    common_errors: list[CommonError] = Field(default_factory=list)
    hidden_variants: list[str] = Field(default_factory=list)
    module: str = "foundations"
    teach: str = ""
    solution_notes: str = ""


class SkillState(BaseModel):
    skill_id: str
    mastery: float = 0.0
    attempts: int = 0
    successful_attempts: int = 0
    recent_success_streak: int = 0
    last_practiced_at: datetime | None = None
    highest_hint_used_recently: int = 0
    review_successes: int = 0
    demonstrated_on: list[str] = Field(default_factory=list)


def mastery_band(mastery: float) -> MasteryBand:
    if mastery >= 0.95:
        return MasteryBand.MASTERED
    if mastery >= 0.80:
        return MasteryBand.STRONG
    if mastery >= 0.60:
        return MasteryBand.PRACTICING
    if mastery >= 0.30:
        return MasteryBand.LEARNING
    return MasteryBand.NEW
