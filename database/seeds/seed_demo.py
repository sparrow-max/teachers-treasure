from __future__ import annotations

from sqlalchemy import select

from database.models import (
    ROLE_MONITOR,
    ROLE_STUDENT,
    SYSTEM_ROLE_MONITOR,
    SYSTEM_ROLE_STUDENT,
    Student,
)
from database.repositories import class_repo, user_repo
from database.seeds._hash import hash_password
from database.session import session_scope

DEMO_CLASS_CODE = "2023-1"
DEMO_CLASS_NAME = "2023级1班"

DEMO_STUDENTS = (
    ("20230001", "张三", ROLE_STUDENT, SYSTEM_ROLE_STUDENT),
    ("20230002", "李四", ROLE_STUDENT, SYSTEM_ROLE_STUDENT),
    ("20230003", "王五", ROLE_MONITOR, SYSTEM_ROLE_MONITOR),
)


def main() -> None:
    with session_scope() as db:
        classroom = class_repo.get_class_by_code(db, DEMO_CLASS_CODE)
        if classroom is None:
            classroom = class_repo.create_class(
                db, DEMO_CLASS_NAME, DEMO_CLASS_CODE
            )
            print(
                f"created class {DEMO_CLASS_CODE} ({DEMO_CLASS_NAME})"
            )
        else:
            print(f"use existing class {DEMO_CLASS_CODE}")

        for student_no, name, roster_role, system_role in DEMO_STUDENTS:
            existing = db.scalar(
                select(Student).where(Student.student_no == student_no)
            )
            if existing is not None:
                if existing.class_id != classroom.id:
                    existing.class_id = classroom.id
                    db.flush()
                    print(
                        f"moved demo student {student_no} ({name}) "
                        f"to class {DEMO_CLASS_CODE}"
                    )
                if user_repo.username_exists(db, student_no):
                    print(f"skip existing student {student_no} ({name})")
                    continue
                user_repo.create_user(
                    db,
                    username=student_no,
                    password_hash=hash_password(student_no),
                    role=system_role,
                    display_name=name,
                    student_id=existing.id,
                    must_change_password=True,
                )
                print(
                    f"created missing account for existing student {student_no} "
                    f"({name}); login {student_no} / initial password {student_no}"
                )
                continue

            student = Student(
                student_no=student_no, name=name, role=roster_role,
                class_id=classroom.id,
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