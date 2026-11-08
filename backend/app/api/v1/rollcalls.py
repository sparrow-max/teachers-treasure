from typing import Literal

from fastapi import APIRouter, Depends, Path, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_password_changed, require_roles
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
    status_code=http_status.HTTP_201_CREATED,
    summary="开始点名并创建场次",
)
def start_rollcall(
    payload: RollcallCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(
        require_roles("teacher", "monitor")
    ),
):
    return ok(rollcall_service.start_rollcall(db, payload))


@router.get(
    "",
    response_model=ApiResponse[Page[SessionOut]],
    summary="场次分页列表",
)
def list_rollcalls(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Literal["calling", "ended"] | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    return ok(
        rollcall_service.list_sessions(
            db,
            page,
            page_size,
            status,
            current_user,
        )
    )


@router.get(
    "/{session_id}",
    response_model=ApiResponse[SessionDetail],
    summary="场次详情与记录",
)
def get_rollcall(
    session_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    return ok(
        rollcall_service.get_session_detail(
            db,
            session_id,
            current_user,
        )
    )


@router.post(
    "/{session_id}/checkin",
    response_model=ApiResponse[RecordOut],
    summary="本人签到",
)
def checkin(
    session_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("student", "monitor")
    ),
):
    return ok(
        rollcall_service.checkin(db, session_id, current_user)
    )


@router.post(
    "/{session_id}/end",
    response_model=ApiResponse[SessionDetail],
    summary="结束点名并生成缺勤",
)
def end_rollcall(
    session_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    _current_user: User = Depends(
        require_roles("teacher", "monitor")
    ),
):
    return ok(rollcall_service.end_rollcall(db, session_id))