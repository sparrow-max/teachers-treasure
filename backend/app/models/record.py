from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AttendanceRecord(TimestampMixin, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "student_id",
            name="uk_records_session_student",
        ),
        UniqueConstraint(
            "session_id",
            "order_no",
            name="uk_records_session_order",
        ),
        Index(
            "idx_records_session_status_order",
            "session_id",
            "status",
            "order_no",
        ),
        Index("idx_records_session_order", "session_id", "order_no"),
        Index("idx_records_student", "student_id"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    session_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("rollcall_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    student_no: Mapped[str] = mapped_column(String(32), nullable=False)
    student_name: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="pending",
    )
    checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )