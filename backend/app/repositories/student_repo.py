from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.models.student import Student

_ORDER_BY = {
    "student_no": (Student.student_no.asc(), Student.id.asc()),
    "name": (Student.name.asc(), Student.id.asc()),
    "id": (Student.id.asc(),),
}


def list_students(
    db: Session,
    keyword: str | None = None,
    active: bool = True,
) -> list[Student]:
    statement = select(Student).where(Student.active.is_(active))
    if keyword:
        pattern = f"%{keyword}%"
        statement = statement.where(
            or_(
                Student.name.ilike(pattern),
                Student.student_no.ilike(pattern),
            )
        )
    statement = statement.order_by(
        Student.student_no.asc(),
        Student.id.asc(),
    )
    return list(db.scalars(statement))


def get_student(db: Session, student_id: int) -> Student | None:
    return db.get(Student, student_id)


def get_student_by_no(db: Session, student_no: str) -> Student | None:
    return db.scalar(
        select(Student).where(Student.student_no == student_no)
    )


def create_student(
    db: Session,
    student_no: str,
    name: str,
    role: str,
) -> Student:
    student = Student(
        student_no=student_no,
        name=name,
        role=role,
        active=True,
    )
    db.add(student)
    db.flush()
    db.refresh(student)
    return student


def deactivate_student(db: Session, student_id: int) -> bool:
    result = db.execute(
        update(Student)
        .where(Student.id == student_id, Student.active.is_(True))
        .values(active=False)
    )
    return result.rowcount == 1


def count_active_students(db: Session) -> int:
    count = db.scalar(
        select(func.count(Student.id)).where(Student.active.is_(True))
    )
    return int(count or 0)


def list_active_students_ordered(
    db: Session,
    order_by: str,
) -> list[Student]:
    columns = _ORDER_BY.get(order_by)
    if columns is None:
        raise ValueError(f"unsupported order_by: {order_by}")
    return list(
        db.scalars(
            select(Student)
            .where(Student.active.is_(True))
            .order_by(*columns)
        )
    )