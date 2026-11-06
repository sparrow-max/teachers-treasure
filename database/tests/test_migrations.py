from __future__ import annotations

from sqlalchemy import inspect, text


EXPECTED_TABLES = {
    "students",
    "rollcall_sessions",
    "attendance_records",
    "users",
}


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


def test_schema_sql_matches_migrations(tmp_path) -> None:
    import sqlite3
    from pathlib import Path

    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    database = tmp_path / "schema_only.db"
    connection = sqlite3.connect(database)
    try:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        connection.close()
    assert EXPECTED_TABLES <= tables