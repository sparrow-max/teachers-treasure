from __future__ import annotations

from datetime import timedelta

import pytest

from database.models import (
    RECORD_ABSENT,
    RECORD_PENDING,
    RECORD_PRESENT,
    ROLE_MONITOR,
    SYSTEM_ROLE_STUDENT,
    SYSTEM_ROLE_TEACHER,
    utcnow,
)
from database.repositories import (
    record_repo,
    session_repo,
    student_repo,
    user_repo,
)


def test_student_repository_list_and_include_inactive(db_session) -> None:
    student_repo.create_student(db_session, "20230001", "张三")
    student_repo.create_student(db_session, "20230002", "李四")
    student_repo.create_student(db_session, "20230003", "王五", ROLE_MONITOR)

    assert [s.student_no for s in student_repo.list_students(db_session)] == [
        "20230001", "20230002", "20230003",
    ]
    assert len(student_repo.list_students(db_session, keyword="李")) == 1
    assert student_repo.list_students(db_session, keyword="20230003")[0].name == "王五"

    assert student_repo.deactivate_student(db_session, 1) is True
    assert [s.student_no for s in student_repo.list_students(db_session)] == [
        "20230002", "20230003",
    ]
    assert len(student_repo.list_students(
        db_session, include_inactive=True
    )) == 3
    assert student_repo.count_active_students(db_session) == 2

    with pytest.raises(ValueError):
        student_repo.list_active_students_ordered(db_session, "invalid")


def test_session_and_records_flow(db_session) -> None:
    first = student_repo.create_student(db_session, "20230001", "张三")
    second = student_repo.create_student(db_session, "20230002", "李四")
    session = session_repo.create_session(db_session, "课堂点名", "student_no")

    record_repo.bulk_create_records(db_session, [
        {
            "session_id": session.id,
            "student_id": first.id,
            "student_no": first.student_no,
            "student_name": first.name,
            "role": first.role,
            "order_no": 1,
            "status": RECORD_PENDING,
        },
        {
            "session_id": session.id,
            "student_id": second.id,
            "student_no": second.student_no,
            "student_name": second.name,
            "role": second.role,
            "order_no": 2,
            "status": RECORD_PENDING,
        },
    ])

    counts = session_repo.aggregate_session_counts(db_session, [session.id])
    assert counts[session.id] == {
        "total_count": 2,
        "present_count": 0,
        "absent_count": 0,
        "pending_count": 2,
    }

    assert record_repo.mark_present(
        db_session, session.id, first.id, utcnow()
    ) == 1
    assert record_repo.mark_present(
        db_session, session.id, first.id, utcnow()
    ) == 0
    record = record_repo.get_record(db_session, session.id, first.id)
    assert record is not None and record.status == RECORD_PRESENT

    assert record_repo.mark_pending_absent(
        db_session, session.id, utcnow() + timedelta(minutes=1)
    ) == 1
    assert record_repo.list_records(
        db_session, session.id, status=RECORD_ABSENT
    )[0].student_id == second.id

    assert session_repo.finish_session(
        db_session, session.id, utcnow() + timedelta(minutes=1)
    ) is True
    assert record_repo.count_records_by_status(db_session, session.id) == {
        RECORD_PRESENT: 1,
        RECORD_ABSENT: 1,
    }

    assert session_repo.finish_session(db_session, session.id) is False


def test_session_student_visibility_filter(db_session) -> None:
    first = student_repo.create_student(db_session, "20230001", "张三")
    second = student_repo.create_student(db_session, "20230002", "李四")
    session = session_repo.create_session(db_session, "课堂点名", "student_no")
    record_repo.bulk_create_records(db_session, [
        {
            "session_id": session.id,
            "student_id": first.id,
            "student_no": first.student_no,
            "student_name": first.name,
            "role": first.role,
            "order_no": 1,
            "status": RECORD_PENDING,
        },
        {
            "session_id": session.id,
            "student_id": second.id,
            "student_no": second.student_no,
            "student_name": second.name,
            "role": second.role,
            "order_no": 2,
            "status": RECORD_PENDING,
        },
    ])
    record_repo.mark_present(db_session, session.id, first.id, utcnow())

    items, total = session_repo.list_sessions(
        db_session, 1, 20, student_id=first.id
    )
    assert total == 1 and items[0].id == session.id

    counts = session_repo.aggregate_session_counts(
        db_session, [session.id], student_id=first.id
    )
    assert counts[session.id] == {
        "total_count": 1,
        "present_count": 1,
        "absent_count": 0,
        "pending_count": 0,
    }

    items, total = session_repo.list_sessions(
        db_session, 1, 20, student_id=99999
    )
    assert total == 0 and items == []


def test_user_repository_password_and_login_fields(db_session) -> None:
    student = student_repo.create_student(db_session, "20230001", "张三")
    user = user_repo.create_user(
        db_session,
        username="20230001",
        password_hash="x" * 60,
        role=SYSTEM_ROLE_STUDENT,
        display_name="张三",
        student_id=student.id,
    )
    assert user.token_version == 0
    assert user_repo.get_active_user_by_username(
        db_session, "20230001"
    ).id == user.id
    assert user_repo.username_exists(db_session, "20230001") is True

    assert user_repo.update_password(
        db_session, user.id, "y" * 60
    ) is True
    db_session.refresh(user)
    assert user.token_version == 1
    assert user.must_change_password is False

    user_repo.set_last_login(db_session, user.id, utcnow())
    db_session.refresh(user)
    assert user.last_login_at is not None

    assert user_repo.deactivate_user_by_student(
        db_session, student.id
    ) == 1
    db_session.refresh(user)
    assert user.active is False
    assert user_repo.get_active_user_by_username(
        db_session, "20230001"
    ) is None


def test_teacher_account_can_be_created(db_session) -> None:
    teacher = user_repo.create_user(
        db_session,
        username="teacher",
        password_hash="x" * 60,
        role=SYSTEM_ROLE_TEACHER,
        display_name="教师",
        student_id=None,
    )
    assert teacher.student_id is None
    assert teacher.role == SYSTEM_ROLE_TEACHER