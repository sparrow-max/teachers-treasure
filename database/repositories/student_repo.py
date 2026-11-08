from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from database.models import ROLE_STUDENT, Student, utcnow

_ORDER_BY_WHITELIST = {
    "student_no": ("student_no", "id"),
    "name": ("name", "id"),
    "id": ("id",),
}


def list_students(
    db: Session,
    keyword: str | None = None,
    active: bool = True,
    include_inactive: bool = False,
    class_id: int | None = None,
) -> list[Student]:
    stmt = select(Student)
    if not include_inactive:
        stmt = stmt.where(Student.active.is_(active))
    if class_id is not None:
        stmt = stmt.where(Student.class_id == class_id)
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(Student.name.ilike(like), Student.student_no.ilike(like))
        )
    stmt = stmt.order_by(Student.student_no.asc(), Student.id.asc())
    return list(db.scalars(stmt).all())


def get_student(db: Session, student_id: int) -> Student | None:
    return db.get(Student, student_id)


def get_student_by_no(db: Session, student_no: str) -> Student | None:
    return db.scalar(select(Student).where(Student.student_no == student_no))


def create_student(
    db: Session,
    student_no: str,
    name: str,
    class_id: int,
    role: str = ROLE_STUDENT,
) -> Student:
    student = Student(
        student_no=student_no, name=name, role=role, class_id=class_id
    )
    db.add(student)
    db.flush()
    db.refresh(student)
    return student


def deactivate_student(
    db: Session, student_id: int, at: datetime | None = None
) -> bool:
    now = at or utcnow()
    result = db.execute(
        update(Student)
        .where(Student.id == student_id, Student.active.is_(True))
        .values(active=False, updated_at=now)
    )
    return result.rowcount == 1


def count_active_students(
    db: Session, class_id: int | None = None
) -> int:
    stmt = select(func.count(Student.id)).where(Student.active.is_(True))
    if class_id is not None:
        stmt = stmt.where(Student.class_id == class_id)
    return int(db.scalar(stmt) or 0)


def list_active_students_ordered(
    db: Session, order_by: str, class_id: int | None = None
) -> list[Student]:
    columns = _ORDER_BY_WHITELIST.get(order_by)
    if columns is None:
        raise ValueError(f"unsupported order_by: {order_by}")
    order = [getattr(Student, column).asc() for column in columns]
    stmt = select(Student).where(Student.active.is_(True))
    if class_id is not None:
        stmt = stmt.where(Student.class_id == class_id)
    stmt = stmt.order_by(*order)
    return list(db.scalars(stmt).all())