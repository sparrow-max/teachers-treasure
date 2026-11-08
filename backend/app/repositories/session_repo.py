from datetime import datetime

from sqlalchemy import exists, func, select, update
from sqlalchemy.orm import Session

from app.models.record import AttendanceRecord
from app.models.session import RollcallSession


def _empty_counts() -> dict[str, int]:
    return {
        "pending": 0,
        "present": 0,
        "absent": 0,
        "total": 0,
    }


def create_session(
    db: Session,
    title: str,
    order_by: str,
    started_at: datetime,
) -> RollcallSession:
    session = RollcallSession(
        title=title,
        status="calling",
        order_by=order_by,
        started_at=started_at,
        ended_at=None,
    )
    db.add(session)
    db.flush()
    db.refresh(session)
    return session


def get_session(
    db: Session,
    session_id: int,
    for_update: bool = False,
) -> RollcallSession | None:
    statement = select(RollcallSession).where(
        RollcallSession.id == session_id
    )
    if for_update:
        statement = statement.with_for_update()
    return db.scalar(statement)


def finish_session(
    db: Session,
    session_id: int,
    ended_at: datetime,
) -> bool:
    result = db.execute(
        update(RollcallSession)
        .where(
            RollcallSession.id == session_id,
            RollcallSession.status == "calling",
        )
        .values(status="ended", ended_at=ended_at)
    )
    return result.rowcount == 1


def list_sessions(
    db: Session,
    page: int,
    page_size: int,
    status: str | None = None,
    student_id: int | None = None,
) -> tuple[list[RollcallSession], int]:
    conditions = []
    if status is not None:
        conditions.append(RollcallSession.status == status)
    if student_id is not None:
        conditions.append(
            exists().where(
                AttendanceRecord.session_id == RollcallSession.id,
                AttendanceRecord.student_id == student_id,
            )
        )

    statement = select(RollcallSession)
    if conditions:
        statement = statement.where(*conditions)

    total = db.scalar(
        select(func.count()).select_from(statement.subquery())
    )
    items = list(
        db.scalars(
            statement.order_by(
                RollcallSession.started_at.desc(),
                RollcallSession.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return items, int(total or 0)


def aggregate_session_counts(
    db: Session,
    session_ids: list[int],
    student_id: int | None = None,
) -> dict[int, dict[str, int]]:
    counts = {session_id: _empty_counts() for session_id in session_ids}
    if not session_ids:
        return counts

    statement = (
        select(
            AttendanceRecord.session_id,
            AttendanceRecord.status,
            func.count(AttendanceRecord.id),
        )
        .where(AttendanceRecord.session_id.in_(session_ids))
        .group_by(
            AttendanceRecord.session_id,
            AttendanceRecord.status,
        )
    )
    if student_id is not None:
        statement = statement.where(
            AttendanceRecord.student_id == student_id
        )

    for session_id, record_status, count in db.execute(statement):
        session_counts = counts.get(session_id)
        if session_counts is None:
            continue
        if record_status in ("pending", "present", "absent"):
            session_counts[record_status] = int(count)
            session_counts["total"] += int(count)
    return counts