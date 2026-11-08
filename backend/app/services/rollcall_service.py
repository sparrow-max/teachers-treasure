from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ApiError, ErrorCode
from app.models.record import AttendanceRecord
from app.models.session import RollcallSession
from app.models.user import User
from app.repositories import record_repo, session_repo, student_repo
from app.schemas.common import Page
from app.schemas.rollcall import (
    RecordOut,
    RollcallCreate,
    SessionDetail,
    SessionOut,
)


def _default_title() -> str:
    now = datetime.now(ZoneInfo(settings.app_timezone))
    return f"{now:%Y-%m-%d} 课堂点名"


def _empty_counts() -> dict[str, int]:
    return {
        "pending": 0,
        "present": 0,
        "absent": 0,
        "total": 0,
    }


def _counts_from_records(
    records: list[AttendanceRecord],
) -> dict[str, int]:
    counts = _empty_counts()
    counts["total"] = len(records)
    for record in records:
        if record.status in ("pending", "present", "absent"):
            counts[record.status] += 1
    return counts


def _session_out(
    session: RollcallSession,
    counts: dict[str, int],
) -> SessionOut:
    return SessionOut(
        id=session.id,
        title=session.title,
        status=session.status,
        order_by=session.order_by,
        started_at=session.started_at,
        ended_at=session.ended_at,
        total_count=counts["total"],
        present_count=counts["present"],
        absent_count=counts["absent"],
        pending_count=counts["pending"],
    )


def _detail(
    session: RollcallSession,
    records: list[AttendanceRecord],
) -> SessionDetail:
    return SessionDetail(
        session=_session_out(session, _counts_from_records(records)),
        records=[
            RecordOut.model_validate(record)
            for record in records
        ],
    )


def start_rollcall(
    db: Session,
    payload: RollcallCreate,
) -> SessionDetail:
    students = student_repo.list_active_students_ordered(
        db,
        payload.order_by,
    )
    if not students:
        raise ApiError(ErrorCode.NO_ACTIVE_STUDENTS)

    title = payload.title or _default_title()
    started_at = datetime.now(timezone.utc)

    try:
        session = session_repo.create_session(
            db,
            title,
            payload.order_by,
            started_at,
        )
        rows = [
            {
                "session_id": session.id,
                "student_id": student.id,
                "student_no": student.student_no,
                "student_name": student.name,
                "role": student.role,
                "order_no": order_no,
                "status": "pending",
                "checked_at": None,
            }
            for order_no, student in enumerate(students, start=1)
        ]
        record_repo.bulk_create_records(db, rows)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(session)
    records = record_repo.list_records(db, session.id)
    return _detail(session, records)


def _student_scope(user: User) -> int | None:
    if user.role != "student":
        return None
    if user.student_id is None:
        raise ApiError(ErrorCode.FORBIDDEN)
    return user.student_id


def list_sessions(
    db: Session,
    page: int,
    page_size: int,
    status: str | None,
    current_user: User,
) -> Page[SessionOut]:
    student_id = _student_scope(current_user)
    sessions, total = session_repo.list_sessions(
        db,
        page,
        page_size,
        status,
        student_id,
    )
    counts = session_repo.aggregate_session_counts(
        db,
        [session.id for session in sessions],
        student_id=student_id,
    )
    items = [
        _session_out(
            session,
            counts.get(session.id, _empty_counts()),
        )
        for session in sessions
    ]
    return Page(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


def get_session_detail(
    db: Session,
    session_id: int,
    current_user: User,
) -> SessionDetail:
    session = session_repo.get_session(db, session_id)
    if session is None:
        raise ApiError(ErrorCode.SESSION_NOT_FOUND)

    student_id = None
    if current_user.role == "student":
        student_id = current_user.student_id
        if student_id is None:
            raise ApiError(ErrorCode.SESSION_NOT_FOUND)

    records = record_repo.list_records(
        db,
        session_id,
        student_id=student_id,
    )
    if student_id is not None and not records:
        raise ApiError(ErrorCode.SESSION_NOT_FOUND)

    return _detail(session, records)


def checkin(
    db: Session,
    session_id: int,
    current_user: User,
) -> RecordOut:
    student_id = current_user.student_id
    if current_user.role == "teacher" or student_id is None:
        raise ApiError(ErrorCode.FORBIDDEN)

    checked_at = datetime.now(timezone.utc)
    updated = record_repo.mark_present(
        db,
        session_id,
        student_id,
        checked_at,
    )
    if updated == 1:
        db.commit()
        record = record_repo.get_record(db, session_id, student_id)
        return RecordOut.model_validate(record)

    db.rollback()
    session = session_repo.get_session(db, session_id)
    if session is None:
        raise ApiError(ErrorCode.SESSION_NOT_FOUND)
    if session.status == "ended":
        raise ApiError(ErrorCode.ROLLCALL_ENDED)

    record = record_repo.get_record(db, session_id, student_id)
    if record is None:
        raise ApiError(ErrorCode.STUDENT_NOT_IN_SESSION)
    if record.status == "present":
        raise ApiError(ErrorCode.ALREADY_CHECKED_IN)
    raise ApiError(ErrorCode.ROLLCALL_ENDED)


def end_rollcall(
    db: Session,
    session_id: int,
) -> SessionDetail:
    session = session_repo.get_session(
        db,
        session_id,
        for_update=True,
    )
    if session is None:
        raise ApiError(ErrorCode.SESSION_NOT_FOUND)
    if session.status == "ended":
        raise ApiError(ErrorCode.ROLLCALL_ENDED)

    ended_at = datetime.now(timezone.utc)
    try:
        record_repo.mark_pending_absent(db, session_id, ended_at)
        finished = session_repo.finish_session(
            db,
            session_id,
            ended_at,
        )
        if not finished:
            raise ApiError(ErrorCode.ROLLCALL_ENDED)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(session)
    records = record_repo.list_records(db, session_id)
    return _detail(session, records)