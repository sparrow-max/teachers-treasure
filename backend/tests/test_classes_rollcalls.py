from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Student, User


def _create_class(
    client: TestClient,
    headers: dict[str, str],
    code: str = "C-002",
    name: str = "二班",
) -> int:
    response = client.post(
        "/api/v1/classes",
        json={"name": name, "code": code},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


def _start_rollcall(
    client: TestClient,
    headers: dict[str, str],
    class_id: int,
    title: str,
) -> dict:
    response = client.post(
        "/api/v1/rollcalls",
        json={"class_id": class_id, "title": title},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_class_lifecycle_and_scope(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
    monitor_headers: dict[str, str],
    student_headers: dict[str, str],
) -> None:
    second_id = _create_class(client, teacher_headers)

    teacher_list = client.get(
        "/api/v1/classes", headers=teacher_headers
    )
    assert teacher_list.status_code == 200
    assert [item["code"] for item in teacher_list.json()["data"]] == [
        "C-001", "C-002",
    ]

    monitor_list = client.get(
        "/api/v1/classes", headers=monitor_headers
    )
    assert [item["id"] for item in monitor_list.json()["data"]] == [1]

    student_list = client.get(
        "/api/v1/classes", headers=student_headers
    )
    assert [item["id"] for item in student_list.json()["data"]] == [1]

    duplicate = client.post(
        "/api/v1/classes",
        json={"name": "重复编号", "code": "C-002"},
        headers=teacher_headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 40907

    deleted_empty = client.delete(
        f"/api/v1/classes/{second_id}", headers=teacher_headers
    )
    assert deleted_empty.status_code == 200

    deleted_non_empty = client.delete(
        "/api/v1/classes/1", headers=teacher_headers
    )
    assert deleted_non_empty.status_code == 409
    assert deleted_non_empty.json()["code"] == 40908


def test_rollcall_checkin_and_end(
    client: TestClient,
    teacher_headers: dict[str, str],
    student_headers: dict[str, str],
    monitor_headers: dict[str, str],
) -> None:
    detail = _start_rollcall(
        client, teacher_headers, 1, "一班点名"
    )
    session_id = detail["session"]["id"]
    assert detail["session"]["class_id"] == 1
    assert detail["session"]["total_count"] == 2
    assert detail["session"]["pending_count"] == 2

    checkin = client.post(
        f"/api/v1/rollcalls/{session_id}/checkin",
        headers=student_headers,
    )
    assert checkin.status_code == 200
    assert checkin.json()["data"]["status"] == "present"

    duplicate = client.post(
        f"/api/v1/rollcalls/{session_id}/checkin",
        headers=student_headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 40902

    monitor_checkin = client.post(
        f"/api/v1/rollcalls/{session_id}/checkin",
        headers=monitor_headers,
    )
    assert monitor_checkin.status_code == 200

    listing = client.get(
        "/api/v1/rollcalls",
        params={"class_id": 1},
        headers=teacher_headers,
    )
    assert listing.status_code == 200
    item = listing.json()["data"]["items"][0]
    assert item["present_count"] == 2
    assert item["pending_count"] == 0

    ended = client.post(
        f"/api/v1/rollcalls/{session_id}/end",
        headers=teacher_headers,
    )
    assert ended.status_code == 200
    assert ended.json()["data"]["session"]["absent_count"] == 0
    assert ended.json()["data"]["session"]["present_count"] == 2

    after_end = client.post(
        f"/api/v1/rollcalls/{session_id}/checkin",
        headers=student_headers,
    )
    assert after_end.status_code == 409
    assert after_end.json()["code"] == 40903

    student_detail = client.get(
        f"/api/v1/rollcalls/{session_id}",
        headers=student_headers,
    )
    assert student_detail.status_code == 200
    assert len(student_detail.json()["data"]["records"]) == 1


def test_cross_class_rollcall_isolation(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
    student_headers: dict[str, str],
) -> None:
    second_id = _create_class(
        client, teacher_headers, "C-010", "十班"
    )
    student = Student(
        student_no="20230099",
        name="十班学生",
        role="学生",
        class_id=second_id,
        active=True,
    )
    db_session.add(student)
    db_session.flush()
    db_session.add(
        User(
            username="20230099",
            password_hash=hash_password("Student123"),
            role="student",
            display_name="十班学生",
            student_id=student.id,
            must_change_password=False,
            active=True,
        )
    )
    db_session.commit()

    detail = _start_rollcall(
        client, teacher_headers, second_id, "十班点名"
    )
    session_id = detail["session"]["id"]

    cross_detail = client.get(
        f"/api/v1/rollcalls/{session_id}",
        headers=student_headers,
    )
    assert cross_detail.status_code == 404
    assert cross_detail.json()["code"] == 40402

    cross_checkin = client.post(
        f"/api/v1/rollcalls/{session_id}/checkin",
        headers=student_headers,
    )
    assert cross_checkin.status_code == 404
    assert cross_checkin.json()["code"] == 40402

    filtered = client.get(
        "/api/v1/rollcalls",
        params={"class_id": second_id},
        headers=teacher_headers,
    )
    assert filtered.status_code == 200
    assert filtered.json()["data"]["total"] == 1
    assert filtered.json()["data"]["items"][0]["class_id"] == second_id