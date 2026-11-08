from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApiError, ErrorCode
from app.core.security import hash_password
from app.repositories import class_repo, student_repo, user_repo
from app.schemas.student import StudentCreate
from database.models import Student, User

_ROLE_TO_SYSTEM = {
    "学生": "student",
    "班长": "monitor",
}


def _resolve_class_id(user: User, requested: int | None) -> int | None:
    if user.role == "teacher":
        return requested
    own_class_id = user.class_id
    if own_class_id is None:
        raise ApiError(ErrorCode.FORBIDDEN)
    if requested is not None and requested != own_class_id:
        raise ApiError(ErrorCode.FORBIDDEN)
    return own_class_id


def list_students(
    db: Session,
    user: User,
    keyword: str | None,
    active: bool,
    include_inactive: bool,
    class_id: int | None,
) -> list[Student]:
    scoped_class_id = _resolve_class_id(user, class_id)
    return student_repo.list_students(
        db,
        keyword=keyword,
        active=active,
        include_inactive=include_inactive,
        class_id=scoped_class_id,
    )


def _initial_password(payload: StudentCreate) -> str:
    password = (
        payload.initial_password
        if payload.initial_password is not None
        else payload.student_no
    )
    if not 6 <= len(password) <= 32:
        raise ApiError(ErrorCode.INVALID_INITIAL_PASSWORD)
    return password


def _integrity_error(exc: IntegrityError) -> ApiError:
    detail = str(getattr(exc, "orig", exc)).lower()
    if "student_no" in detail:
        return ApiError(ErrorCode.STUDENT_NO_EXISTS)
    if "username" in detail:
        return ApiError(ErrorCode.USERNAME_EXISTS)
    return ApiError(ErrorCode.STUDENT_NO_EXISTS)


def create_student(db: Session, payload: StudentCreate) -> Student:
    classroom = class_repo.get_class(db, payload.class_id)
    if classroom is None or not classroom.active:
        raise ApiError(ErrorCode.CLASS_NOT_FOUND)

    if student_repo.get_student_by_no(db, payload.student_no) is not None:
        raise ApiError(ErrorCode.STUDENT_NO_EXISTS)

    if payload.create_account and user_repo.username_exists(
        db, payload.student_no
    ):
        raise ApiError(ErrorCode.USERNAME_EXISTS)

    password = _initial_password(payload) if payload.create_account else None

    try:
        student = student_repo.create_student(
            db,
            payload.student_no,
            payload.name,
            payload.class_id,
            payload.role,
        )
        if payload.create_account and password is not None:
            user_repo.create_user(
                db,
                username=payload.student_no,
                password_hash=hash_password(password),
                role=_ROLE_TO_SYSTEM[payload.role],
                display_name=payload.name,
                student_id=student.id,
                must_change_password=True,
            )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _integrity_error(exc) from exc

    db.refresh(student)
    return student


def delete_student(db: Session, student_id: int) -> dict[str, int | bool]:
    deactivated = student_repo.deactivate_student(db, student_id)
    if not deactivated:
        db.rollback()
        raise ApiError(ErrorCode.STUDENT_NOT_FOUND)

    user_repo.deactivate_user_by_student(db, student_id)
    db.commit()
    return {"id": student_id, "deleted": True}