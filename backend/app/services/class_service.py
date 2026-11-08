from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApiError, ErrorCode
from app.repositories import class_repo
from app.schemas.class_ import ClassCreate
from database.models import Classroom, User


def _visible_class_id(user: User) -> int | None:
    if user.role == "teacher":
        return None
    class_id = user.class_id
    if class_id is None:
        raise ApiError(ErrorCode.FORBIDDEN)
    return class_id


def list_classes(
    db: Session,
    user: User,
    active: bool,
    include_inactive: bool,
) -> list[Classroom]:
    return class_repo.list_classes(
        db,
        active=active,
        include_inactive=include_inactive,
        visible_class_id=_visible_class_id(user),
    )


def create_class(db: Session, payload: ClassCreate) -> Classroom:
    if class_repo.code_exists(db, payload.code):
        raise ApiError(ErrorCode.CLASS_CODE_EXISTS)
    try:
        classroom = class_repo.create_class(db, payload.name, payload.code)
        db.commit()
        db.refresh(classroom)
        return classroom
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(ErrorCode.CLASS_CODE_EXISTS) from exc


def delete_class(db: Session, class_id: int) -> dict[str, int | bool]:
    classroom = class_repo.get_class(db, class_id)
    if classroom is None:
        raise ApiError(ErrorCode.CLASS_NOT_FOUND)
    if class_repo.count_active_students(db, class_id) > 0:
        raise ApiError(ErrorCode.CLASS_HAS_STUDENTS)
    if not class_repo.deactivate_class(db, class_id):
        raise ApiError(ErrorCode.CLASS_NOT_FOUND)
    db.commit()
    return {"id": class_id, "deleted": True}