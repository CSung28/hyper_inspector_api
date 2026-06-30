from __future__ import annotations

from typing import Any


def _num(value: Any) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _pct(value: Any) -> str:
    if value is None:
        return "계산할 수 없습니다"
    return f"{float(value) * 100:,.2f}%"


def format_answer(question: str, plan: dict[str, Any], result: dict[str, Any], include_sql: bool = True) -> dict[str, Any]:
    intent = plan.get("intent")
    measure = plan.get("measure_column")
    date_column = plan.get("date_column")
    table = plan.get("table")
    rows = result.get("rows") or result.get("data") or []
    value = result.get("value")

    if intent == "recent_period_sum":
        answer = f"{date_column} 기준 최근 기간 {measure} 합계는 {_num(value)}입니다."
        result_type = "kpi"
        data = [{"metric": measure, "value": value}]
    elif intent == "monthly_trend":
        answer = f"{measure} 월별 추이를 계산했습니다. 총 {len(rows)}개 월이 반환되었습니다."
        result_type = "table"
        data = rows
    elif intent == "top_n_by_dimension":
        answer = f"{plan.get('dimension_column')}별 {measure} TOP {plan.get('limit') or 10}을 계산했습니다."
        result_type = "table"
        data = rows
    elif intent == "month_over_month":
        answer = (
            f"최근 월 {measure}는 전월 대비 {_num(result.get('change_amount'))} "
            f"({_pct(result.get('change_rate'))}) 변동했습니다."
        )
        result_type = "kpi"
        data = [
            {"metric": "previous_month_value", "value": result.get("previous_month_value")},
            {"metric": "latest_month_value", "value": result.get("latest_month_value")},
            {"metric": "change_amount", "value": result.get("change_amount")},
            {"metric": "change_rate", "value": result.get("change_rate")},
        ]
    elif intent == "min_max_date":
        answer = f"{date_column} 기준 데이터 기간은 {result.get('period_start')}부터 {result.get('period_end')}까지입니다."
        result_type = "kpi"
        data = [{"metric": "min_date", "value": result.get("period_start")}, {"metric": "max_date", "value": result.get("period_end")}]
    elif intent in {"overall_sum", "overall_avg", "row_count", "distinct_count", "null_count"}:
        answer = result.get("answer") or f"요청한 값을 계산했습니다: {_num(value)}"
        result_type = "kpi"
        data = [{"metric": result.get("metric") or intent, "value": value}]
    else:
        answer = result.get("answer") or "질문을 처리하지 못했습니다."
        result_type = "unsupported"
        data = []

    response = {
        "question": question,
        "answer": answer,
        "result_type": result_type,
        "value": value,
        "unit": None,
        "table": table,
        "date_column": date_column,
        "measure_column": measure,
        "dimension_column": plan.get("dimension_column"),
        "period_start": result.get("period_start"),
        "period_end": result.get("period_end"),
        "rows_used": result.get("rows_used"),
        "data": data,
        "executed_sql": result.get("executed_sql") if include_sql else None,
        "assumptions": plan.get("assumptions") or result.get("assumptions") or [],
        "confidence": plan.get("confidence"),
        "clarification_required": False,
        "clarification_message": None,
    }
    return response
