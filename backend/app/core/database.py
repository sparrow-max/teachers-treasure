from collections.abc import Generator

from sqlalchemy.orm import Session

from database.session import SessionLocal, engine
from database.session import get_db as _database_get_db


def get_db() -> Generator[Session, None, None]:
    yield from _database_get_db()


__all__ = ["engine", "SessionLocal", "get_db"]