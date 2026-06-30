from __future__ import annotations

from difflib import get_close_matches
from typing import Any

from app.services.hyper_profiler import is_date_type, is_numeric_type, is_text_type
from app.services.nl_query_planner import SUPPORTED_INTENTS
from app.services.sql_builder import unquote_identifier


ALLOWED_AGGREGATIONS = {"sum", "avg", "count", "min", "max"}
REQUIRED_COLUMNS = {
    "recent_period_sum": ("date_column", "measure_column"),
    "monthly_trend": ("date_column", "measure_column"),
    "top_n_by_dimension": ("dimension_column", "measure_column"),
    "month_over_month": ("date_column", "measure_column"),
    "overall_sum": ("measure_column",),
    "overall_avg": ("measure_column",),
    "min_max_date": ("date_column",),
    "row_count": (),
    "distinct_count": ("dimension_column",),
    "null_count": ("dimension_column",),
}


def _tables(profile: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(profile.get("tables"), list):
        return profile["tables"]
    if profile.get("table"):
        return [profile]
    return []


def _find_table(profile: dict[str, Any], table_name: str | None) -> dict[str, Any] | None:
    tables = _tables(profile)
    if not tables:
        return None
    if not table_name:
        return tables[0]
    target = unquote_identifier(table_name).casefold()
    for table in tables:
        if table.get("table") == table_name or unquote_identifier(table.get("table", "")).casefold() == target:
            return table
    return None


def _column_map(table_profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    columns = {}
    for column in table_profile.get("columns", []):
        columns[column["column_name"].casefold()] = column
        columns[unquote_identifier(column["column_name"]).casefold()] = column
    return columns


def _closest_columns(table_profile: dict[str, Any], name: str | None) -> list[str]:
    if not name:
        return []
    names = [column["column_name"] for column in table_profile.get("columns", [])]
    return get_close_matches(name, names, n=5, cutoff=0.35)


def _clarify(plan: dict[str, Any], message: str, suggestions: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        **plan,
        "clarification_required": True,
        "clarification_message": message,
        "candidate_columns": suggestions or {},
        "validated": False,
    }


def validate_query_plan(plan: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    intent = plan.get("intent") or "unsupported"
    if intent not in SUPPORTED_INTENTS:
        return _clarify(plan, f"지원하지 않는 intent입니다: {intent}")
    if intent == "unsupported":
        return _clarify(plan, plan.get("clarification_message") or "지원하기 어려운 질문입니다.")

    table_profile = _find_table(profile, plan.get("table"))
    if not table_profile:
        return _clarify(
            plan,
            "질문에서 사용할 테이블을 실제 Hyper profile에서 찾지 못했습니다.",
            {"tables": [table.get("table") for table in _tables(profile)]},
        )

    normalized = {**plan, "table": table_profile["table"]}
    columns = _column_map(table_profile)

    for field in REQUIRED_COLUMNS.get(intent, ()):
        name = normalized.get(field)
        if not name:
            return _clarify(normalized, f"{intent}에는 {field}이 필요합니다.")
        column = columns.get(str(name).casefold()) or columns.get(unquote_identifier(str(name)).casefold())
        if not column:
            return _clarify(
                normalized,
                f"'{name}' 컬럼을 실제 테이블에서 찾지 못했습니다. 후보 컬럼을 선택해주세요.",
                {field: _closest_columns(table_profile, str(name))},
            )
        normalized[field] = column["column_name"]

    aggregation = normalized.get("aggregation")
    if aggregation is not None:
        aggregation = str(aggregation).lower()
        if aggregation not in ALLOWED_AGGREGATIONS:
            return _clarify(normalized, f"지원하지 않는 aggregation입니다: {aggregation}")
        normalized["aggregation"] = aggregation

    limit = normalized.get("limit")
    if limit is not None:
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            return _clarify(normalized, "limit은 숫자여야 합니다.")
        if limit < 1 or limit > 100:
            return _clarify(normalized, "limit은 1~100 사이여야 합니다.")
        normalized["limit"] = limit

    date_column = normalized.get("date_column")
    if date_column:
        column = columns[date_column.casefold()]
        if not is_date_type(column["data_type"]):
            return _clarify(normalized, f"{date_column} 컬럼은 날짜 타입이 아닙니다.")

    measure_column = normalized.get("measure_column")
    if measure_column:
        column = columns[measure_column.casefold()]
        if not is_numeric_type(column["data_type"]):
            return _clarify(normalized, f"{measure_column} 컬럼은 숫자 측정값 타입이 아닙니다.")

    dimension_column = normalized.get("dimension_column")
    if dimension_column:
        column = columns[dimension_column.casefold()]
        if intent == "top_n_by_dimension" and is_numeric_type(column["data_type"]) and not is_text_type(column["data_type"]):
            return _clarify(normalized, f"{dimension_column} 컬럼은 차원 컬럼으로 보기 어렵습니다.")

    filters = normalized.get("filters") or []
    for item in filters:
        if item.get("operator") not in {"=", "between", ">=", "<=", ">", "<"}:
            return _clarify(normalized, "초기 버전에서는 equality와 date range 필터만 지원합니다.")
        if item.get("column") not in [column["column_name"] for column in table_profile.get("columns", [])]:
            return _clarify(normalized, f"필터 컬럼을 찾지 못했습니다: {item.get('column')}")

    normalized["filters"] = filters
    normalized["clarification_required"] = False
    normalized["clarification_message"] = None
    normalized["validated"] = True
    return normalized
