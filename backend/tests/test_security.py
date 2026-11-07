import pytest

from app.core.config import settings
from app.core.errors import ApiError, ErrorCode
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    password_hash = hash_password("Abc12345")

    assert password_hash != "Abc12345"
    assert verify_password("Abc12345", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_access_token_roundtrip() -> None:
    token, expires_in = create_access_token(
        user_id=7,
        username="teacher",
        role="teacher",
        student_id=None,
    )
    payload = decode_access_token(token)

    assert expires_in == settings.jwt_expire_minutes * 60
    assert payload["sub"] == "7"
    assert payload["username"] == "teacher"
    assert payload["role"] == "teacher"
    assert payload["student_id"] is None
    assert payload["jti"]


def test_invalid_token_maps_to_unauthorized() -> None:
    with pytest.raises(ApiError) as exc_info:
        decode_access_token("not-a-valid-token")

    assert exc_info.value.code == ErrorCode.UNAUTHORIZED
    assert exc_info.value.http_status == 401