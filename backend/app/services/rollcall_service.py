from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ApiError, ErrorCode
from app.repositories import class_repo, record_repo, session_repo, student_repo
from app.schemas.rollcall import (
    RecordOut,
    RollcallCreate,
    SessionDetail,
    SessionOut,
)
from app.schemas.common import Page
from database.models import (
    RECORD_PENDING,
    RECORD_PRESENT,
    SESSION_ENDED,
    User,
)

_ZERO_COUNTS = {
    "total_count": 0,
    "present_count": 0,
    "absent_count": 0,
    "pending_count": 0,
}


def _own_class_id(user: User) -> int:
    class_id = user.class_id
    if class_id is None:
        raise ApiError(ErrorCode.FORBIDDEN)
    return class_id


def _resolve_class_id(user: User, requested: int | None) -> int:
    if user.role == "teacher":
        if requested is None:
            raise ApiError(ErrorCode.VALIDATION_ERROR)
        return requested
    own = _own_class_id(user)
    if requested is not None and requested != own:
        raise ApiError(ErrorCode.FORBIDDEN)
    return own


def _assert_session_scope(user: User, class_id: int) -> None:
    if user.role == "teacher":
        return
    if _own_class_id(user) != class_id:
        raise ApiError(ErrorCode.SESSION_NOT_FOUND)


def _session_out(session, counts: dict[str, int]) -> SessionOut:
    return SessionOut(
        id=session.id,
        class_id=session.class_id,
        title=session.title,
        status=session.status,
        order_by=session.order_by,
        started_at=session.started_at,
        ended_at=session.ended_at,
        total_count=counts.get("total_count", 0),
        present_count=counts.get("present_count", 0),
        absent_count=counts.get("absent_count", 0),
        pending_count=counts.get("pending_count", 0),
    )


def get_session_detail(
    db: Session, user: User, session_id: int
) -> SessionDetail:
    session = session_repo.get_session(db, session_id)
    if session is None:
        raise ApiError(ErrorCode.SESSION_NOT_FOUND)
    _assert_session_scope(user, session.class_id)

    student_id = user.student_id if user.role == "student" else None
    records = record_repo.list_records(
        db, session_id, student_id=student_id
    )
    if user.role == "student" and not records:
        raise ApiError(ErrorCode.SESSION_NOT_FOUND)

    counts = session_repo.aggregate_session_counts(
        db, [session_id], student_id=student_id
    ).get(session_id, _ZERO_COUNTS)
    return SessionDetail(
        session=_session_out(session, counts),
        records=[RecordOut.model_validate(record) for record in records],
    )


def start_rollcall(
    db: Session, user: User, payload: RollcallCreate
) -> SessionDetail:
    class_id = _resolve_class_id(user, payload.class_id)
    classroom = class_repo.get_class(db, class_id)
    if classroom is None or not classroom.active:
        raise ApiError(ErrorCode.CLASS_NOT_FOUND)

    students = student_repo.list_active_students_ordered(
        db, payload.order_by, class_id
    )
    if not students:
        raise ApiError(ErrorCode.NO_ACTIVE_STUDENTS)

    title = payload.title or (
        datetime.now(ZoneInfo(settings.app_timezone))
        .strftime("%Y-%m-%d 课堂点名")
    )
    try:
        session = session_repo.create_session(
            db, title, payload.order_by, class_id
        )
        record_repo.bulk_create_records(db, [
            {
                "session_id": session.id,
                "student_id": student.id,
                "student_no": student.student_no,
                "student_name": student.name,
                "role": student.role,
                "order_no": index,
                "status": RECORD_PENDING,
            }
            for index, student in enumerate(students, start=1)
        ])
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(ErrorCode.INTERNAL_ERROR) from exc

    return get_session_detail(db, user, session.id)


def list_sessions(
    db: Session,
    user: User,
    page: int,
    page_size: int,
    status: str | None,
    class_id: int | None,
) -> Page[SessionOut]:
    if user.role == "teacher":
        scoped_class_id = class_id
        student_id = None
    else:
        scoped_class_id = _own_class_id(user)
        if class_id is not None and class_id != scoped_class_id:
            raise ApiError(ErrorCode.FORBIDDEN)
        student_id = user.student_id if user.role == "student" else None

    items, total = session_repo.list_sessions(
        db,
        page,
        page_size,
        status=status,
        student_id=student_id,
        class_id=scoped_class_id,
    )
    session_ids = [item.id for item in items]
    counts = session_repo.aggregate_session_counts(
        db, session_ids, student_id=student_id
    )
    return Page(
        items=[
            _session_out(item, counts.get(item.id, _ZERO_COUNTS))
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


def checkin(db: Session, user: User, session_id: int) -> RecordOut:
    if user.student_id is None:
        raise ApiError(ErrorCode.FORBIDDEN)
    session = session_repo.get_session(db, session_id)
    if session is None:
        raise ApiError(ErrorCode.SESSION_NOT_FOUND)
    _assert_session_scope(user, session.class_id)
    if session.status == SESSION_ENDED:
        raise ApiError(ErrorCode.ROLLCALL_ENDED)

    updated = record_repo.mark_present(
        db, session_id, user.student_id
    )
    if updated == 0:
        record = record_repo.get_record(db, session_id, user.student_id)
        if record is None:
            raise ApiError(ErrorCode.STUDENT_NOT_IN_SESSION)
        if record.status == RECORD_PRESENT:
            raise ApiError(ErrorCode.ALREADY_CHECKED_IN)
        raise ApiError(ErrorCode.STUDENT_NOT_IN_SESSION)
    db.commit()
    record = record_repo.get_record(db, session_id, user.student_id)
    if record is None:
        raise ApiError(ErrorCode.STUDENT_NOT_IN_SESSION)
    return RecordOut.model_validate(record)


def end_rollcall(
    db: Session, user: User, session_id: int
) -> SessionDetail:
    session = session_repo.get_session(db, session_id)
    if session is None:
        raise ApiError(ErrorCode.SESSION_NOT_FOUND)
    _assert_session_scope(user, session.class_id)
    if session.status == SESSION_ENDED:
        raise ApiError(ErrorCode.ROLLCALL_ENDED)

    record_repo.mark_pending_absent(db, session_id)
    if not session_repo.finish_session(db, session_id):
        db.rollback()
        raise ApiError(ErrorCode.ROLLCALL_ENDED)
    db.commit()
    return get_session_detail(db, user, session_id)