from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable

from tableauhyperapi import Name, TableName, escape_string_literal


FORBIDDEN_SQL_TOKENS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "COPY",
    "ATTACH",
    "PRAGMA",
    "TRUNCATE",
    "MERGE",
)


@dataclass(frozen=True)
class SafeColumn:
    raw_name: str
    sql: str


def _split_quoted_name(value: str) -> list[str]:
    text = value.strip()
    parts: list[str] = []
    current: list[str] = []
    in_quotes = False
    i = 0

    while i < len(text):
        char = text[i]

        if char == '"':
            if in_quotes and i + 1 < len(text) and text[i + 1] == '"':
                current.append('"')
                i += 2
                continue
            in_quotes = not in_quotes
            i += 1
            continue

        if char == "." and not in_quotes:
            parts.append("".join(current).strip())
            current = []
            i += 1
            continue

        current.append(char)
        i += 1

    parts.append("".join(current).strip())
    return [part for part in parts if part]


def unquote_identifier(value: str) -> str:
    parts = _split_quoted_name(value)
    if not parts:
        return value.strip().strip('"')
    return parts[-1]


def safe_table_name(table_name: str) -> str:
    parts = _split_quoted_name(table_name)
    if not parts:
        raise ValueError("테이블명이 비어 있습니다.")
    if len(parts) > 3:
        raise ValueError(f"지원하지 않는 테이블명 형식입니다: {table_name}")
    return str(TableName(*parts))


def _column_lookup(columns: Iterable[str]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for column in columns:
        raw = unquote_identifier(column)
        lookup[raw.casefold()] = raw
        lookup[column.casefold()] = raw
    return lookup


def safe_column_name(column_name: str, allowed_columns: Iterable[str]) -> SafeColumn:
    lookup = _column_lookup(allowed_columns)
    key = column_name.casefold()
    raw = lookup.get(key) or lookup.get(unquote_identifier(column_name).casefold())

    if raw is None:
        raise ValueError(f"테이블에 없는 컬럼입니다: {column_name}")

    return SafeColumn(raw_name=raw, sql=str(Name(raw)))


def sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        return f"TIMESTAMP {escape_string_literal(value.isoformat(sep=' '))}"
    if isinstance(value, date):
        return f"DATE {escape_string_literal(value.isoformat())}"
    return escape_string_literal(str(value))


def date_literal(value: date) -> str:
    return f"DATE {escape_string_literal(value.isoformat())}"


def assert_select_only(sql: str) -> str:
    stripped = sql.strip()
    upper = stripped.upper()
    if not upper.startswith("SELECT"):
        raise ValueError("SELECT 쿼리만 실행할 수 있습니다.")
    if ";" in stripped.rstrip(";"):
        raise ValueError("하나의 SELECT 문만 실행할 수 있습니다.")
    for token in FORBIDDEN_SQL_TOKENS:
        if token in upper.split():
            raise ValueError(f"허용되지 않는 SQL 명령입니다: {token}")
    return stripped.rstrip(";")


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year = month_index // 12
    month = month_index % 12 + 1
    days = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return date(year, month, min(value.day, days[month - 1]))


def period_start_from_anchor(anchor: date, period: dict | None) -> date | None:
    if not period:
        return None
    period_type = period.get("type")
    if period_type == "recent_days":
        return anchor - timedelta(days=max(1, int(period.get("days", 1))) - 1)
    if period_type == "recent_years":
        return _add_months(anchor, -12 * max(1, int(period.get("years", 1))))
    months = max(1, int(period.get("months", 3)))
    return _add_months(_month_start(anchor), -(months - 1))


def build_plan_sql(plan: dict, allowed_columns: Iterable[str], anchor_date: date | None = None) -> tuple[str, dict]:
    intent = plan["intent"]
    table_sql = safe_table_name(plan["table"])
    meta: dict = {}

    def col(name: str):
        return safe_column_name(name, allowed_columns)

    if intent == "row_count":
        return assert_select_only(f"SELECT COUNT(*) AS value FROM {table_sql}"), meta

    if intent == "recent_period_sum":
        date_col = col(plan["date_column"])
        measure_col = col(plan["measure_column"])
        if anchor_date is None:
            raise ValueError("recent_period_sum에는 anchor_date가 필요합니다.")
        period_start = period_start_from_anchor(anchor_date, plan.get("period"))
        meta = {"period_start": period_start, "period_end": anchor_date}
        sql = (
            f"SELECT SUM({measure_col.sql}) AS value, COUNT(*) AS rows_used "
            f"FROM {table_sql} "
            f"WHERE {date_col.sql} >= {date_literal(period_start)} "
            f"AND {date_col.sql} <= {date_literal(anchor_date)}"
        )
        return assert_select_only(sql), meta

    if intent == "monthly_trend":
        date_col = col(plan["date_column"])
        measure_col = col(plan["measure_column"])
        aggregation = plan.get("aggregation") or "sum"
        limit = int(plan.get("limit") or 24)
        sql = (
            f"SELECT DATE_TRUNC('month', {date_col.sql}) AS month, "
            f"{aggregation.upper()}({measure_col.sql}) AS value, COUNT(*) AS rows_used "
            f"FROM {table_sql} "
            f"WHERE {date_col.sql} IS NOT NULL "
            f"GROUP BY DATE_TRUNC('month', {date_col.sql}) "
            f"ORDER BY month ASC "
            f"LIMIT {limit}"
        )
        return assert_select_only(sql), meta

    if intent == "top_n_by_dimension":
        dimension_col = col(plan["dimension_column"])
        measure_col = col(plan["measure_column"])
        aggregation = plan.get("aggregation") or "sum"
        limit = int(plan.get("limit") or 10)
        sql = (
            f"SELECT {dimension_col.sql} AS dimension_value, "
            f"{aggregation.upper()}({measure_col.sql}) AS value, COUNT(*) AS rows_used "
            f"FROM {table_sql} "
            f"WHERE {dimension_col.sql} IS NOT NULL "
            f"GROUP BY {dimension_col.sql} "
            f"ORDER BY value DESC "
            f"LIMIT {limit}"
        )
        return assert_select_only(sql), meta

    if intent in {"overall_sum", "overall_avg"}:
        measure_col = col(plan["measure_column"])
        aggregation = "SUM" if intent == "overall_sum" else "AVG"
        sql = f"SELECT {aggregation}({measure_col.sql}) AS value, COUNT(*) AS rows_used FROM {table_sql}"
        return assert_select_only(sql), meta

    if intent == "min_max_date":
        date_col = col(plan["date_column"])
        sql = f"SELECT MIN({date_col.sql}) AS min_date, MAX({date_col.sql}) AS max_date, COUNT(*) AS rows_used FROM {table_sql}"
        return assert_select_only(sql), meta

    if intent == "distinct_count":
        dimension_col = col(plan["dimension_column"])
        sql = f"SELECT COUNT(DISTINCT {dimension_col.sql}) AS value, COUNT(*) AS rows_used FROM {table_sql}"
        return assert_select_only(sql), meta

    if intent == "null_count":
        dimension_col = col(plan["dimension_column"])
        sql = f"SELECT COUNT(*) - COUNT({dimension_col.sql}) AS value, COUNT(*) AS rows_used FROM {table_sql}"
        return assert_select_only(sql), meta

    raise ValueError(f"지원하지 않는 intent입니다: {intent}")
