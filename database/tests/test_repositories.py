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
    class_repo,
    record_repo,
    session_repo,
    student_repo,
    user_repo,
)


def make_class(db, code="C-001", name="测试班"):
    return class_repo.create_class(db, name, code)


def test_class_repository(db_session) -> None:
    first = make_class(db_session, "C-001", "一班")
    second = make_class(db_session, "C-002", "二班")
    default = class_repo.get_class_by_code(db_session, "DEFAULT")

    assert [item.code for item in class_repo.list_classes(db_session)] == [
        "C-001", "C-002", "DEFAULT",
    ]
    assert class_repo.list_classes(
        db_session, visible_class_id=first.id
    ) == [first]
    assert class_repo.get_class(db_session, first.id).name == "一班"
    assert class_repo.get_class_by_code(db_session, "C-002").id == second.id
    assert class_repo.code_exists(db_session, "C-001") is True

    student = student_repo.create_student(
        db_session, "20230001", "张三", first.id
    )
    assert class_repo.count_active_students(db_session, first.id) == 1
    assert class_repo.deactivate_class(db_session, first.id) is True
    assert class_repo.deactivate_class(db_session, first.id) is False

    active_ids = {
        item.id for item in class_repo.list_classes(db_session)
    }
    assert active_ids == {second.id, default.id}
    all_classes = class_repo.list_classes(
        db_session, include_inactive=True
    )
    assert {item.id for item in all_classes} == {
        first.id, second.id, default.id,
    }
    assert student.class_id == first.id


def test_student_repository_list_and_class_filter(db_session) -> None:
    first = make_class(db_session, "C-001", "一班")
    second = make_class(db_session, "C-002", "二班")

    one = student_repo.create_student(
        db_session, "20230001", "张三", first.id
    )
    two = student_repo.create_student(
        db_session, "20230002", "李四", first.id
    )
    three = student_repo.create_student(
        db_session, "20230003", "王五", second.id, ROLE_MONITOR
    )

    assert [
        item.student_no
        for item in student_repo.list_students(
            db_session, class_id=first.id
        )
    ] == ["20230001", "20230002"]
    assert [
        item.student_no
        for item in student_repo.list_students(
            db_session, class_id=second.id
        )
    ] == ["20230003"]
    assert len(student_repo.list_students(db_session, keyword="李")) == 1

    assert student_repo.deactivate_student(db_session, one.id) is True
    assert [
        item.student_no
        for item in student_repo.list_students(
            db_session, class_id=first.id
        )
    ] == ["20230002"]
    assert len(student_repo.list_students(
        db_session, include_inactive=True
    )) == 3
    assert student_repo.count_active_students(
        db_session, first.id
    ) == 1
    assert student_repo.count_active_students(db_session) == 2

    ordered = student_repo.list_active_students_ordered(
        db_session, "name", first.id
    )
    assert [item.name for item in ordered] == ["李四"]

    with pytest.raises(ValueError):
        student_repo.list_active_students_ordered(
            db_session, "invalid", first.id
        )


def test_session_and_records_flow(db_session) -> None:
    first_class = make_class(db_session, "C-001", "一班")
    other_class = make_class(db_session, "C-002", "二班")

    first = student_repo.create_student(
        db_session, "20230001", "张三", first_class.id
    )
    second = student_repo.create_student(
        db_session, "20230002", "李四", first_class.id
    )
    session = session_repo.create_session(
        db_session, "课堂点名", "student_no", first_class.id
    )
    other_session = session_repo.create_session(
        db_session, "二班点名", "student_no", other_class.id
    )

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

    counts = session_repo.aggregate_session_counts(
        db_session, [session.id]
    )
    assert counts[session.id] == {
        "total_count": 2,
        "present_count": 0,
        "absent_count": 0,
        "pending_count": 2,
    }

    items, total = session_repo.list_sessions(
        db_session, 1, 20, class_id=first_class.id
    )
    assert total == 1 and items[0].id == session.id
    items, total = session_repo.list_sessions(
        db_session, 1, 20, class_id=other_class.id
    )
    assert total == 1 and items[0].id == other_session.id

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
    assert record_repo.count_records_by_status(
        db_session, session.id
    ) == {
        RECORD_PRESENT: 1,
        RECORD_ABSENT: 1,
    }

    assert session_repo.finish_session(db_session, session.id) is False


def test_session_student_and_class_visibility(db_session) -> None:
    first_class = make_class(db_session, "C-001", "一班")
    other_class = make_class(db_session, "C-002", "二班")

    first = student_repo.create_student(
        db_session, "20230001", "张三", first_class.id
    )
    second = student_repo.create_student(
        db_session, "20230002", "李四", first_class.id
    )
    session = session_repo.create_session(
        db_session, "课堂点名", "student_no", first_class.id
    )
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

    items, total = session_repo.list_sessions(
        db_session, 1, 20, class_id=other_class.id
    )
    assert total == 0 and items == []


def test_user_repository_password_and_login_fields(db_session) -> None:
    classroom = make_class(db_session, "C-001", "一班")
    student = student_repo.create_student(
        db_session, "20230001", "张三", classroom.id
    )
    user = user_repo.create_user(
        db_session,
        username="20230001",
        password_hash="x" * 60,
        role=SYSTEM_ROLE_STUDENT,
        display_name="张三",
        student_id=student.id,
    )
    assert user.token_version == 0
    loaded = user_repo.get_active_user_by_username(
        db_session, "20230001"
    )
    assert loaded.id == user.id
    assert loaded.student is not None
    assert loaded.student.classroom.code == "C-001"
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