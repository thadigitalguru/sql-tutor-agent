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
    SkillDef("anti_join", "Anti-joins", ("left_join", "subquery")),
    SkillDef("json_semi_structured", "JSON fields", ("filter_where",)),
    SkillDef("keyset_pagination", "Keyset pagination", ("order_by", "limit")),
    SkillDef("recursive_cte", "Recursive CTEs", ("cte",)),
    SkillDef("star_schema", "Star schema", ("inner_join", "group_by")),
    SkillDef("data_grain", "Query grain", ("group_by", "inner_join")),
    SkillDef("bridge_tables", "Bridge tables", ("inner_join",)),
    SkillDef("scd_point_in_time", "SCD Type 2 / PIT", ("inner_join", "date_operations")),
    SkillDef("effective_dated", "Effective-dated joins", ("inner_join", "date_operations")),
    SkillDef("sessionization", "Sessionization", ("window_functions",)),
    SkillDef("inference_ops", "Inference logs", ("window_functions",)),
    SkillDef("feature_store", "Point-in-time features", ("window_functions", "date_operations")),
    SkillDef("train_eval_split", "Train/eval splits", ("window_functions",)),
    SkillDef("eval_metrics", "Offline eval joins", ("inference_ops",)),
    SkillDef("rag_retrieval", "RAG retrieval SQL", ("json_semi_structured", "inner_join")),
    SkillDef("cost_attribution", "Usage / cost rollups", ("group_by",)),
)

FOUNDATION_SKILL_IDS: tuple[str, ...] = (
    "select_basic",
    "select_aliases",
    "select_distinct",
    "filter_where",
    "comparison_operators",
    "boolean_logic",
    "filter_in_like",
    "order_by",
    "limit",
    "null_handling",
    "aggregate_count",
    "aggregate_sum",
)

INTERMEDIATE_SKILL_IDS: tuple[str, ...] = FOUNDATION_SKILL_IDS + (
    "group_by",
    "having",
    "inner_join",
    "table_aliases",
    "left_join",
    "case_expression",
)

ADVANCED_SKILL_IDS: tuple[str, ...] = INTERMEDIATE_SKILL_IDS + (
    "subquery",
    "cte",
    "date_operations",
    "set_operations",
    "window_functions",
    "json_semi_structured",
    "anti_join",
)


def skill_by_id(skill_id: str) -> SkillDef | None:
    return next((skill for skill in SKILLS if skill.id == skill_id), None)


def skill_prerequisites(skill_id: str) -> tuple[str, ...]:
    skill = skill_by_id(skill_id)
    return skill.prerequisites if skill else ()


def seeded_skill_ids(sql_level: str) -> tuple[str, ...]:
    if sql_level == "advanced":
        return ADVANCED_SKILL_IDS
    if sql_level == "intermediate":
        return INTERMEDIATE_SKILL_IDS
    return ()
