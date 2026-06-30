from app.services.query_plan_validator import validate_query_plan


PROFILE = {
    "tables": [
        {
            "table": '"Extract"."Orders"',
            "row_count": 1000,
            "columns": [
                {"column_name": "Order Date", "data_type": "DATE"},
                {"column_name": "Sales", "data_type": "DOUBLE"},
                {"column_name": "Region", "data_type": "TEXT"},
            ],
        }
    ]
}


def test_validator_accepts_real_columns():
    plan = {
        "intent": "recent_period_sum",
        "table": '"Extract"."Orders"',
        "date_column": "Order Date",
        "measure_column": "Sales",
        "aggregation": "sum",
        "period": {"type": "recent_months", "months": 3, "anchor": "max_date_in_data"},
        "group_by": [],
        "filters": [],
        "limit": None,
        "confidence": 0.9,
        "assumptions": [],
        "clarification_required": False,
        "clarification_message": None,
    }
    validated = validate_query_plan(plan, PROFILE)
    assert validated["validated"] is True
    assert validated["clarification_required"] is False


def test_validator_clarifies_missing_column():
    plan = {
        "intent": "overall_sum",
        "table": '"Extract"."Orders"',
        "measure_column": "Salez",
        "aggregation": "sum",
        "filters": [],
    }
    validated = validate_query_plan(plan, PROFILE)
    assert validated["clarification_required"] is True
    assert validated["executed_sql"] is None if "executed_sql" in validated else True
    assert "Sales" in validated["candidate_columns"]["measure_column"]


def test_validator_rejects_wrong_type():
    plan = {
        "intent": "recent_period_sum",
        "table": '"Extract"."Orders"',
        "date_column": "Region",
        "measure_column": "Sales",
        "aggregation": "sum",
        "filters": [],
    }
    validated = validate_query_plan(plan, PROFILE)
    assert validated["clarification_required"] is True
