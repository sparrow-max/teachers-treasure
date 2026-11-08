from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import Student, User


def test_teacher_lists_active_students_sorted(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
) -> None:
    db_session.add_all(
        [
            Student(
                student_no="20230003",
                name="丙",
                role="学生",
                active=True,
            ),
            Student(
                student_no="20230001",
                name="甲",
                role="学生",
                active=True,
            ),
            Student(
                student_no="20230002",
                name="乙",
                role="学生",
                active=False,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/students", headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert [
        item["student_no"] for item in body["data"]
    ] == ["20230001", "20230003"]
    assert body["data"][0]["created_at"].endswith("+08:00")


def test_keyword_and_active_filters(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
) -> None:
    db_session.add_all(
        [
            Student(
                student_no="20230001",
                name="张三",
                role="学生",
                active=True,
            ),
            Student(
                student_no="20230002",
                name="李四",
                role="学生",
                active=True,
            ),
            Student(
                student_no="20230003",
                name="张小明",
                role="学生",
                active=False,
            ),
        ]
    )
    db_session.commit()

    by_name = client.get(
        "/api/v1/students",
        params={"keyword": "张"},
        headers=teacher_headers,
    )
    assert [
        item["student_no"] for item in by_name.json()["data"]
    ] == ["20230001"]

    by_no = client.get(
        "/api/v1/students",
        params={"keyword": "2023000"},
        headers=teacher_headers,
    )
    assert [
        item["student_no"] for item in by_no.json()["data"]
    ] == ["20230001", "20230002"]

    inactive = client.get(
        "/api/v1/students",
        params={"active": "false"},
        headers=teacher_headers,
    )
    assert [
        item["student_no"] for item in inactive.json()["data"]
    ] == ["20230003"]


def test_monitor_can_list_but_cannot_modify(
    client: TestClient,
    monitor_headers: dict[str, str],
) -> None:
    listed = client.get("/api/v1/students", headers=monitor_headers)
    assert listed.status_code == 200
    assert [
        item["student_no"] for item in listed.json()["data"]
    ] == ["20230001"]

    created = client.post(
        "/api/v1/students",
        json={"student_no": "20230020", "name": "不允许"},
        headers=monitor_headers,
    )
    assert created.status_code == 403
    assert created.json()["code"] == 40301

    deleted = client.delete(
        "/api/v1/students/1",
        headers=monitor_headers,
    )
    assert deleted.status_code == 403
    assert deleted.json()["code"] == 40301


def test_student_cannot_list_students(
    client: TestClient,
    student_headers: dict[str, str],
) -> None:
    response = client.get("/api/v1/students", headers=student_headers)

    assert response.status_code == 403
    assert response.json()["code"] == 40301


def test_create_student_creates_linked_account(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/students",
        json={
            "student_no": "20230009",
            "name": "王五",
            "role": "班长",
            "initial_password": "Init1234",
        },
        headers=teacher_headers,
    )

    assert response.status_code == 201
    body = response.json()
    data = body["data"]
    assert body["code"] == 0
    assert data["student_no"] == "20230009"
    assert data["name"] == "王五"
    assert data["role"] == "班长"
    assert data["active"] is True
    assert "initial_password" not in data
    assert "password_hash" not in data

    student = db_session.scalar(
        select(Student).where(Student.student_no == "20230009")
    )
    user = db_session.scalar(
        select(User).where(User.username == "20230009")
    )
    assert student is not None
    assert user is not None
    assert user.student_id == student.id
    assert user.role == "monitor"
    assert user.must_change_password is True
    assert user.active is True
    assert verify_password("Init1234", user.password_hash)

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "20230009", "password": "Init1234"},
    )
    assert login.status_code == 200
    assert login.json()["data"]["user"]["role"] == "monitor"
    assert (
        login.json()["data"]["user"]["must_change_password"] is True
    )


def test_create_student_defaults_password_to_student_no(
    client: TestClient,
    teacher_headers: dict[str, str],
) -> None:
    created = client.post(
        "/api/v1/students",
        json={"student_no": "20230010", "name": "赵六"},
        headers=teacher_headers,
    )
    assert created.status_code == 201
    assert created.json()["data"]["role"] == "学生"

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "20230010", "password": "20230010"},
    )
    assert login.status_code == 200
    assert login.json()["data"]["user"]["role"] == "student"


def test_create_student_validation(
    client: TestClient,
    teacher_headers: dict[str, str],
) -> None:
    cases = [
        (
            {"student_no": "12345", "name": "张三"},
            40001,
        ),
        (
            {"student_no": "2023000A!", "name": "张三"},
            40001,
        ),
        (
            {"student_no": "20230011", "name": ""},
            40001,
        ),
        (
            {"student_no": "20230011", "name": "张三", "role": "教师"},
            40001,
        ),
        (
            {
                "student_no": "20230011",
                "name": "张三",
                "initial_password": "123",
            },
            40002,
        ),
    ]

    for payload, expected_code in cases:
        response = client.post(
            "/api/v1/students",
            json=payload,
            headers=teacher_headers,
        )
        assert response.status_code == 400
        assert response.json()["code"] == expected_code


def test_duplicate_student_no_rejected_even_after_delete(
    client: TestClient,
    teacher_headers: dict[str, str],
) -> None:
    payload = {"student_no": "20230012", "name": "重复学号"}

    first = client.post(
        "/api/v1/students",
        json=payload,
        headers=teacher_headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/api/v1/students",
        json=payload,
        headers=teacher_headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 40901

    student_id = first.json()["data"]["id"]
    deleted = client.delete(
        f"/api/v1/students/{student_id}",
        headers=teacher_headers,
    )
    assert deleted.status_code == 200

    reused = client.post(
        "/api/v1/students",
        json=payload,
        headers=teacher_headers,
    )
    assert reused.status_code == 409
    assert reused.json()["code"] == 40901


def test_username_conflict_returns_40906(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
) -> None:
    db_session.add(
        User(
            username="20230013",
            password_hash=hash_password("Conflict123"),
            role="teacher",
            display_name="冲突账号",
            student_id=None,
            must_change_password=False,
            active=True,
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/students",
        json={"student_no": "20230013", "name": "冲突学生"},
        headers=teacher_headers,
    )

    assert response.status_code == 409
    assert response.json()["code"] == 40906
    assert (
        db_session.scalar(
            select(Student).where(Student.student_no == "20230013")
        )
        is None
    )


def test_delete_soft_deletes_and_disables_account(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
) -> None:
    created = client.post(
        "/api/v1/students",
        json={"student_no": "20230014", "name": "删除我"},
        headers=teacher_headers,
    )
    assert created.status_code == 201
    student_id = created.json()["data"]["id"]

    deleted = client.delete(
        f"/api/v1/students/{student_id}",
        headers=teacher_headers,
    )
    assert deleted.status_code == 200
    assert deleted.json()["data"] == {
        "id": student_id,
        "deleted": True,
    }

    db_session.expire_all()
    student = db_session.scalar(
        select(Student).where(Student.student_no == "20230014")
    )
    user = db_session.scalar(
        select(User).where(User.username == "20230014")
    )
    assert student is not None
    assert student.active is False
    assert user is not None
    assert user.active is False

    default_list = client.get(
        "/api/v1/students",
        headers=teacher_headers,
    )
    assert "20230014" not in [
        item["student_no"] for item in default_list.json()["data"]
    ]

    inactive_list = client.get(
        "/api/v1/students",
        params={"active": "false"},
        headers=teacher_headers,
    )
    assert "20230014" in [
        item["student_no"] for item in inactive_list.json()["data"]
    ]

    again = client.delete(
        f"/api/v1/students/{student_id}",
        headers=teacher_headers,
    )
    assert again.status_code == 404
    assert again.json()["code"] == 40401

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "20230014", "password": "20230014"},
    )
    assert login.status_code == 401
    assert login.json()["code"] == 40102


def test_create_student_without_account(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/students",
        json={
            "student_no": "20230015",
            "name": "无账号",
            "create_account": False,
        },
        headers=teacher_headers,
    )

    assert response.status_code == 201
    student_id = response.json()["data"]["id"]
    assert (
        db_session.scalar(
            select(User).where(User.student_id == student_id)
        )
        is None
    )

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "20230015", "password": "20230015"},
    )
    assert login.status_code == 401
    assert login.json()["code"] == 40102