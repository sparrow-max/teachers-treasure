from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user import User


def get_active_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(
        select(User).where(
            User.username == username,
            User.active.is_(True),
        )
    )


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.scalar(
        select(User).where(
            User.id == user_id,
            User.active.is_(True),
        )
    )


def username_exists(db: Session, username: str) -> bool:
    return (
        db.scalar(
            select(User.id).where(User.username == username).limit(1)
        )
        is not None
    )


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
        active=True,
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
) -> bool:
    result = db.execute(
        update(User)
        .where(User.id == user_id, User.active.is_(True))
        .values(
            password_hash=password_hash,
            must_change_password=must_change_password,
        )
    )
    return result.rowcount == 1


def set_last_login(
    db: Session,
    user_id: int,
    logged_in_at: datetime,
) -> None:
    db.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_login_at=logged_in_at)
    )

def deactivate_user_by_student(
    db: Session,
    student_id: int,
) -> int:
    result = db.execute(
        update(User)
        .where(
            User.student_id == student_id,
            User.active.is_(True),
        )
        .values(active=False)
    )
    return result.rowcount