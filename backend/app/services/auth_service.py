import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import ApiError, ErrorCode
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories import user_repo
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    UserOut,
)


def login(db: Session, payload: LoginRequest) -> LoginResponse:
    user = user_repo.get_active_user_by_username(db, payload.username)
    if user is None or not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise ApiError(ErrorCode.INVALID_CREDENTIALS)

    user_repo.set_last_login(db, user.id, datetime.now(timezone.utc))
    db.commit()
    db.refresh(user)

    access_token, expires_in = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
        student_id=user.student_id,
        token_version=user.token_version,
    )
    return LoginResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


def get_user(db: Session, user_id: int) -> User:
    user = user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise ApiError(ErrorCode.UNAUTHORIZED)
    return user


def _is_valid_new_password(password: str) -> bool:
    if not 8 <= len(password) <= 64:
        return False
    if re.search(r"[A-Za-z]", password) is None:
        return False
    if re.search(r"\d", password) is None:
        return False
    return True


def change_password(
    db: Session,
    user_id: int,
    payload: ChangePasswordRequest,
) -> None:
    user = get_user(db, user_id)

    if not verify_password(payload.old_password, user.password_hash):
        raise ApiError(ErrorCode.WRONG_OLD_PASSWORD)
    if not _is_valid_new_password(payload.new_password):
        raise ApiError(ErrorCode.INVALID_NEW_PASSWORD)
    if payload.new_password == payload.old_password:
        raise ApiError(ErrorCode.INVALID_NEW_PASSWORD)

    updated = user_repo.update_password(
        db,
        user_id,
        hash_password(payload.new_password),
        must_change_password=False,
    )
    if not updated:
        raise ApiError(ErrorCode.UNAUTHORIZED)

    db.commit()
    db.refresh(user)


def seed_teacher(
    db: Session,
    username: str,
    password: str,
    reset: bool = False,
) -> User:
    existing = user_repo.get_user_by_username(db, username)

    if existing is not None:
        if existing.role != "teacher":
            raise ApiError(ErrorCode.USERNAME_EXISTS)
        if reset:
            existing.password_hash = hash_password(password)
            existing.must_change_password = True
            existing.active = True
            db.commit()
            db.refresh(existing)
        return existing

    user = user_repo.create_user(
        db,
        username=username,
        password_hash=hash_password(password),
        role="teacher",
        display_name=username,
        student_id=None,
        must_change_password=True,
    )
    db.commit()
    db.refresh(user)
    return user