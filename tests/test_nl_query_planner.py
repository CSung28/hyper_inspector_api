from app.services.nl_query_planner import rule_based_plan


PROFILE = {
    "tables": [
        {
            "table": '"Extract"."Orders"',
            "row_count": 1000,
            "columns": [
                {"column_name": "Order Date", "data_type": "DATE", "min_date": "2023-01-01", "max_date": "2023-12-31", "distinct_count": 365},
                {"column_name": "Sales", "data_type": "DOUBLE", "distinct_count": 950},
                {"column_name": "Profit", "data_type": "DOUBLE", "distinct_count": 900},
                {"column_name": "Region", "data_type": "TEXT", "distinct_count": 4},
                {"column_name": "Category", "data_type": "TEXT", "distinct_count": 3},
            ],
        }
    ]
}


def test_rule_based_recent_period_sum():
    plan = rule_based_plan("최근 3개월 Sales 매출은 얼마야?", PROFILE)
    assert plan["intent"] == "recent_period_sum"
    assert plan["date_column"] == "Order Date"
    assert plan["measure_column"] == "Sales"
    assert plan["period"]["months"] == 3


def test_rule_based_monthly_trend():
    plan = rule_based_plan("월별 Sales 추이를 보여줘", PROFILE)
    assert plan["intent"] == "monthly_trend"
    assert plan["measure_column"] == "Sales"


def test_rule_based_top_n():
    plan = rule_based_plan("Region별 Sales TOP 5", PROFILE)
    assert plan["intent"] == "top_n_by_dimension"
    assert plan["dimension_column"] == "Region"
    assert plan["measure_column"] == "Sales"
    assert plan["limit"] == 5


def test_rule_based_month_over_month():
    plan = rule_based_plan("최근 월 Sales 전월 대비", PROFILE)
    assert plan["intent"] == "month_over_month"
    assert plan["date_column"] == "Order Date"
    assert plan["measure_column"] == "Sales"


def test_rule_based_min_max_date():
    plan = rule_based_plan("데이터는 언제부터 언제까지 있어?", PROFILE)
    assert plan["intent"] == "min_max_date"
    assert plan["date_column"] == "Order Date"
