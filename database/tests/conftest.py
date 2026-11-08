from __future__ import annotations

import sys
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
DB_DIR = ROOT / "database"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture()
def db_engine(database_path: Path, monkeypatch: pytest.MonkeyPatch):
    url = f"sqlite:///{database_path}"
    monkeypatch.setenv("DATABASE_URL", url)

    config = Config(str(DB_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(DB_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")

    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    factory = sessionmaker(
        bind=db_engine, class_=Session, autoflush=False,
        expire_on_commit=False,
    )
    session = factory()
    try:
        yield session
    finally:
        session.close()