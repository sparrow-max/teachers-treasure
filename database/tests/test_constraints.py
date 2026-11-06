from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database.models import (
    AttendanceRecord,
    RollcallSession,
    Student,
    User,
    utcnow,
)


def add_student(db, student_no="20230001", name="张三", role="学生"):
    student = Student(student_no=student_no, name=name, role=role)
    db.add(student)
    db.flush()
    return student


def add_session(db, title="课堂点名"):
    session = RollcallSession(title=title)
    db.add(session)
    db.flush()
    return session


def add_record(
    db,
    session,
    student,
    order_no=1,
    status="pending",
    checked_at=None,
):
    record = AttendanceRecord(
        session_id=session.id,
        student_id=student.id,
        student_no=student.student_no,
        student_name=student.name,
        role=student.role,
        order_no=order_no,
        status=status,
        checked_at=checked_at,
    )
    db.add(record)
    db.flush()
    return record


def test_student_no_length_and_role_constraints(db_session) -> None:
    with pytest.raises(IntegrityError):
        add_student(db_session, student_no="12345")
    db_session.rollback()

    with pytest.raises(IntegrityError):
        add_student(db_session, student_no="20230001", role="未知角色")
    db_session.rollback()

    student = add_student(db_session, student_no="123456")
    assert student.student_no == "123456"


def test_student_no_is_unique(db_session) -> None:
    add_student(db_session, student_no="20230001")
    with pytest.raises(IntegrityError):
        add_student(db_session, student_no="20230001", name="李四")
    db_session.rollback()


def test_session_state_constraints(db_session) -> None:
    with pytest.raises(IntegrityError):
        db_session.add(RollcallSession(title="非法结束", status="ended"))
        db_session.flush()
    db_session.rollback()

    with pytest.raises(IntegrityError):
        db_session.add(
            RollcallSession(
                title="非法进行中",
                status="calling",
                ended_at=utcnow(),
            )
        )
        db_session.flush()
    db_session.rollback()

    session = add_session(db_session)
    assert session.status == "calling"


def test_record_checked_at_three_states(db_session) -> None:
    student = add_student(db_session)
    session = add_session(db_session)

    with pytest.raises(IntegrityError):
        add_record(
            db_session, session, student, order_no=1,
            status="pending", checked_at=utcnow(),
        )
    db_session.rollback()

    student = add_student(db_session)
    session = add_session(db_session)
    with pytest.raises(IntegrityError):
        add_record(db_session, session, student, order_no=1, status="present")
    db_session.rollback()

    student = add_student(db_session)
    session = add_session(db_session)
    with pytest.raises(IntegrityError):
        add_record(db_session, session, student, order_no=1, status="absent")
    db_session.rollback()

    student = add_student(db_session, "20230001", "张三")
    session = add_session(db_session, "待签到场次")
    pending = add_record(
        db_session, session, student, order_no=1, status="pending"
    )
    assert pending.checked_at is None

    present_student = add_student(db_session, "20230002", "李四")
    present_session = add_session(db_session, "已签到场次")
    present = add_record(
        db_session, present_session, present_student, order_no=1,
        status="present", checked_at=utcnow(),
    )
    assert present.checked_at is not None

    absent_student = add_student(db_session, "20230003", "王五")
    absent_session = add_session(db_session, "缺勤场次")
    absent = add_record(
        db_session, absent_session, absent_student, order_no=1,
        status="absent", checked_at=utcnow() + timedelta(seconds=1),
    )
    assert absent.checked_at is not None


def test_record_unique_session_student_and_order(db_session) -> None:
    student = add_student(db_session)
    other = add_student(db_session, student_no="20230002", name="李四")
    session = add_session(db_session)
    add_record(db_session, session, student, order_no=1)

    with pytest.raises(IntegrityError):
        add_record(db_session, session, student, order_no=2)
    db_session.rollback()

    student = add_student(db_session)
    other = add_student(db_session, student_no="20230002", name="李四")
    session = add_session(db_session)
    add_record(db_session, session, student, order_no=1)
    with pytest.raises(IntegrityError):
        add_record(db_session, session, other, order_no=1)
    db_session.rollback()


def test_user_binding_and_token_version(db_session) -> None:
    student = add_student(db_session)

    with pytest.raises(IntegrityError):
        db_session.add(
            User(
                username="teacher1",
                password_hash="x" * 60,
                role="teacher",
                display_name="教师",
                student_id=student.id,
            )
        )
        db_session.flush()
    db_session.rollback()

    student = add_student(db_session)
    with pytest.raises(IntegrityError):
        db_session.add(
            User(
                username="student1",
                password_hash="x" * 60,
                role="student",
                display_name="张三",
                student_id=None,
            )
        )
        db_session.flush()
    db_session.rollback()

    student = add_student(db_session)
    user = User(
        username="student1",
        password_hash="x" * 60,
        role="student",
        display_name="张三",
        student_id=student.id,
    )
    db_session.add(user)
    db_session.flush()
    assert user.token_version == 0

    with pytest.raises(IntegrityError):
        db_session.add(
            User(
                username="teacher1",
                password_hash="x" * 60,
                role="teacher",
                display_name="教师",
                student_id=None,
                token_version=-1,
            )
        )
        db_session.flush()
    db_session.rollback()


def test_foreign_key_cascade_and_restrict(db_session) -> None:
    student = add_student(db_session)
    session = add_session(db_session)
    add_record(db_session, session, student)
    db_session.commit()

    db_session.execute(
        text("DELETE FROM rollcall_sessions WHERE id = :id"),
        {"id": session.id},
    )
    db_session.commit()
    db_session.expunge_all()
    remaining = db_session.scalar(
        text("SELECT COUNT(*) FROM attendance_records WHERE session_id = :id"),
        {"id": session.id},
    )
    assert remaining == 0

    student = add_student(db_session, student_no="20230002", name="李四")
    session = add_session(db_session, title="第二场")
    add_record(db_session, session, student)
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.execute(
            text("DELETE FROM students WHERE id = :id"), {"id": student.id}
        )
        db_session.commit()
    db_session.rollback()