from __future__ import annotations

from sqlalchemy import select

from database.models import (
    ROLE_MONITOR,
    ROLE_STUDENT,
    SYSTEM_ROLE_MONITOR,
    SYSTEM_ROLE_STUDENT,
    Student,
)
from database.repositories import user_repo
from database.seeds._hash import hash_password
from database.session import session_scope

DEMO_STUDENTS = (
    ("20230001", "张三", ROLE_STUDENT, SYSTEM_ROLE_STUDENT),
    ("20230002", "李四", ROLE_STUDENT, SYSTEM_ROLE_STUDENT),
    ("20230003", "王五", ROLE_MONITOR, SYSTEM_ROLE_MONITOR),
)


def main() -> None:
    with session_scope() as db:
        for student_no, name, roster_role, system_role in DEMO_STUDENTS:
            existing = db.scalar(
                select(Student).where(Student.student_no == student_no)
            )
            if existing is not None:
                print(f"skip existing student {student_no} ({name})")
                continue

            student = Student(
                student_no=student_no, name=name, role=roster_role
            )
            db.add(student)
            db.flush()

            if user_repo.username_exists(db, student_no):
                print(
                    f"skip account {student_no}: username already exists"
                )
                continue

            user_repo.create_user(
                db,
                username=student_no,
                password_hash=hash_password(student_no),
                role=system_role,
                display_name=name,
                student_id=student.id,
                must_change_password=True,
            )
            print(
                f"created student {student_no} ({name}, {roster_role}); "
                f"login {student_no} / initial password {student_no}"
            )

    print("demo seed finished; all student accounts must change password on first login")


if __name__ == "__main__":
    main()