from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import require_password_changed
from app.core.security import hash_password, verify_password
from app.models import User
from app.services.auth_service import seed_teacher


def _create_user(
    db: Session,
    username: str = "teacher",
    password: str = "Secret123",
    role: str = "teacher",
    active: bool = True,
    must_change_password: bool = False,
) -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        display_name="教师",
        student_id=None,
        must_change_password=must_change_password,
        active=active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(
    client: TestClient,
    username: str = "teacher",
    password: str = "Secret123",
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_login_returns_token_and_user(
    client: TestClient,
    db_session: Session,
) -> None:
    user = _create_user(db_session)

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "teacher", "password": "Secret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 28800
    assert data["access_token"]
    assert data["user"]["username"] == "teacher"
    assert data["user"]["role"] == "teacher"
    assert data["user"]["student_id"] is None
    assert data["user"]["must_change_password"] is False
    assert data["user"]["created_at"].endswith("+08:00")
    assert data["user"]["last_login_at"].endswith("+08:00")

    db_session.refresh(user)
    assert user.last_login_at is not None


def test_login_rejects_invalid_credentials_uniformly(
    client: TestClient,
    db_session: Session,
) -> None:
    _create_user(db_session)
    _create_user(
        db_session,
        username="disabled",
        active=False,
    )

    cases = [
        ("teacher", "wrong-password"),
        ("missing-user", "Secret123"),
        ("disabled", "Secret123"),
    ]
    for username, password in cases:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        assert response.status_code == 401
        body = response.json()
        assert body["code"] == 40102
        assert body["message"] == "用户名或密码错误"
        assert body["data"] is None


def test_me_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == 40101


def test_me_returns_current_user(
    client: TestClient,
    db_session: Session,
) -> None:
    _create_user(db_session)
    token = _login(client)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "teacher"
    assert body["data"]["role"] == "teacher"


def test_expired_token_returns_40103(
    client: TestClient,
    db_session: Session,
) -> None:
    user = _create_user(db_session)
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "student_id": None,
            "iat": now - timedelta(hours=9),
            "exp": now - timedelta(hours=1),
            "jti": "expired-token",
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == 40103


def test_change_password_validation_and_success(
    client: TestClient,
    db_session: Session,
) -> None:
    user = _create_user(
        db_session,
        password="OldPass123",
        must_change_password=True,
    )
    token = _login(client, password="OldPass123")
    headers = {"Authorization": f"Bearer {token}"}

    wrong_old = client.post(
        "/api/v1/auth/change-password",
        json={
            "old_password": "WrongPass1",
            "new_password": "NewPass123",
        },
        headers=headers,
    )
    assert wrong_old.status_code == 400
    assert wrong_old.json()["code"] == 40003

    weak_new = client.post(
        "/api/v1/auth/change-password",
        json={
            "old_password": "OldPass123",
            "new_password": "abcdefgh",
        },
        headers=headers,
    )
    assert weak_new.status_code == 400
    assert weak_new.json()["code"] == 40004

    same_password = client.post(
        "/api/v1/auth/change-password",
        json={
            "old_password": "OldPass123",
            "new_password": "OldPass123",
        },
        headers=headers,
    )
    assert same_password.status_code == 400
    assert same_password.json()["code"] == 40004

    changed = client.post(
        "/api/v1/auth/change-password",
        json={
            "old_password": "OldPass123",
            "new_password": "NewPass123",
        },
        headers=headers,
    )
    assert changed.status_code == 200
    assert changed.json()["data"] == {"changed": True}

    db_session.refresh(user)
    assert user.must_change_password is False
    assert verify_password("NewPass123", user.password_hash)

    old_login = client.post(
        "/api/v1/auth/login",
        json={"username": "teacher", "password": "OldPass123"},
    )
    assert old_login.status_code == 401
    assert old_login.json()["code"] == 40102

    new_login = client.post(
        "/api/v1/auth/login",
        json={"username": "teacher", "password": "NewPass123"},
    )
    assert new_login.status_code == 200


def test_must_change_password_blocks_business_routes(
    client: TestClient,
    db_session: Session,
) -> None:
    _create_user(
        db_session,
        password="Secret123",
        must_change_password=True,
    )

    @client.app.get("/api/v1/_test/protected")
    def protected(
        user: User = Depends(require_password_changed),
    ) -> dict[str, bool]:
        return {"ok": True}

    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200

    response = client.get("/api/v1/_test/protected", headers=headers)
    assert response.status_code == 403
    assert response.json()["code"] == 40302


def test_seed_teacher_creates_and_resets(db_session: Session) -> None:
    user = seed_teacher(db_session, "teacher", "SeedPass123")

    assert user.role == "teacher"
    assert user.student_id is None
    assert user.must_change_password is True
    assert verify_password("SeedPass123", user.password_hash)

    same = seed_teacher(db_session, "teacher", "OtherPass123")
    assert same.id == user.id
    assert verify_password("SeedPass123", same.password_hash)

    reset = seed_teacher(
        db_session,
        "teacher",
        "ResetPass123",
        reset=True,
    )
    assert reset.id == user.id
    assert reset.must_change_password is True
    assert verify_password("ResetPass123", reset.password_hash)