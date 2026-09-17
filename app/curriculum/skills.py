"""Canonical skill graph. Keep ids stable; curriculum YAML references them."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SkillDef:
    id: str
    name: str
    prerequisites: tuple[str, ...] = field(default_factory=tuple)
    goal_tags: tuple[str, ...] = ("foundations",)


SKILLS: tuple[SkillDef, ...] = (
    SkillDef("select_basic", "SELECT"),
    SkillDef("select_aliases", "Column aliases", ("select_basic",)),
    SkillDef("select_distinct", "DISTINCT", ("select_basic",)),
    SkillDef("filter_where", "WHERE", ("select_basic",)),
    SkillDef("comparison_operators", "Comparisons", ("filter_where",)),
    SkillDef("boolean_logic", "AND / OR / NOT", ("filter_where",)),
    SkillDef("filter_in_like", "IN / BETWEEN / LIKE", ("filter_where",)),
    SkillDef("order_by", "ORDER BY", ("select_basic",)),
    SkillDef("limit", "LIMIT", ("order_by",)),
    SkillDef("null_handling", "NULL", ("filter_where",)),
    SkillDef("aggregate_count", "COUNT", ("select_basic",)),
    SkillDef("aggregate_sum", "SUM / AVG / MIN / MAX", ("aggregate_count",)),
    SkillDef("group_by", "GROUP BY", ("aggregate_sum",)),
    SkillDef("having", "HAVING", ("group_by",)),
    SkillDef("inner_join", "INNER JOIN", ("select_basic", "filter_where")),
    SkillDef("table_aliases", "Table aliases", ("inner_join",)),
    SkillDef("left_join", "LEFT JOIN", ("inner_join",)),
    SkillDef("subquery", "Subqueries", ("filter_where", "aggregate_sum")),
    SkillDef("cte", "CTEs", ("subquery", "group_by")),
    SkillDef("case_expression", "CASE", ("filter_where",)),
    SkillDef("date_operations", "Dates", ("filter_where", "group_by")),
    SkillDef("set_operations", "UNION / INTERSECT / EXCEPT", ("select_basic",)),
    SkillDef("window_functions", "Window functions", ("group_by", "inner_join")),
)


def skill_by_id(skill_id: str) -> SkillDef | None:
    return next((skill for skill in SKILLS if skill.id == skill_id), None)


def skill_prerequisites(skill_id: str) -> tuple[str, ...]:
    skill = skill_by_id(skill_id)
    return skill.prerequisites if skill else ()
