from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from database.models import Classroom, Student, utcnow


def list_classes(
    db: Session,
    active: bool = True,
    include_inactive: bool = False,
    visible_class_id: int | None = None,
) -> list[Classroom]:
    stmt = select(Classroom)
    if visible_class_id is not None:
        stmt = stmt.where(Classroom.id == visible_class_id)
    elif not include_inactive:
        stmt = stmt.where(Classroom.active.is_(active))
    stmt = stmt.order_by(Classroom.code.asc(), Classroom.id.asc())
    return list(db.scalars(stmt).all())


def get_class(db: Session, class_id: int) -> Classroom | None:
    return db.get(Classroom, class_id)


def get_class_by_code(db: Session, code: str) -> Classroom | None:
    return db.scalar(select(Classroom).where(Classroom.code == code))


def create_class(db: Session, name: str, code: str) -> Classroom:
    classroom = Classroom(name=name, code=code)
    db.add(classroom)
    db.flush()
    db.refresh(classroom)
    return classroom


def deactivate_class(
    db: Session, class_id: int, at: datetime | None = None
) -> bool:
    now = at or utcnow()
    result = db.execute(
        update(Classroom)
        .where(Classroom.id == class_id, Classroom.active.is_(True))
        .values(active=False, updated_at=now)
    )
    return result.rowcount == 1


def count_active_students(db: Session, class_id: int) -> int:
    return int(db.scalar(
        select(func.count(Student.id)).where(
            Student.class_id == class_id,
            Student.active.is_(True),
        )
    ) or 0)


def code_exists(db: Session, code: str) -> bool:
    return bool(db.scalar(
        select(func.count(Classroom.id)).where(Classroom.code == code)
    ))