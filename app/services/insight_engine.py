from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from tableauhyperapi import Connection, CreateMode, HyperProcess, Telemetry

from app.services.hyper_reader import APP_NAME, assert_known_table, get_table_schema, validate_hyper_path
from app.services.sql_builder import assert_select_only, build_plan_sql, date_literal, safe_column_name, safe_table_name


def _json_safe(value: Any):
    if value is None:
        return None
    if hasattr(value, "item"):
        try:
            value = value.item()
        except ValueError:
            pass
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        return date(int(value.year), int(value.month), int(value.day))
    return date.fromisoformat(str(value)[:10])


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year = month_index // 12
    month = month_index % 12 + 1
    days = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return date(year, month, min(value.day, days[month - 1]))


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _connect(path: Path):
    return HyperProcess(
        telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU,
        user_agent=APP_NAME,
    )


def _prepare(hyper_path: str | Path, table_name: str, *columns: str):
    path = validate_hyper_path(hyper_path)
    table_name = assert_known_table(path, table_name)
    schema = get_table_schema(path, table_name)
    allowed_columns = [column["column_name"] for column in schema]
    safe_columns = [safe_column_name(column, allowed_columns) for column in columns]
    return path, table_name, safe_table_name(table_name), safe_columns


def recent_period_sum(
    hyper_path: str | Path,
    table_name: str,
    date_column: str,
    measure_column: str,
    months: int = 3,
) -> dict[str, Any]:
    path, table_name, table_sql, columns = _prepare(hyper_path, table_name, date_column, measure_column)
    date_col, measure_col = columns

    with _connect(path) as hyper:
        with Connection(hyper.endpoint, str(path), CreateMode.NONE) as connection:
            max_sql = f"SELECT MAX({date_col.sql}) FROM {table_sql}"
            max_value = connection.execute_scalar_query(max_sql)
            if max_value is None:
                raise ValueError("날짜 컬럼의 MAX 값을 찾을 수 없습니다.")

            period_end = _as_date(max_value)
            period_start = _add_months(period_end, -months)
            executed_sql = (
                f"SELECT SUM({measure_col.sql}) AS value, COUNT(*) AS rows_used "
                f"FROM {table_sql} "
                f"WHERE {date_col.sql} >= {date_literal(period_start)} "
                f"AND {date_col.sql} <= {date_literal(period_end)}"
            )
            with connection.execute_query(executed_sql) as result:
                row = next(iter(result))

    return {
        "insight_title": f"최근 {months}개월 {measure_col.raw_name} 합계",
        "value": _json_safe(row[0]) or 0,
        "table": table_name,
        "date_column": date_col.raw_name,
        "measure_column": measure_col.raw_name,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "rows_used": _json_safe(row[1]) or 0,
        "executed_sql": executed_sql,
        "assumptions": [
            f"{date_col.raw_name}의 MAX 값을 기준일로 사용했습니다.",
            f"최근 {months}개월 시작일은 Python에서 계산했습니다.",
        ],
        "confidence": 0.86,
    }


def monthly_trend(
    hyper_path: str | Path,
    table_name: str,
    date_column: str,
    measure_column: str,
    limit: int = 24,
) -> dict[str, Any]:
    path, table_name, table_sql, columns = _prepare(hyper_path, table_name, date_column, measure_column)
    date_col, measure_col = columns
    limit = max(1, min(int(limit), 120))

    executed_sql = (
        f"SELECT DATE_TRUNC('month', {date_col.sql}) AS month, "
        f"SUM({measure_col.sql}) AS value, COUNT(*) AS rows_used "
        f"FROM {table_sql} "
        f"WHERE {date_col.sql} IS NOT NULL "
        f"GROUP BY DATE_TRUNC('month', {date_col.sql}) "
        f"ORDER BY month DESC "
        f"LIMIT {limit}"
    )

    with _connect(path) as hyper:
        with Connection(hyper.endpoint, str(path), CreateMode.NONE) as connection:
            rows = []
            with connection.execute_query(executed_sql) as result:
                for row in result:
                    rows.append(
                        {
                            "month": _json_safe(row[0]),
                            "value": _json_safe(row[1]) or 0,
                            "rows_used": _json_safe(row[2]) or 0,
                        }
                    )

    rows.reverse()
    return {
        "insight_title": f"월별 {measure_col.raw_name} 추이",
        "value": rows[-1]["value"] if rows else 0,
        "table": table_name,
        "date_column": date_col.raw_name,
        "measure_column": measure_col.raw_name,
        "period_start": rows[0]["month"] if rows else None,
        "period_end": rows[-1]["month"] if rows else None,
        "rows_used": sum(row["rows_used"] for row in rows),
        "executed_sql": executed_sql,
        "assumptions": ["DATE_TRUNC('month', date_column) 기준으로 월을 계산했습니다."],
        "confidence": 0.84,
        "rows": rows,
    }


def top_n(
    hyper_path: str | Path,
    table_name: str,
    dimension_column: str,
    measure_column: str,
    limit: int = 10,
) -> dict[str, Any]:
    path, table_name, table_sql, columns = _prepare(hyper_path, table_name, dimension_column, measure_column)
    dimension_col, measure_col = columns
    limit = max(1, min(int(limit), 100))

    executed_sql = (
        f"SELECT {dimension_col.sql} AS dimension_value, "
        f"SUM({measure_col.sql}) AS value, COUNT(*) AS rows_used "
        f"FROM {table_sql} "
        f"WHERE {dimension_col.sql} IS NOT NULL "
        f"GROUP BY {dimension_col.sql} "
        f"ORDER BY value DESC "
        f"LIMIT {limit}"
    )

    with _connect(path) as hyper:
        with Connection(hyper.endpoint, str(path), CreateMode.NONE) as connection:
            rows = []
            with connection.execute_query(executed_sql) as result:
                for row in result:
                    rows.append(
                        {
                            "dimension_value": _json_safe(row[0]),
                            "value": _json_safe(row[1]) or 0,
                            "rows_used": _json_safe(row[2]) or 0,
                        }
                    )

    return {
        "insight_title": f"{dimension_col.raw_name}별 {measure_col.raw_name} TOP {limit}",
        "value": rows[0]["value"] if rows else 0,
        "table": table_name,
        "date_column": None,
        "measure_column": measure_col.raw_name,
        "dimension_column": dimension_col.raw_name,
        "period_start": None,
        "period_end": None,
        "rows_used": sum(row["rows_used"] for row in rows),
        "executed_sql": executed_sql,
        "assumptions": ["선택한 차원 컬럼별 측정값 합계 기준으로 정렬했습니다."],
        "confidence": 0.82,
        "rows": rows,
    }


def month_over_month(
    hyper_path: str | Path,
    table_name: str,
    date_column: str,
    measure_column: str,
) -> dict[str, Any]:
    trend = monthly_trend(hyper_path, table_name, date_column, measure_column, limit=2)
    rows = trend["rows"]
    previous = rows[-2] if len(rows) >= 2 else None
    latest = rows[-1] if rows else None

    latest_value = latest["value"] if latest else 0
    previous_value = previous["value"] if previous else 0
    change_rate = None
    if previous_value:
        change_rate = (latest_value - previous_value) / previous_value

    return {
        **trend,
        "insight_title": f"전월 대비 {trend['measure_column']} 증감률",
        "value": change_rate,
        "period_start": previous["month"] if previous else None,
        "period_end": latest["month"] if latest else None,
        "assumptions": trend["assumptions"] + ["최신 월과 직전 월만 비교했습니다."],
        "confidence": 0.8,
        "latest_month_value": latest_value,
        "previous_month_value": previous_value,
        "change_rate": change_rate,
    }


def _schema_columns(hyper_path: str | Path, table_name: str) -> list[str]:
    return [column["column_name"] for column in get_table_schema(hyper_path, table_name)]


def _fetch_rows(connection: Connection, sql: str) -> list[list[Any]]:
    sql = assert_select_only(sql)
    with connection.execute_query(sql) as result:
        return [[_json_safe(value) for value in row] for row in result]


def _as_number(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


def _anchor_date(connection: Connection, table_sql: str, date_column_sql: str) -> date:
    max_sql = assert_select_only(f"SELECT MAX({date_column_sql}) FROM {table_sql}")
    max_value = connection.execute_scalar_query(max_sql)
    if max_value is None:
        raise ValueError("날짜 컬럼의 MAX 값을 찾을 수 없습니다.")
    return _as_date(max_value)


def execute_query_plan(hyper_path: str | Path, plan: dict[str, Any]) -> dict[str, Any]:
    path = validate_hyper_path(hyper_path)
    table_name = assert_known_table(path, plan["table"])
    allowed_columns = _schema_columns(path, table_name)
    table_sql = safe_table_name(table_name)
    intent = plan["intent"]

    with _connect(path) as hyper:
        with Connection(hyper.endpoint, str(path), CreateMode.NONE) as connection:
            if intent == "month_over_month":
                date_col = safe_column_name(plan["date_column"], allowed_columns)
                measure_col = safe_column_name(plan["measure_column"], allowed_columns)
                anchor = _anchor_date(connection, table_sql, date_col.sql)
                latest_month = _month_start(anchor)
                previous_month = _add_months(latest_month, -1)
                next_month = _add_months(latest_month, 1)
                executed_sql = assert_select_only(
                    f"SELECT DATE_TRUNC('month', {date_col.sql}) AS month, "
                    f"SUM({measure_col.sql}) AS value, COUNT(*) AS rows_used "
                    f"FROM {table_sql} "
                    f"WHERE {date_col.sql} >= {date_literal(previous_month)} "
                    f"AND {date_col.sql} < {date_literal(next_month)} "
                    f"GROUP BY DATE_TRUNC('month', {date_col.sql}) "
                    f"ORDER BY month ASC"
                )
                rows = [
                    {"month": row[0], "value": row[1] or 0, "rows_used": row[2] or 0}
                    for row in _fetch_rows(connection, executed_sql)
                ]
                previous = rows[0] if rows else {"value": 0, "rows_used": 0, "month": previous_month.isoformat()}
                latest = rows[-1] if len(rows) > 1 else {"value": 0, "rows_used": 0, "month": latest_month.isoformat()}
                previous_value = _as_number(previous["value"])
                latest_value = _as_number(latest["value"])
                change_amount = latest_value - previous_value
                change_rate = (change_amount / previous_value) if previous_value else None
                return {
                    "value": change_rate,
                    "period_start": previous.get("month"),
                    "period_end": latest.get("month"),
                    "rows_used": (previous.get("rows_used") or 0) + (latest.get("rows_used") or 0),
                    "executed_sql": executed_sql,
                    "rows": rows,
                    "previous_month_value": previous_value,
                    "latest_month_value": latest_value,
                    "change_amount": change_amount,
                    "change_rate": change_rate,
                }

            anchor = None
            if intent == "recent_period_sum":
                date_col = safe_column_name(plan["date_column"], allowed_columns)
                anchor = _anchor_date(connection, table_sql, date_col.sql)

            executed_sql, meta = build_plan_sql(plan, allowed_columns, anchor)
            rows = _fetch_rows(connection, executed_sql)

    if intent == "monthly_trend":
        trend_rows = [{"month": row[0], "value": row[1] or 0, "rows_used": row[2] or 0} for row in rows]
        return {
            "value": trend_rows[-1]["value"] if trend_rows else 0,
            "period_start": trend_rows[0]["month"] if trend_rows else None,
            "period_end": trend_rows[-1]["month"] if trend_rows else None,
            "rows_used": sum(row["rows_used"] for row in trend_rows),
            "executed_sql": executed_sql,
            "rows": trend_rows,
        }

    if intent == "top_n_by_dimension":
        top_rows = [{"dimension_value": row[0], "value": row[1] or 0, "rows_used": row[2] or 0} for row in rows]
        return {
            "value": top_rows[0]["value"] if top_rows else 0,
            "period_start": None,
            "period_end": None,
            "rows_used": sum(row["rows_used"] for row in top_rows),
            "executed_sql": executed_sql,
            "rows": top_rows,
        }

    if intent == "min_max_date":
        row = rows[0] if rows else [None, None, 0]
        return {
            "value": row[1],
            "period_start": row[0],
            "period_end": row[1],
            "rows_used": row[2],
            "executed_sql": executed_sql,
        }

    row = rows[0] if rows else [0, 0]
    if intent == "row_count":
        return {
            "value": row[0] or 0,
            "rows_used": row[0] or 0,
            "period_start": None,
            "period_end": None,
            "executed_sql": executed_sql,
            "answer": f"테이블 행 수는 {row[0] or 0:,}건입니다.",
            "metric": "row_count",
        }

    return {
        "value": row[0] or 0,
        "rows_used": row[1] if len(row) > 1 else None,
        "period_start": meta.get("period_start").isoformat() if meta.get("period_start") else None,
        "period_end": meta.get("period_end").isoformat() if meta.get("period_end") else None,
        "executed_sql": executed_sql,
        "metric": plan.get("measure_column") or plan.get("dimension_column") or intent,
    }
