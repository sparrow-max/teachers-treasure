from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ApiError, ErrorCode
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repo import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise ApiError(ErrorCode.UNAUTHORIZED)
    payload = decode_access_token(credentials.credentials)
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ApiError(ErrorCode.UNAUTHORIZED) from exc
    user = get_user_by_id(db, user_id)
    if user is None:
        raise ApiError(ErrorCode.UNAUTHORIZED)
    try:
        token_version = int(payload.get("pv", -1))
    except (TypeError, ValueError) as exc:
        raise ApiError(ErrorCode.UNAUTHORIZED) from exc
    if token_version != user.token_version:
        raise ApiError(ErrorCode.TOKEN_EXPIRED)
    return user


def require_password_changed(
    user: User = Depends(get_current_user),
) -> User:
    if user.must_change_password:
        raise ApiError(ErrorCode.PASSWORD_CHANGE_REQUIRED)
    return user


def require_roles(*roles: str):
    def dependency(
        user: User = Depends(require_password_changed),
    ) -> User:
        if user.role not in roles:
            raise ApiError(ErrorCode.FORBIDDEN)
        return user

    return dependency