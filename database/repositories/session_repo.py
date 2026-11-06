from __future__ import annotations

from datetime import datetime

from sqlalchemy import case, func, select, update
from sqlalchemy.orm import Session

from database.models import (
    RECORD_ABSENT,
    RECORD_PENDING,
    RECORD_PRESENT,
    SESSION_CALLING,
    AttendanceRecord,
    RollcallSession,
    utcnow,
)


def create_session(
    db: Session,
    title: str,
    order_by: str,
    class_id: int,
    started_at: datetime | None = None,
) -> RollcallSession:
    session = RollcallSession(
        title=title,
        order_by=order_by,
        class_id=class_id,
        status=SESSION_CALLING,
        started_at=started_at or utcnow(),
    )
    db.add(session)
    db.flush()
    db.refresh(session)
    return session


def get_session(
    db: Session, session_id: int, for_update: bool = False
) -> RollcallSession | None:
    stmt = select(RollcallSession).where(RollcallSession.id == session_id)
    if for_update:
        stmt = stmt.with_for_update()
    return db.scalar(stmt)


def finish_session(
    db: Session, session_id: int, ended_at: datetime | None = None
) -> bool:
    at = ended_at or utcnow()
    result = db.execute(
        update(RollcallSession)
        .where(
            RollcallSession.id == session_id,
            RollcallSession.status == SESSION_CALLING,
        )
        .values(status="ended", ended_at=at, updated_at=at)
    )
    return result.rowcount == 1


def _session_filters(
    status: str | None,
    student_id: int | None,
    class_id: int | None,
) -> list:
    filters = []
    if status is not None:
        filters.append(RollcallSession.status == status)
    if class_id is not None:
        filters.append(RollcallSession.class_id == class_id)
    if student_id is not None:
        participation = (
            select(AttendanceRecord.id)
            .where(
                AttendanceRecord.session_id == RollcallSession.id,
                AttendanceRecord.student_id == student_id,
            )
            .exists()
        )
        filters.append(participation)
    return filters


def list_sessions(
    db: Session,
    page: int,
    page_size: int,
    status: str | None = None,
    student_id: int | None = None,
    class_id: int | None = None,
) -> tuple[list[RollcallSession], int]:
    filters = _session_filters(status, student_id, class_id)
    total = int(db.scalar(
        select(func.count(RollcallSession.id)).where(*filters)
    ) or 0)
    stmt = (
        select(RollcallSession)
        .where(*filters)
        .order_by(
            RollcallSession.started_at.desc(), RollcallSession.id.desc()
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(stmt).all()), total


def aggregate_session_counts(
    db: Session,
    session_ids: list[int],
    student_id: int | None = None,
) -> dict[int, dict[str, int]]:
    if not session_ids:
        return {}
    stmt = (
        select(
            AttendanceRecord.session_id,
            func.count(AttendanceRecord.id).label("total_count"),
            func.sum(
                case((AttendanceRecord.status == RECORD_PRESENT, 1), else_=0)
            ).label("present_count"),
            func.sum(
                case((AttendanceRecord.status == RECORD_ABSENT, 1), else_=0)
            ).label("absent_count"),
            func.sum(
                case((AttendanceRecord.status == RECORD_PENDING, 1), else_=0)
            ).label("pending_count"),
        )
        .where(AttendanceRecord.session_id.in_(session_ids))
        .group_by(AttendanceRecord.session_id)
    )
    if student_id is not None:
        stmt = stmt.where(AttendanceRecord.student_id == student_id)

    result: dict[int, dict[str, int]] = {}
    for row in db.execute(stmt):
        result[int(row.session_id)] = {
            "total_count": int(row.total_count or 0),
            "present_count": int(row.present_count or 0),
            "absent_count": int(row.absent_count or 0),
            "pending_count": int(row.pending_count or 0),
        }
    return result