from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.response import ok
from app.models.user import User
from app.schemas.common import ApiResponse, Page
from app.schemas.rollcall import (
    RecordOut,
    RollcallCreate,
    SessionDetail,
    SessionOut,
)
from app.services import rollcall_service

router = APIRouter(prefix="/rollcalls", tags=["rollcalls"])


@router.post(
    "",
    response_model=ApiResponse[SessionDetail],
    status_code=status.HTTP_201_CREATED,
    summary="开始点名",
)
def start_rollcall(
    payload: RollcallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "monitor")),
):
    return ok(rollcall_service.start_rollcall(db, current_user, payload))


@router.get(
    "",
    response_model=ApiResponse[Page[SessionOut]],
    summary="场次分页列表",
)
def list_sessions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    class_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("teacher", "monitor", "student")
    ),
):
    return ok(
        rollcall_service.list_sessions(
            db, current_user, page, page_size, status, class_id
        )
    )


@router.get(
    "/{session_id}",
    response_model=ApiResponse[SessionDetail],
    summary="场次详情",
)
def get_session(
    session_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("teacher", "monitor", "student")
    ),
):
    return ok(rollcall_service.get_session_detail(db, current_user, session_id))


@router.post(
    "/{session_id}/checkin",
    response_model=ApiResponse[RecordOut],
    summary="本人签到",
)
def checkin(
    session_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("student", "monitor")),
):
    return ok(rollcall_service.checkin(db, current_user, session_id))


@router.post(
    "/{session_id}/end",
    response_model=ApiResponse[SessionDetail],
    summary="结束点名",
)
def end_rollcall(
    session_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("teacher", "monitor")),
):
    return ok(rollcall_service.end_rollcall(db, current_user, session_id))