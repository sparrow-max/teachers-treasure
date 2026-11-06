from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import inspect, text

EXPECTED_TABLES = {
    "students",
    "rollcall_sessions",
    "attendance_records",
    "users",
}


def _snapshot(path: str | Path) -> dict[str, dict[str, object]]:
    connection = sqlite3.connect(path)
    try:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "AND name <> 'alembic_version' ORDER BY name"
            )
        ]
        result: dict[str, dict[str, object]] = {}
        for table in tables:
            columns = {
                row[1]: (row[2].upper(), bool(row[3]), bool(row[5]), row[4])
                for row in connection.execute(f"PRAGMA table_info({table})")
            }
            index_rows = list(connection.execute(f"PRAGMA index_list({table})"))
            indexes = {
                row[1]: tuple(
                    item[2]
                    for item in connection.execute(
                        f"PRAGMA index_info({row[1]})"
                    )
                )
                for row in index_rows
                if not row[1].startswith("sqlite_autoindex")
            }
            unique_sets = {
                tuple(
                    item[2]
                    for item in connection.execute(
                        f"PRAGMA index_info({row[1]})"
                    )
                )
                for row in index_rows
                if row[2]
            }
            foreign_keys = {
                (row[2], row[3], row[4], row[5], row[6])
                for row in connection.execute(f"PRAGMA foreign_key_list({table})")
            }
            result[table] = {
                "columns": columns,
                "indexes": indexes,
                "unique_sets": unique_sets,
                "foreign_keys": foreign_keys,
            }
        return result
    finally:
        connection.close()


def test_migration_head_creates_all_tables(db_engine) -> None:
    tables = set(inspect(db_engine).get_table_names())
    assert EXPECTED_TABLES <= tables
    with db_engine.connect() as connection:
        version = connection.scalar(text("SELECT version_num FROM alembic_version"))
    assert version == "0005"


def test_users_has_token_version(db_engine) -> None:
    columns = {column["name"] for column in inspect(db_engine).get_columns("users")}
    assert "token_version" in columns


def test_expected_indexes_exist(db_engine) -> None:
    expected = {
        "students": {"idx_students_active_no"},
        "rollcall_sessions": {"idx_sessions_started", "idx_sessions_status"},
        "attendance_records": {
            "idx_records_session_status_order",
            "idx_records_session_order",
            "idx_records_student",
        },
        "users": {"idx_users_role", "idx_users_active"},
    }
    inspector = inspect(db_engine)
    for table, names in expected.items():
        actual = {index["name"] for index in inspector.get_indexes(table)}
        assert names <= actual


def test_schema_sql_matches_migrations(db_engine, tmp_path: Path) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    schema_database = tmp_path / "schema_only.db"

    connection = sqlite3.connect(schema_database)
    try:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
    finally:
        connection.close()

    migration_database = db_engine.url.database
    assert migration_database is not None
    assert _snapshot(migration_database) == _snapshot(schema_database)