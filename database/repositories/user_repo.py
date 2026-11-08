from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from database.models import User, utcnow


def get_active_user_by_username(
    db: Session, username: str
) -> User | None:
    return db.scalar(
        select(User).where(
            User.username == username, User.active.is_(True)
        )
    )


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_user_by_id(
    db: Session, user_id: int, active_only: bool = True
) -> User | None:
    stmt = select(User).where(User.id == user_id)
    if active_only:
        stmt = stmt.where(User.active.is_(True))
    return db.scalar(stmt)


def create_user(
    db: Session,
    username: str,
    password_hash: str,
    role: str,
    display_name: str,
    student_id: int | None,
    must_change_password: bool = True,
) -> User:
    user = User(
        username=username,
        password_hash=password_hash,
        role=role,
        display_name=display_name,
        student_id=student_id,
        must_change_password=must_change_password,
        token_version=0,
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def update_password(
    db: Session,
    user_id: int,
    password_hash: str,
    must_change_password: bool = False,
    bump_token_version: bool = True,
) -> bool:
    values: dict[str, object] = {
        "password_hash": password_hash,
        "must_change_password": must_change_password,
        "updated_at": utcnow(),
    }
    if bump_token_version:
        values["token_version"] = User.token_version + 1
    result = db.execute(
        update(User)
        .where(User.id == user_id, User.active.is_(True))
        .values(**values)
    )
    return result.rowcount == 1


def set_last_login(
    db: Session, user_id: int, at: datetime | None = None
) -> None:
    db.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_login_at=at or utcnow(), updated_at=at or utcnow())
    )


def deactivate_user_by_student(
    db: Session, student_id: int
) -> int:
    result = db.execute(
        update(User)
        .where(
            User.student_id == student_id,
            User.active.is_(True),
        )
        .values(active=False, updated_at=utcnow())
    )
    return int(result.rowcount or 0)


def username_exists(db: Session, username: str) -> bool:
    return bool(db.scalar(
        select(func.count(User.id)).where(User.username == username)
    ))