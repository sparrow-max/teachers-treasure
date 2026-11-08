from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import ok
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    UserOut,
)
from app.schemas.common import ApiResponse, ChangedResult
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponse],
    summary="登录并获取 Token",
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    return ok(auth_service.login(db, payload))


@router.get(
    "/me",
    response_model=ApiResponse[UserOut],
    summary="获取当前登录用户",
)
def me(
    current_user: User = Depends(get_current_user),
):
    return ok(UserOut.model_validate(current_user))


@router.post(
    "/change-password",
    response_model=ApiResponse[ChangedResult],
    summary="修改本人密码",
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    auth_service.change_password(db, current_user.id, payload)
    return ok(ChangedResult(changed=True))