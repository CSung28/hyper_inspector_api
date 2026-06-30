from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.hyper_routes import get_hyper_file_path
from app.services.answer_formatter import format_answer
from app.services.hyper_profiler import profile_hyper_file
from app.services.insight_engine import execute_query_plan
from app.services.nl_query_planner import create_query_plan
from app.services.query_plan_validator import validate_query_plan


router = APIRouter(prefix="/hyper", tags=["Ask"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    language: str = "ko"
    include_sql: bool = True


class ExecutePlanRequest(BaseModel):
    question: str | None = None
    query_plan: dict[str, Any]
    include_sql: bool = True


@router.post("/{file_id}/ask/plan")
async def create_ask_plan(file_id: str, request: AskRequest):
    hyper_path = get_hyper_file_path(file_id)
    try:
        profile = profile_hyper_file(hyper_path)
        plan = await create_query_plan(request.question, profile, request.language)
        validated_plan = validate_query_plan(plan, profile)
        return {
            "question": request.question,
            "query_plan": validated_plan,
            "clarification_required": validated_plan.get("clarification_required", False),
            "clarification_message": validated_plan.get("clarification_message"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="질문 분석 중 문제가 발생했습니다. 파일과 질문을 확인해주세요.") from e


@router.post("/{file_id}/ask/execute-plan")
def execute_ask_plan(file_id: str, request: ExecutePlanRequest):
    hyper_path = get_hyper_file_path(file_id)
    try:
        profile = profile_hyper_file(hyper_path)
        validated_plan = validate_query_plan(request.query_plan, profile)
        if validated_plan.get("clarification_required"):
            return {
                "question": request.question,
                "answer": validated_plan.get("clarification_message"),
                "result_type": "clarification",
                "clarification_required": True,
                "clarification_message": validated_plan.get("clarification_message"),
                "candidate_columns": validated_plan.get("candidate_columns", {}),
                "query_plan": validated_plan,
                "executed_sql": None,
            }
        result = execute_query_plan(hyper_path, validated_plan)
        return format_answer(request.question or "", validated_plan, result, request.include_sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail="분석 계획 실행 중 문제가 발생했습니다. 검증된 SELECT 분석만 실행할 수 있습니다.") from e


@router.post("/{file_id}/ask")
async def ask_hyper_file(file_id: str, request: AskRequest):
    hyper_path = get_hyper_file_path(file_id)
    try:
        profile = profile_hyper_file(hyper_path)
        plan = await create_query_plan(request.question, profile, request.language)
        validated_plan = validate_query_plan(plan, profile)
        if validated_plan.get("clarification_required"):
            return {
                "question": request.question,
                "answer": validated_plan.get("clarification_message"),
                "result_type": "clarification",
                "clarification_required": True,
                "clarification_message": validated_plan.get("clarification_message"),
                "candidate_columns": validated_plan.get("candidate_columns", {}),
                "query_plan": validated_plan,
                "executed_sql": None,
                "assumptions": validated_plan.get("assumptions", []),
                "confidence": validated_plan.get("confidence"),
            }
        result = execute_query_plan(hyper_path, validated_plan)
        return format_answer(request.question, validated_plan, result, request.include_sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail="질문을 처리하지 못했습니다. 다른 표현으로 다시 질문해주세요.") from e
