from __future__ import annotations

from pathlib import Path
from typing import Any

from tableauhyperapi import Connection, CreateMode, HyperProcess, Telemetry

from app.services.hyper_reader import APP_NAME, assert_known_table, get_table_schema, list_tables, validate_hyper_path
from app.services.sql_builder import safe_column_name, safe_table_name, unquote_identifier


TEXT_TYPES = ("TEXT", "VARCHAR", "CHAR")
DATE_TYPES = ("DATE", "TIMESTAMP", "TIMESTAMP_TZ")
NUMERIC_TYPES = ("INT", "BIG_INT", "SMALL_INT", "DOUBLE", "FLOAT", "NUMERIC", "REAL")


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


def _type_name(data_type: str) -> str:
    return data_type.upper()


def is_text_type(data_type: str) -> bool:
    return any(token in _type_name(data_type) for token in TEXT_TYPES)


def is_date_type(data_type: str) -> bool:
    return any(token in _type_name(data_type) for token in DATE_TYPES)


def is_numeric_type(data_type: str) -> bool:
    type_name = _type_name(data_type)
    return any(token in type_name for token in NUMERIC_TYPES)


def _scalar(connection: Connection, sql: str):
    return _json_safe(connection.execute_scalar_query(sql))


def _query_rows(connection: Connection, sql: str) -> list[list[Any]]:
    with connection.execute_query(sql) as result:
        return [[_json_safe(value) for value in row] for row in result]


def profile_table(hyper_path: str | Path, table_name: str, top_values_limit: int = 5) -> dict[str, Any]:
    path = validate_hyper_path(hyper_path)
    table_name = assert_known_table(path, table_name)
    table_sql = safe_table_name(table_name)
    schema = get_table_schema(path, table_name)
    allowed_columns = [column["column_name"] for column in schema]

    with HyperProcess(
        telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU,
        user_agent=APP_NAME,
    ) as hyper:
        with Connection(
            endpoint=hyper.endpoint,
            database=str(path),
            create_mode=CreateMode.NONE,
        ) as connection:
            row_count = _scalar(connection, f"SELECT COUNT(*) FROM {table_sql}")
            profiled_columns = []

            for column in schema:
                safe_column = safe_column_name(column["column_name"], allowed_columns)
                column_sql = safe_column.sql
                data_type = column["data_type"]

                base = _query_rows(
                    connection,
                    (
                        f"SELECT "
                        f"COUNT(*) - COUNT({column_sql}) AS null_count, "
                        f"COUNT(DISTINCT {column_sql}) AS distinct_count "
                        f"FROM {table_sql}"
                    ),
                )[0]

                profile: dict[str, Any] = {
                    "column_name": safe_column.raw_name,
                    "source_column_name": column["column_name"],
                    "data_type": data_type,
                    "null_count": base[0],
                    "distinct_count": base[1],
                }

                if is_text_type(data_type):
                    profile["top_values"] = [
                        {"value": row[0], "count": row[1]}
                        for row in _query_rows(
                            connection,
                            (
                                f"SELECT {column_sql}, COUNT(*) AS value_count "
                                f"FROM {table_sql} "
                                f"WHERE {column_sql} IS NOT NULL "
                                f"GROUP BY {column_sql} "
                                f"ORDER BY value_count DESC "
                                f"LIMIT {int(top_values_limit)}"
                            ),
                        )
                    ]
                elif is_date_type(data_type):
                    min_max = _query_rows(
                        connection,
                        f"SELECT MIN({column_sql}), MAX({column_sql}) FROM {table_sql}",
                    )[0]
                    profile["min_date"] = min_max[0]
                    profile["max_date"] = min_max[1]
                    profile["min"] = min_max[0]
                    profile["max"] = min_max[1]
                elif is_numeric_type(data_type):
                    stats = _query_rows(
                        connection,
                        (
                            f"SELECT MIN({column_sql}), MAX({column_sql}), "
                            f"SUM({column_sql}), AVG({column_sql}) "
                            f"FROM {table_sql}"
                        ),
                    )[0]
                    profile["min"] = stats[0]
                    profile["max"] = stats[1]
                    profile["sum"] = stats[2]
                    profile["avg"] = stats[3]
                else:
                    min_max = _query_rows(
                        connection,
                        f"SELECT MIN({column_sql}), MAX({column_sql}) FROM {table_sql}",
                    )[0]
                    profile["min"] = min_max[0]
                    profile["max"] = min_max[1]

                profiled_columns.append(profile)

    return {
        "table": table_name,
        "row_count": row_count,
        "columns": profiled_columns,
    }


def profile_hyper_file(hyper_path: str | Path) -> dict[str, Any]:
    path = validate_hyper_path(hyper_path)
    tables = []
    for table in list_tables(path):
        tables.append(profile_table(path, table))
    return {
        "tables": tables,
        "table_count": len(tables),
    }


def get_profile_table(profile: dict[str, Any], table_name: str | None = None) -> dict[str, Any]:
    tables = profile.get("tables", [])
    if table_name is None:
        if not tables:
            raise ValueError("프로파일링된 테이블이 없습니다.")
        return tables[0]

    target = unquote_identifier(table_name).casefold()
    for table in tables:
        if table["table"] == table_name or unquote_identifier(table["table"]).casefold() == target:
            return table

    raise ValueError(f"프로파일에서 테이블을 찾을 수 없습니다: {table_name}")
