from __future__ import annotations

from typing import Any

from app.services.hyper_profiler import is_date_type, is_numeric_type, is_text_type


DATE_KEYWORDS = ("date", "일자", "날짜", "order date")
SALES_KEYWORDS = ("sales", "revenue", "amount", "매출", "판매액", "금액")
PROFIT_KEYWORDS = ("profit", "이익", "손익")
QUANTITY_KEYWORDS = ("quantity", "qty", "수량")


def _contains_any(name: str, keywords: tuple[str, ...]) -> bool:
    lowered = name.casefold()
    return any(keyword.casefold() in lowered for keyword in keywords)


def _candidate(column: dict[str, Any], role: str, confidence: float, reasons: list[str]) -> dict[str, Any]:
    return {
        "column_name": column["column_name"],
        "data_type": column["data_type"],
        "role": role,
        "confidence": round(min(confidence, 0.99), 2),
        "reasons": reasons,
    }


def detect_semantics(table_profile: dict[str, Any]) -> dict[str, Any]:
    date_candidates = []
    measure_candidates = []
    sales_candidates = []
    profit_candidates = []
    quantity_candidates = []
    dimension_candidates = []

    row_count = table_profile.get("row_count") or 0

    for column in table_profile.get("columns", []):
        name = column["column_name"]
        data_type = column["data_type"]
        distinct_count = column.get("distinct_count") or 0

        if is_date_type(data_type) or _contains_any(name, DATE_KEYWORDS):
            confidence = 0.55
            reasons = []
            if is_date_type(data_type):
                confidence += 0.3
                reasons.append("date/time type")
            if _contains_any(name, DATE_KEYWORDS):
                confidence += 0.2
                reasons.append("date-like column name")
            date_candidates.append(_candidate(column, "date", confidence, reasons))

        if is_numeric_type(data_type):
            confidence = 0.65
            reasons = ["numeric type"]
            measure_candidates.append(_candidate(column, "measure", confidence, reasons))

            if _contains_any(name, SALES_KEYWORDS):
                sales_candidates.append(_candidate(column, "sales", 0.95, reasons + ["sales-like name"]))
            if _contains_any(name, PROFIT_KEYWORDS):
                profit_candidates.append(_candidate(column, "profit", 0.93, reasons + ["profit-like name"]))
            if _contains_any(name, QUANTITY_KEYWORDS):
                quantity_candidates.append(_candidate(column, "quantity", 0.9, reasons + ["quantity-like name"]))

        low_cardinality = row_count and distinct_count <= max(30, row_count * 0.2)
        if is_text_type(data_type) or "BOOL" in data_type.upper() or low_cardinality:
            confidence = 0.55
            reasons = []
            if is_text_type(data_type) or "BOOL" in data_type.upper():
                confidence += 0.2
                reasons.append("categorical type")
            if low_cardinality:
                confidence += 0.15
                reasons.append("low distinct count")
            dimension_candidates.append(_candidate(column, "dimension", confidence, reasons))

    def sorted_candidates(items):
        return sorted(items, key=lambda item: item["confidence"], reverse=True)

    return {
        "table": table_profile["table"],
        "date_candidates": sorted_candidates(date_candidates),
        "measure_candidates": sorted_candidates(measure_candidates),
        "sales_candidates": sorted_candidates(sales_candidates),
        "profit_candidates": sorted_candidates(profit_candidates),
        "quantity_candidates": sorted_candidates(quantity_candidates),
        "dimension_candidates": sorted_candidates(dimension_candidates),
    }


def build_suggestions(semantics: dict[str, Any]) -> list[dict[str, Any]]:
    table = semantics["table"]
    date = (semantics["date_candidates"] or [{}])[0].get("column_name")
    sales = (semantics["sales_candidates"] or semantics["measure_candidates"] or [{}])[0].get("column_name")
    dimension = (semantics["dimension_candidates"] or [{}])[0].get("column_name")

    suggestions = []
    if date and sales:
        suggestions.append(
            {
                "title": "최근 3개월 매출 합계",
                "kind": "recent_period_sum",
                "table": table,
                "date_column": date,
                "measure_column": sales,
                "months": 3,
                "confidence": 0.9,
                "assumptions": ["가장 가능성이 높은 날짜 컬럼과 매출 컬럼을 사용했습니다."],
            }
        )
        suggestions.append(
            {
                "title": "월별 매출 추이",
                "kind": "monthly_trend",
                "table": table,
                "date_column": date,
                "measure_column": sales,
                "confidence": 0.86,
                "assumptions": ["월 단위로 날짜 컬럼을 묶어 측정값 합계를 계산합니다."],
            }
        )
    if dimension and sales:
        suggestions.append(
            {
                "title": f"{dimension}별 TOP 10",
                "kind": "top_n",
                "table": table,
                "dimension_column": dimension,
                "measure_column": sales,
                "limit": 10,
                "confidence": 0.82,
                "assumptions": ["범주형 후보 컬럼을 차원으로 사용했습니다."],
            }
        )
    return suggestions
