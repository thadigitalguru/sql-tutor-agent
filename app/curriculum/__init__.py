"""Load YAML exercises and the skill graph from disk."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from app.config import settings
from app.curriculum.skills import SKILLS, SkillDef, skill_by_id
from app.domain import CommonError, EvaluationSpec, Exercise, Hint


class CurriculumError(ValueError):
    pass


def load_exercises(curriculum_dir: Path | None = None) -> list[Exercise]:
    return list(_exercise_index(curriculum_dir).values())


def get_exercise(exercise_id: str, curriculum_dir: Path | None = None) -> Exercise:
    index = _exercise_index(curriculum_dir)
    if exercise_id not in index:
        raise CurriculumError(f"Unknown exercise: {exercise_id}")
    return index[exercise_id]


def exercises_for_skill(skill_id: str, curriculum_dir: Path | None = None) -> list[Exercise]:
    return [ex for ex in load_exercises(curriculum_dir) if ex.primary_skill == skill_id]


@lru_cache(maxsize=4)
def _exercise_index(curriculum_dir: Path | None) -> dict[str, Exercise]:
    root = curriculum_dir or settings.curriculum_dir
    index: dict[str, Exercise] = {}
    for path in sorted(root.rglob("*.yaml")):
        if path.name.startswith("_"):
            continue
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not payload or "id" not in payload:
            continue
        exercise = _parse_exercise(payload, module=path.parent.name)
        if exercise.id in index:
            raise CurriculumError(f"Duplicate exercise id: {exercise.id}")
        index[exercise.id] = exercise
    return index


def reload_curriculum() -> None:
    _exercise_index.cache_clear()


def _parse_exercise(payload: dict, *, module: str) -> Exercise:
    evaluation = payload.get("evaluation") or {}
    hints_raw = payload.get("hints") or []
    hints: list[Hint] = []
    for item in hints_raw:
        if isinstance(item, str):
            hints.append(Hint(level=len(hints) + 1, text=item))
        else:
            hints.append(Hint(level=int(item.get("level", len(hints) + 1)), text=item["text"]))

    schema = payload.get("schema") or payload.get("schema_visibility") or {}
    if isinstance(schema, dict):
        tables = schema.get("tables") or []
    else:
        tables = schema

    reference = payload.get("reference") or payload.get("reference_solution") or {}
    if isinstance(reference, str):
        reference_sql = reference
    else:
        reference_sql = reference.get("sql") or payload.get("reference_sql") or ""

    common = []
    for item in payload.get("common_errors") or payload.get("diagnostic_rules") or []:
        if isinstance(item, str):
            common.append(CommonError(tag=item))
        else:
            common.append(CommonError(tag=item.get("tag", ""), explanation=item.get("explanation", "")))

    if not skill_by_id(payload["primary_skill"]):
        raise CurriculumError(f"Unknown primary_skill: {payload['primary_skill']}")

    return Exercise(
        id=payload["id"],
        title=payload["title"],
        primary_skill=payload["primary_skill"],
        secondary_skills=list(payload.get("secondary_skills") or []),
        difficulty=int(payload.get("difficulty", 1)),
        dataset=payload["dataset"],
        prerequisites=list(payload.get("prerequisites") or []),
        prompt=str(payload["prompt"]).strip(),
        concept=str(payload.get("concept") or "").strip(),
        schema_tables=list(tables),
        evaluation=EvaluationSpec(
            mode=evaluation.get("mode", "result_set"),
            order_matters=bool(evaluation.get("order_matters", False)),
            duplicates_matter=bool(evaluation.get("duplicates_matter", True)),
            require_column_names=bool(evaluation.get("require_column_names", False)),
            numeric_tolerance=float(evaluation.get("numeric_tolerance", 0.005)),
        ),
        reference_sql=str(reference_sql).strip(),
        hints=hints,
        common_errors=common,
        hidden_variants=list(payload.get("hidden_variants") or []),
        module=payload.get("module") or module,
        teach=str(payload.get("teach") or "").strip(),
        solution_notes=str(payload.get("solution_notes") or "").strip(),
    )


def all_skills() -> list[SkillDef]:
    return list(SKILLS)
