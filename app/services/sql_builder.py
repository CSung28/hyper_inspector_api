from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

from tableauhyperapi import Name, TableName, escape_string_literal


@dataclass(frozen=True)
class SafeColumn:
    raw_name: str
    sql: str


def _split_quoted_name(value: str) -> list[str]:
    text = value.strip()
    parts: list[str] = []
    current: list[str] = []
    in_quotes = False
    i = 0

    while i < len(text):
        char = text[i]

        if char == '"':
            if in_quotes and i + 1 < len(text) and text[i + 1] == '"':
                current.append('"')
                i += 2
                continue
            in_quotes = not in_quotes
            i += 1
            continue

        if char == "." and not in_quotes:
            parts.append("".join(current).strip())
            current = []
            i += 1
            continue

        current.append(char)
        i += 1

    parts.append("".join(current).strip())
    return [part for part in parts if part]


def unquote_identifier(value: str) -> str:
    parts = _split_quoted_name(value)
    if not parts:
        return value.strip().strip('"')
    return parts[-1]


def safe_table_name(table_name: str) -> str:
    parts = _split_quoted_name(table_name)
    if not parts:
        raise ValueError("테이블명이 비어 있습니다.")
    if len(parts) > 3:
        raise ValueError(f"지원하지 않는 테이블명 형식입니다: {table_name}")
    return str(TableName(*parts))


def _column_lookup(columns: Iterable[str]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for column in columns:
        raw = unquote_identifier(column)
        lookup[raw.casefold()] = raw
        lookup[column.casefold()] = raw
    return lookup


def safe_column_name(column_name: str, allowed_columns: Iterable[str]) -> SafeColumn:
    lookup = _column_lookup(allowed_columns)
    key = column_name.casefold()
    raw = lookup.get(key) or lookup.get(unquote_identifier(column_name).casefold())

    if raw is None:
        raise ValueError(f"테이블에 없는 컬럼입니다: {column_name}")

    return SafeColumn(raw_name=raw, sql=str(Name(raw)))


def sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        return f"TIMESTAMP {escape_string_literal(value.isoformat(sep=' '))}"
    if isinstance(value, date):
        return f"DATE {escape_string_literal(value.isoformat())}"
    return escape_string_literal(str(value))


def date_literal(value: date) -> str:
    return f"DATE {escape_string_literal(value.isoformat())}"
