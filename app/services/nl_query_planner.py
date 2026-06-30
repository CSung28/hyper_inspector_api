from __future__ import annotations

import json
import os
import re
from difflib import SequenceMatcher
from typing import Any

import httpx
from dotenv import load_dotenv

from app.services.hyper_profiler import is_date_type, is_numeric_type, is_text_type
from app.services.semantic_detector import detect_semantics


load_dotenv()

SUPPORTED_INTENTS = {
    "recent_period_sum",
    "monthly_trend",
    "top_n_by_dimension",
    "month_over_month",
    "overall_sum",
    "overall_avg",
    "min_max_date",
    "row_count",
    "distinct_count",
    "null_count",
    "unsupported",
}


def _base_plan(question: str) -> dict[str, Any]:
    return {
        "intent": "unsupported",
        "table": None,
        "date_column": None,
        "measure_column": None,
        "dimension_column": None,
        "aggregation": None,
        "period": None,
        "group_by": [],
        "filters": [],
        "sort": None,
        "limit": None,
        "confidence": 0.0,
        "assumptions": [],
        "clarification_required": True,
        "clarification_message": f"지원할 수 있는 분석 질문인지 확인이 필요합니다: {question}",
    }


def _first_table(profile: dict[str, Any]) -> dict[str, Any] | None:
    tables = profile.get("tables")
    if isinstance(tables, list) and tables:
        return tables[0]
    if profile.get("table") and profile.get("columns"):
        return profile
    return None


def _column_names(table_profile: dict[str, Any]) -> list[str]:
    return [column["column_name"] for column in table_profile.get("columns", [])]


def _normalize(text: str) -> str:
    return re.sub(r"[\s_\-]+", "", text.casefold())


def _find_column(text: str, columns: list[str], aliases: dict[str, tuple[str, ...]] | None = None) -> str | None:
    folded = _normalize(text)
    aliases = aliases or {}

    for column in columns:
        if _normalize(column) in folded:
            return column

    for role, names in aliases.items():
        for name in names:
            if _normalize(name) in folded:
                for column in columns:
                    if _normalize(column) == _normalize(role):
                        return column

    best_column = None
    best_score = 0.0
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9 _-]*|[가-힣]+", text)
    for token in tokens:
        for column in columns:
            score = SequenceMatcher(None, _normalize(token), _normalize(column)).ratio()
            if score > best_score:
                best_score = score
                best_column = column
    return best_column if best_score >= 0.82 else None


def _best_date(table_profile: dict[str, Any], semantics: dict[str, Any]) -> str | None:
    candidates = semantics.get("date_candidates") or []
    if candidates:
        return candidates[0]["column_name"]
    for column in table_profile.get("columns", []):
        if is_date_type(column.get("data_type", "")):
            return column["column_name"]
    return None


def _best_measure(question: str, table_profile: dict[str, Any], semantics: dict[str, Any]) -> str | None:
    columns = _column_names(table_profile)
    numeric_columns = {
        column["column_name"]
        for column in table_profile.get("columns", [])
        if is_numeric_type(column.get("data_type", ""))
    }
    explicit = _find_column(
        question,
        columns,
        {
            "Sales": ("매출", "판매액", "금액", "revenue", "amount"),
            "Profit": ("이익", "손익"),
            "Quantity": ("수량", "qty"),
        },
    )
    if explicit and explicit in numeric_columns:
        return explicit

    lowered = question.casefold()
    if any(word in lowered for word in ("profit", "이익", "손익")):
        candidates = semantics.get("profit_candidates") or []
        if candidates:
            return candidates[0]["column_name"]
    if any(word in lowered for word in ("quantity", "qty", "수량")):
        candidates = semantics.get("quantity_candidates") or []
        if candidates:
            return candidates[0]["column_name"]
    candidates = semantics.get("sales_candidates") or semantics.get("measure_candidates") or []
    return candidates[0]["column_name"] if candidates else None


def _best_dimension(question: str, table_profile: dict[str, Any], semantics: dict[str, Any]) -> str | None:
    columns = _column_names(table_profile)
    by_match = re.search(r"([A-Za-z][A-Za-z0-9 _-]*|[가-힣]+)\s*별", question)
    if by_match:
        explicit_by = _find_column(by_match.group(1), columns)
        if explicit_by:
            return explicit_by
    explicit = _find_column(question, columns)
    if explicit:
        column_profile = next((col for col in table_profile.get("columns", []) if col["column_name"] == explicit), None)
        if column_profile and (is_text_type(column_profile["data_type"]) or not is_numeric_type(column_profile["data_type"])):
            return explicit
    candidates = semantics.get("dimension_candidates") or []
    return candidates[0]["column_name"] if candidates else None


def _extract_limit(question: str, default: int | None = None) -> int | None:
    match = re.search(r"(?:top|TOP)\s*(\d+)|(\d+)\s*(?:개|위)", question)
    if not match:
        return default
    return int(next(value for value in match.groups() if value))


def _recent_period(question: str) -> dict[str, Any]:
    match = re.search(r"최근\s*(\d+)\s*(개월|월|일|년)", question)
    if not match:
        return {"type": "recent_months", "months": 3, "anchor": "max_date_in_data"}
    amount = int(match.group(1))
    unit = match.group(2)
    if unit == "일":
        return {"type": "recent_days", "days": amount, "anchor": "max_date_in_data"}
    if unit == "년":
        return {"type": "recent_years", "years": amount, "anchor": "max_date_in_data"}
    return {"type": "recent_months", "months": amount, "anchor": "max_date_in_data"}


def rule_based_plan(question: str, profile: dict[str, Any], language: str = "ko") -> dict[str, Any]:
    table_profile = _first_table(profile)
    plan = _base_plan(question)
    if not table_profile:
        return plan

    semantics = detect_semantics(table_profile)
    table = table_profile["table"]
    date_column = _best_date(table_profile, semantics)
    measure_column = _best_measure(question, table_profile, semantics)
    dimension_column = _best_dimension(question, table_profile, semantics)
    text = question.casefold()

    plan.update(
        {
            "table": table,
            "date_column": date_column,
            "measure_column": measure_column,
            "dimension_column": None,
            "aggregation": "sum",
            "clarification_required": False,
            "clarification_message": None,
            "confidence": 0.72,
        }
    )

    if "언제부터" in question or "언제까지" in question or "가장 최근" in question:
        plan.update(
            {
                "intent": "min_max_date",
                "measure_column": None,
                "aggregation": None,
                "assumptions": ["날짜 범위는 선택된 날짜 컬럼의 MIN/MAX로 계산합니다."],
                "confidence": 0.82,
            }
        )
        return plan

    if "전월" in question or "mom" in text or "month over month" in text:
        plan.update(
            {
                "intent": "month_over_month",
                "period": {"type": "latest_complete_month_pair", "anchor": "max_date_in_data"},
                "assumptions": ["최신 월과 직전 월은 날짜 컬럼의 최대 날짜를 기준으로 찾습니다."],
                "confidence": 0.81,
            }
        )
        return plan

    if "월별" in question or "추이" in question or "trend" in text:
        plan.update(
            {
                "intent": "monthly_trend",
                "group_by": [date_column] if date_column else [],
                "sort": {"column": "month", "direction": "asc"},
                "limit": _extract_limit(question, 24),
                "assumptions": ["월별 집계는 DATE_TRUNC('month', 날짜 컬럼)을 기준으로 계산합니다."],
                "confidence": 0.8,
            }
        )
        return plan

    if "top" in text or "TOP" in question or "상위" in question:
        plan.update(
            {
                "intent": "top_n_by_dimension",
                "dimension_column": dimension_column,
                "group_by": [dimension_column] if dimension_column else [],
                "sort": {"column": "value", "direction": "desc"},
                "limit": _extract_limit(question, 10),
                "assumptions": ["차원 컬럼별 측정값 합계를 내림차순으로 정렬합니다."],
                "confidence": 0.78,
            }
        )
        return plan

    if "row" in text or "행" in question or "건수" in question:
        plan.update(
            {
                "intent": "row_count",
                "date_column": None,
                "measure_column": None,
                "aggregation": "count",
                "confidence": 0.78,
            }
        )
        return plan

    if "평균" in question or "avg" in text or "average" in text:
        plan.update({"intent": "overall_avg", "aggregation": "avg", "confidence": 0.76})
        return plan

    if "distinct" in text or "고유" in question:
        plan.update({"intent": "distinct_count", "aggregation": "count", "confidence": 0.68})
        return plan

    if "null" in text or "결측" in question or "비어" in question:
        plan.update({"intent": "null_count", "aggregation": "count", "confidence": 0.68})
        return plan

    if "최근" in question:
        plan.update(
            {
                "intent": "recent_period_sum",
                "period": _recent_period(question),
                "assumptions": ["최근 기간은 오늘이 아니라 날짜 컬럼의 최대 날짜를 기준으로 계산합니다."],
                "confidence": 0.83,
            }
        )
        return plan

    if "합계" in question or "매출" in question or "sales" in text or "sum" in text:
        plan.update(
            {
                "intent": "overall_sum",
                "period": None,
                "assumptions": ["기간 조건이 없어 전체 기간 합계로 계산합니다."],
                "confidence": 0.73,
            }
        )
        return plan

    return plan


def _profile_for_prompt(profile: dict[str, Any]) -> dict[str, Any]:
    tables = profile.get("tables") or [profile]
    compact_tables = []
    for table in tables:
        semantics = detect_semantics(table)
        compact_tables.append(
            {
                "table": table.get("table"),
                "row_count": table.get("row_count"),
                "columns": [
                    {
                        "name": column.get("column_name"),
                        "type": column.get("data_type"),
                        "min_date": column.get("min_date"),
                        "max_date": column.get("max_date"),
                        "min": column.get("min"),
                        "max": column.get("max"),
                    }
                    for column in table.get("columns", [])
                ],
                "roles": {
                    "date": semantics.get("date_candidates", []),
                    "measure": semantics.get("measure_candidates", []),
                    "dimension": semantics.get("dimension_candidates", []),
                    "sales": semantics.get("sales_candidates", []),
                    "profit": semantics.get("profit_candidates", []),
                },
            }
        )
    return {"tables": compact_tables}


def _system_prompt() -> str:
    return (
        "너는 Tableau Hyper 파일의 데이터 분석 계획을 만드는 엔진이다. "
        "SQL을 직접 작성하지 말고 반드시 순수 JSON만 반환한다. markdown을 쓰지 마라. "
        "profile에 없는 테이블/컬럼은 절대 선택하지 마라. 애매하면 clarification_required=true로 반환한다. "
        "지원 intent는 recent_period_sum, monthly_trend, top_n_by_dimension, month_over_month, "
        "overall_sum, overall_avg, min_max_date, row_count, distinct_count, null_count, unsupported 뿐이다. "
        "JSON schema: {intent, table, date_column, measure_column, dimension_column, aggregation, period, "
        "group_by, filters, sort, limit, confidence, assumptions, clarification_required, clarification_message}. "
        "aggregation은 sum, avg, count, min, max 중 하나 또는 null이다. "
        "최근 N개월/일/년은 period.anchor=max_date_in_data로 계획한다."
    )


async def openai_plan(question: str, profile: dict[str, Any], language: str = "ko") -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    payload = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "language": language,
                        "question": question,
                        "profile": _profile_for_prompt(profile),
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    plan = json.loads(content)
    if plan.get("intent") not in SUPPORTED_INTENTS:
        plan["intent"] = "unsupported"
    return plan


async def create_query_plan(question: str, profile: dict[str, Any], language: str = "ko") -> dict[str, Any]:
    try:
        plan = await openai_plan(question, profile, language)
        if plan is not None:
            return plan
    except Exception:
        pass
    return rule_based_plan(question, profile, language)
