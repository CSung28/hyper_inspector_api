from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.hyper_routes import get_hyper_file_path
from app.services.hyper_profiler import get_profile_table, profile_hyper_file, profile_table
from app.services.insight_engine import month_over_month, monthly_trend, recent_period_sum, top_n
from app.services.semantic_detector import build_suggestions, detect_semantics


router = APIRouter(prefix="/hyper", tags=["Insights"])


class InsightQuery(BaseModel):
    kind: Literal["recent_period_sum", "monthly_trend", "top_n", "month_over_month"]
    table: str
    date_column: str | None = None
    measure_column: str
    dimension_column: str | None = None
    months: int = Field(default=3, ge=1, le=60)
    limit: int = Field(default=10, ge=1, le=100)


@router.get("/{file_id}/profile")
def get_profile(
    file_id: str,
    table: str | None = Query(default=None),
):
    hyper_path = get_hyper_file_path(file_id)

    try:
        if table:
            return profile_table(hyper_path, table)
        return profile_hyper_file(hyper_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_id}/insights/suggestions")
def get_insight_suggestions(
    file_id: str,
    table: str | None = Query(default=None),
):
    hyper_path = get_hyper_file_path(file_id)

    try:
        if table:
            table_profile = profile_table(hyper_path, table)
        else:
            profile = profile_hyper_file(hyper_path)
            table_profile = get_profile_table(profile)
        semantics = detect_semantics(table_profile)
        return {
            "table": table_profile["table"],
            "profile_summary": {
                "row_count": table_profile["row_count"],
                "column_count": len(table_profile["columns"]),
            },
            "semantics": semantics,
            "suggestions": build_suggestions(semantics),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{file_id}/insights/query")
def run_insight_query(file_id: str, query: InsightQuery):
    hyper_path = get_hyper_file_path(file_id)

    try:
        if query.kind == "recent_period_sum":
            if query.date_column is None:
                raise ValueError("recent_period_sum에는 date_column이 필요합니다.")
            return recent_period_sum(
                hyper_path,
                query.table,
                query.date_column,
                query.measure_column,
                query.months,
            )

        if query.kind == "monthly_trend":
            if query.date_column is None:
                raise ValueError("monthly_trend에는 date_column이 필요합니다.")
            return monthly_trend(
                hyper_path,
                query.table,
                query.date_column,
                query.measure_column,
                query.limit,
            )

        if query.kind == "top_n":
            if query.dimension_column is None:
                raise ValueError("top_n에는 dimension_column이 필요합니다.")
            return top_n(
                hyper_path,
                query.table,
                query.dimension_column,
                query.measure_column,
                query.limit,
            )

        if query.kind == "month_over_month":
            if query.date_column is None:
                raise ValueError("month_over_month에는 date_column이 필요합니다.")
            return month_over_month(
                hyper_path,
                query.table,
                query.date_column,
                query.measure_column,
            )

        raise ValueError(f"지원하지 않는 insight 종류입니다: {query.kind}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_id}/insights/monthly-trend")
def get_monthly_trend(
    file_id: str,
    table: str = Query(...),
    date_column: str = Query(...),
    measure_column: str = Query(...),
    limit: int = Query(default=24, ge=1, le=120),
):
    hyper_path = get_hyper_file_path(file_id)

    try:
        return monthly_trend(hyper_path, table, date_column, measure_column, limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_id}/insights/top-n")
def get_top_n(
    file_id: str,
    table: str = Query(...),
    dimension_column: str = Query(...),
    measure_column: str = Query(...),
    limit: int = Query(default=10, ge=1, le=100),
):
    hyper_path = get_hyper_file_path(file_id)

    try:
        return top_n(hyper_path, table, dimension_column, measure_column, limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
