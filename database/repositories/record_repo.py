from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, insert, select, update
from sqlalchemy.orm import Session

from database.models import (
    RECORD_PENDING,
    RECORD_PRESENT,
    AttendanceRecord,
    utcnow,
)


def bulk_create_records(
    db: Session, rows: list[dict[str, object]]
) -> None:
    if not rows:
        return
    db.execute(insert(AttendanceRecord), rows)


def list_records(
    db: Session,
    session_id: int,
    status: str | None = None,
    student_id: int | None = None,
) -> list[AttendanceRecord]:
    stmt = select(AttendanceRecord).where(
        AttendanceRecord.session_id == session_id
    )
    if status is not None:
        stmt = stmt.where(AttendanceRecord.status == status)
    if student_id is not None:
        stmt = stmt.where(AttendanceRecord.student_id == student_id)
    stmt = stmt.order_by(AttendanceRecord.order_no.asc())
    return list(db.scalars(stmt).all())


def get_record(
    db: Session, session_id: int, student_id: int
) -> AttendanceRecord | None:
    return db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.session_id == session_id,
            AttendanceRecord.student_id == student_id,
        )
    )


def mark_present(
    db: Session,
    session_id: int,
    student_id: int,
    checked_at: datetime | None = None,
) -> int:
    at = checked_at or utcnow()
    result = db.execute(
        update(AttendanceRecord)
        .where(
            AttendanceRecord.session_id == session_id,
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.status == RECORD_PENDING,
        )
        .values(status=RECORD_PRESENT, checked_at=at, updated_at=at)
    )
    return int(result.rowcount or 0)


def mark_pending_absent(
    db: Session, session_id: int, ended_at: datetime | None = None
) -> int:
    at = ended_at or utcnow()
    result = db.execute(
        update(AttendanceRecord)
        .where(
            AttendanceRecord.session_id == session_id,
            AttendanceRecord.status == RECORD_PENDING,
        )
        .values(status="absent", checked_at=at, updated_at=at)
    )
    return int(result.rowcount or 0)


def count_records_by_status(
    db: Session, session_id: int
) -> dict[str, int]:
    rows = db.execute(
        select(
            AttendanceRecord.status,
            func.count(AttendanceRecord.id),
        )
        .where(AttendanceRecord.session_id == session_id)
        .group_by(AttendanceRecord.status)
    )
    return {status: int(count) for status, count in rows}