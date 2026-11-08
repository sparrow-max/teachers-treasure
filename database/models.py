from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

ROLE_STUDENT = "学生"
ROLE_MONITOR = "班长"
ROLE_TEACHER = "教师"
STUDENT_ROLES = (ROLE_STUDENT, ROLE_MONITOR, ROLE_TEACHER)

SYSTEM_ROLE_TEACHER = "teacher"
SYSTEM_ROLE_MONITOR = "monitor"
SYSTEM_ROLE_STUDENT = "student"
SYSTEM_ROLES = (SYSTEM_ROLE_TEACHER, SYSTEM_ROLE_MONITOR, SYSTEM_ROLE_STUDENT)

SESSION_CALLING = "calling"
SESSION_ENDED = "ended"
SESSION_STATUSES = (SESSION_CALLING, SESSION_ENDED)

RECORD_PENDING = "pending"
RECORD_PRESENT = "present"
RECORD_ABSENT = "absent"
RECORD_STATUSES = (RECORD_PENDING, RECORD_PRESENT, RECORD_ABSENT)

ORDER_BY_STUDENT_NO = "student_no"
ORDER_BY_NAME = "name"
ORDER_BY_ID = "id"
ORDER_BY_CHOICES = (ORDER_BY_STUDENT_NO, ORDER_BY_NAME, ORDER_BY_ID)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Classroom(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
        server_default=func.current_timestamp(),
    )

    students: Mapped[list["Student"]] = relationship(back_populates="classroom")
    sessions: Mapped[list["RollcallSession"]] = relationship(
        back_populates="classroom"
    )

    __table_args__ = (
        UniqueConstraint("code", name="uk_classes_code"),
        CheckConstraint("length(name) BETWEEN 1 AND 32", name="ck_classes_name_len"),
        CheckConstraint("length(code) BETWEEN 1 AND 32", name="ck_classes_code_len"),
        Index("idx_classes_active_code", "active", "code"),
    )


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="RESTRICT"), nullable=False
    )
    student_no: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ROLE_STUDENT, server_default=text("'学生'")
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
        server_default=func.current_timestamp(),
    )

    records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="student")
    user: Mapped[Optional["User"]] = relationship(back_populates="student", uselist=False)
    classroom: Mapped["Classroom"] = relationship(back_populates="students")

    __table_args__ = (
        UniqueConstraint("student_no", name="uk_students_student_no"),
        CheckConstraint("role IN ('学生', '班长', '教师')", name="ck_students_role"),
        CheckConstraint("length(student_no) BETWEEN 6 AND 32", name="ck_students_no_len"),
        CheckConstraint("length(name) BETWEEN 1 AND 32", name="ck_students_name_len"),
        Index("idx_students_active_no", "active", "student_no"),
        Index(
            "idx_students_class_active_no",
            "class_id", "active", "student_no",
        ),
    )


class RollcallSession(Base):
    __tablename__ = "rollcall_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=SESSION_CALLING, server_default=text("'calling'")
    )
    order_by: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ORDER_BY_STUDENT_NO,
        server_default=text("'student_no'"),
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
        server_default=func.current_timestamp(),
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
        server_default=func.current_timestamp(),
    )

    records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )
    classroom: Mapped["Classroom"] = relationship(back_populates="sessions")

    __table_args__ = (
        CheckConstraint("status IN ('calling', 'ended')", name="ck_sessions_status"),
        CheckConstraint(
            "order_by IN ('student_no', 'name', 'id')", name="ck_sessions_order_by"
        ),
        CheckConstraint("length(title) BETWEEN 1 AND 64", name="ck_sessions_title_len"),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ck_sessions_time"),
        CheckConstraint(
            "(status = 'calling' AND ended_at IS NULL) "
            "OR (status = 'ended' AND ended_at IS NOT NULL)",
            name="ck_sessions_state",
        ),
        Index("idx_sessions_started", "started_at", "id"),
        Index("idx_sessions_status", "status"),
        Index("idx_sessions_class_started", "class_id", "started_at", "id"),
    )


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("rollcall_sessions.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )
    student_no: Mapped[str] = mapped_column(String(32), nullable=False)
    student_name: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=RECORD_PENDING, server_default=text("'pending'")
    )
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
        server_default=func.current_timestamp(),
    )

    session: Mapped["RollcallSession"] = relationship(back_populates="records")
    student: Mapped["Student"] = relationship(back_populates="records")

    __table_args__ = (
        UniqueConstraint(
            "session_id", "student_id", name="uk_records_session_student"
        ),
        UniqueConstraint("session_id", "order_no", name="uk_records_session_order"),
        CheckConstraint(
            "status IN ('pending', 'present', 'absent')", name="ck_records_status"
        ),
        CheckConstraint("order_no >= 1", name="ck_records_order"),
        CheckConstraint(
            "(status = 'pending' AND checked_at IS NULL) "
            "OR (status IN ('present', 'absent') AND checked_at IS NOT NULL)",
            name="ck_records_checked",
        ),
        CheckConstraint("length(student_no) BETWEEN 6 AND 32", name="ck_records_no_len"),
        CheckConstraint("length(student_name) BETWEEN 1 AND 32", name="ck_records_name_len"),
        CheckConstraint("role IN ('学生', '班长', '教师')", name="ck_records_role"),
        Index("idx_records_session_status_order", "session_id", "status", "order_no"),
        Index("idx_records_session_order", "session_id", "order_no"),
        Index("idx_records_student", "student_id"),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name: Mapped[str] = mapped_column(String(32), nullable=False)
    student_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=True
    )
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
        server_default=func.current_timestamp(),
    )

    student: Mapped[Optional["Student"]] = relationship(back_populates="user")

    @property
    def class_id(self) -> int | None:
        return self.student.class_id if self.student is not None else None

    __table_args__ = (
        UniqueConstraint("username", name="uk_users_username"),
        UniqueConstraint("student_id", name="uk_users_student"),
        CheckConstraint(
            "role IN ('teacher', 'monitor', 'student')", name="ck_users_role"
        ),
        CheckConstraint(
            "(role = 'teacher' AND student_id IS NULL) "
            "OR (role <> 'teacher' AND student_id IS NOT NULL)",
            name="ck_users_binding",
        ),
        CheckConstraint("length(username) BETWEEN 1 AND 32", name="ck_users_username_len"),
        CheckConstraint(
            "length(display_name) BETWEEN 1 AND 32", name="ck_users_display_len"
        ),
        CheckConstraint("length(password_hash) >= 20", name="ck_users_password"),
        CheckConstraint("token_version >= 0", name="ck_users_token_version"),
        Index("idx_users_role", "role"),
        Index("idx_users_active", "active"),
    )