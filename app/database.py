"""Persistence helpers for local SQLite and production PostgreSQL."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DEFAULT_DATABASE = Path(__file__).resolve().parent.parent / "data" / "calculator.db"


def database_path() -> Path:
    configured = os.getenv("CALCULATOR_DATABASE_PATH")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_DATABASE


def using_postgres() -> bool:
    return bool(os.getenv("DATABASE_URL", "").strip())


def placeholder() -> str:
    return "%s" if using_postgres() else "?"


@contextmanager
def connection() -> Iterator[Any]:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        import psycopg
        from psycopg.rows import dict_row

        database = psycopg.connect(database_url, row_factory=dict_row)
    else:
        path = database_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        database = sqlite3.connect(path, timeout=5)
        database.row_factory = sqlite3.Row
        database.execute("PRAGMA foreign_keys = ON")
        database.execute("PRAGMA journal_mode = WAL")

    try:
        yield database
        database.commit()
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


def initialize_database() -> None:
    primary_key = (
        "BIGSERIAL PRIMARY KEY"
        if using_postgres()
        else "INTEGER PRIMARY KEY AUTOINCREMENT"
    )
    with connection() as database:
        database.execute(
            f"""
            CREATE TABLE IF NOT EXISTS calculation_history (
                id {primary_key},
                expression TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        database.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_calculation_history_created_at
            ON calculation_history(created_at DESC)
            """
        )
        if not using_postgres():
            database.execute("PRAGMA optimize")


def create_history(expression: str, result: int | float) -> dict[str, object]:
    created_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    result_text = str(result)
    mark = placeholder()
    with connection() as database:
        if using_postgres():
            row = database.execute(
                f"""
                INSERT INTO calculation_history (expression, result, created_at)
                VALUES ({mark}, {mark}, {mark})
                RETURNING id
                """,
                (expression, result_text, created_at),
            ).fetchone()
            history_id = row["id"]
        else:
            cursor = database.execute(
                f"""
                INSERT INTO calculation_history (expression, result, created_at)
                VALUES ({mark}, {mark}, {mark})
                """,
                (expression, result_text, created_at),
            )
            history_id = cursor.lastrowid
    return {
        "id": history_id,
        "expression": expression,
        "result": result_text,
        "created_at": created_at,
    }


def list_history(query: str, page: int, page_size: int) -> dict[str, object]:
    mark = placeholder()
    where_clause = (
        f"WHERE expression LIKE {mark} OR result LIKE {mark}" if query else ""
    )
    parameters: list[object] = []
    if query:
        search = f"%{query}%"
        parameters.extend([search, search])

    offset = (page - 1) * page_size
    with connection() as database:
        total_row = database.execute(
            f"SELECT COUNT(*) AS total FROM calculation_history {where_clause}",
            parameters,
        ).fetchone()
        total = total_row["total"]
        rows = database.execute(
            f"""
            SELECT id, expression, result, created_at
            FROM calculation_history
            {where_clause}
            ORDER BY id DESC
            LIMIT {mark} OFFSET {mark}
            """,
            [*parameters, page_size, offset],
        ).fetchall()
    return {
        "items": [dict(row) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


def delete_history(history_id: int) -> bool:
    with connection() as database:
        cursor = database.execute(
            f"DELETE FROM calculation_history WHERE id = {placeholder()}",
            (history_id,),
        )
    return cursor.rowcount > 0


def clear_history() -> int:
    with connection() as database:
        cursor = database.execute("DELETE FROM calculation_history")
    return cursor.rowcount


def history_statistics() -> dict[str, object]:
    with connection() as database:
        row = database.execute(
            """
            SELECT COUNT(*) AS total,
                   MIN(created_at) AS first_calculation,
                   MAX(created_at) AS latest_calculation
            FROM calculation_history
            """
        ).fetchone()
    return dict(row)
