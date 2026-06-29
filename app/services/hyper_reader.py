from pathlib import Path
from typing import Any

import pandas as pd
from tableauhyperapi import (
    Connection,
    CreateMode,
    HyperProcess,
    Telemetry,
)

APP_NAME = "hyper-inspector-api"


def validate_hyper_path(hyper_path: str | Path) -> Path:
    """
    입력받은 파일 경로가 실제 .hyper 파일인지 확인합니다.
    """
    path = Path(hyper_path)

    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

    if path.suffix.lower() != ".hyper":
        raise ValueError(".hyper 파일만 지원합니다.")

    return path


def list_tables(hyper_path: str | Path) -> list[str]:
    """
    .hyper 파일 안에 들어 있는 테이블 목록을 반환합니다.
    """
    path = validate_hyper_path(hyper_path)
    tables: list[str] = []

    with HyperProcess(
        telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU,
        user_agent=APP_NAME,
    ) as hyper:
        with Connection(
            endpoint=hyper.endpoint,
            database=str(path),
            create_mode=CreateMode.NONE,
        ) as connection:
            schemas = connection.catalog.get_schema_names()

            for schema in schemas:
                table_names = connection.catalog.get_table_names(schema)

                for table_name in table_names:
                    tables.append(str(table_name))

    return tables


def assert_known_table(hyper_path: str | Path, table_name: str) -> None:
    """
    사용자가 입력한 table_name이 실제 Hyper 파일 안에 있는 테이블인지 확인합니다.
    """
    tables = list_tables(hyper_path)

    if table_name not in tables:
        raise ValueError(f"존재하지 않는 테이블입니다: {table_name}")


def get_table_schema(hyper_path: str | Path, table_name: str) -> list[dict[str, Any]]:
    """
    특정 테이블의 컬럼명과 데이터 타입을 반환합니다.
    """
    path = validate_hyper_path(hyper_path)
    assert_known_table(path, table_name)

    query = f"SELECT * FROM {table_name} LIMIT 0"

    with HyperProcess(
        telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU,
        user_agent=APP_NAME,
    ) as hyper:
        with Connection(
            endpoint=hyper.endpoint,
            database=str(path),
            create_mode=CreateMode.NONE,
        ) as connection:
            with connection.execute_query(query) as result:
                return [
                    {
                        "column_name": str(column.name),
                        "data_type": str(column.type),
                    }
                    for column in result.schema.columns
                ]


def get_row_count(hyper_path: str | Path, table_name: str) -> int:
    """
    특정 테이블의 전체 행 수를 반환합니다.
    """
    path = validate_hyper_path(hyper_path)
    assert_known_table(path, table_name)

    query = f"SELECT COUNT(*) FROM {table_name}"

    with HyperProcess(
        telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU,
        user_agent=APP_NAME,
    ) as hyper:
        with Connection(
            endpoint=hyper.endpoint,
            database=str(path),
            create_mode=CreateMode.NONE,
        ) as connection:
            value = connection.execute_scalar_query(query)

            if value is None:
                raise ValueError("row count 결과가 비어 있습니다.")

            if not isinstance(value, int):
                raise TypeError(f"row count 결과가 int가 아닙니다: {type(value)}")

            return value


def preview_table(
    hyper_path: str | Path,
    table_name: str,
    limit: int = 100,
) -> pd.DataFrame:
    """
    특정 테이블의 상위 N행을 pandas DataFrame으로 반환합니다.
    """
    path = validate_hyper_path(hyper_path)
    assert_known_table(path, table_name)

    if limit < 1:
        raise ValueError("limit은 1 이상이어야 합니다.")

    if limit > 1000:
        raise ValueError("preview limit은 1000 이하로 제한합니다.")

    query = f"SELECT * FROM {table_name} LIMIT {limit}"

    with HyperProcess(
        telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU,
        user_agent=APP_NAME,
    ) as hyper:
        with Connection(
            endpoint=hyper.endpoint,
            database=str(path),
            create_mode=CreateMode.NONE,
        ) as connection:
            with connection.execute_query(query) as result:
                column_names = [str(column.name) for column in result.schema.columns]
                rows = [list(row) for row in result]

    return pd.DataFrame(rows, columns=column_names)
