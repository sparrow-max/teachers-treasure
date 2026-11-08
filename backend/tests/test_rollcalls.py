from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.models import (
    AttendanceRecord,
    Base,
    RollcallSession,
    Student,
    User,
)
from app.repositories import record_repo


def _add_student(
    db: Session,
    student_no: str,
    name: str,
    role: str = "学生",
    active: bool = True,
) -> Student:
    student = Student(
        student_no=student_no,
        name=name,
        role=role,
        active=active,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def _start(
    client: TestClient,
    headers: dict[str, str],
    payload: dict[str, object] | None = None,
) -> dict:
    response = client.post(
        "/api/v1/rollcalls",
        json=payload or {},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_start_rollcall_creates_pending_records(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
) -> None:
    _add_student(db_session, "20230003", "丙")
    _add_student(db_session, "20230001", "甲")
    _add_student(db_session, "20230002", "乙")

    data = _start(
        client,
        teacher_headers,
        {"title": "第一次点名"},
    )

    session = data["session"]
    assert session["title"] == "第一次点名"
    assert session["status"] == "calling"
    assert session["order_by"] == "student_no"
    assert session["total_count"] == 3
    assert session["pending_count"] == 3
    assert session["present_count"] == 0
    assert session["absent_count"] == 0
    assert session["ended_at"] is None
    assert session["started_at"].endswith("+08:00")

    assert [
        record["student_no"] for record in data["records"]
    ] == ["20230001", "20230002", "20230003"]
    assert [
        record["order_no"] for record in data["records"]
    ] == [1, 2, 3]
    assert all(
        record["status"] == "pending"
        for record in data["records"]
    )
    assert all(
        record["checked_at"] is None
        for record in data["records"]
    )
    assert (
        db_session.scalar(select(func.count(RollcallSession.id)))
        == 1
    )


def test_start_rollcall_uses_default_title(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
) -> None:
    _add_student(db_session, "20230001", "甲")

    data = _start(client, teacher_headers)

    assert data["session"]["title"].endswith("课堂点名")


def test_start_rollcall_rejects_empty_student_list(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/rollcalls",
        json={},
        headers=teacher_headers,
    )

    assert response.status_code == 409
    assert response.json()["code"] == 40905
    assert (
        db_session.scalar(select(func.count(RollcallSession.id)))
        == 0
    )


def test_monitor_can_start_rollcall(
    client: TestClient,
    monitor_headers: dict[str, str],
) -> None:
    data = _start(client, monitor_headers)

    assert data["session"]["total_count"] == 1
    assert data["records"][0]["student_no"] == "20230001"


def test_student_cannot_start_rollcall(
    client: TestClient,
    student_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/rollcalls",
        json={},
        headers=student_headers,
    )

    assert response.status_code == 403
    assert response.json()["code"] == 40301


def test_checkin_updates_record_and_blocks_duplicate(
    client: TestClient,
    teacher_headers: dict[str, str],
    student_headers: dict[str, str],
) -> None:
    data = _start(client, teacher_headers)
    session_id = data["session"]["id"]

    checked = client.post(
        f"/api/v1/rollcalls/{session_id}/checkin",
        headers=student_headers,
    )
    assert checked.status_code == 200
    record = checked.json()["data"]
    assert record["status"] == "present"
    assert record["student_no"] == "20230002"
    assert record["checked_at"].endswith("+08:00")

    duplicate = client.post(
        f"/api/v1/rollcalls/{session_id}/checkin",
        headers=student_headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 40902

    teacher_detail = client.get(
        f"/api/v1/rollcalls/{session_id}",
        headers=teacher_headers,
    )
    session = teacher_detail.json()["data"]["session"]
    assert session["total_count"] == 1
    assert session["present_count"] == 1
    assert session["pending_count"] == 0
    assert session["absent_count"] == 0

    student_detail = client.get(
        f"/api/v1/rollcalls/{session_id}",
        headers=student_headers,
    )
    student_data = student_detail.json()["data"]
    assert student_data["session"]["total_count"] == 1
    assert student_data["session"]["present_count"] == 1
    assert len(student_data["records"]) == 1
    assert "my_status" not in student_data["session"]
    assert "my_checked_at" not in student_data["session"]


def test_student_not_in_session_returns_40904(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
    student_headers: dict[str, str],
    student_user: User,
) -> None:
    _add_student(db_session, "20230001", "其他学生")

    student = db_session.get(Student, student_user.student_id)
    assert student is not None
    student.active = False
    db_session.commit()

    data = _start(client, teacher_headers)
    session_id = data["session"]["id"]
    assert [
        record["student_no"] for record in data["records"]
    ] == ["20230001"]

    response = client.post(
        f"/api/v1/rollcalls/{session_id}/checkin",
        headers=student_headers,
    )

    assert response.status_code == 409
    assert response.json()["code"] == 40904


def test_teacher_cannot_checkin(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
) -> None:
    _add_student(db_session, "20230001", "甲")
    data = _start(client, teacher_headers)
    session_id = data["session"]["id"]

    response = client.post(
        f"/api/v1/rollcalls/{session_id}/checkin",
        headers=teacher_headers,
    )

    assert response.status_code == 403
    assert response.json()["code"] == 40301


def test_student_cannot_end_rollcall(
    client: TestClient,
    teacher_headers: dict[str, str],
    student_headers: dict[str, str],
) -> None:
    data = _start(client, teacher_headers)
    session_id = data["session"]["id"]

    response = client.post(
        f"/api/v1/rollcalls/{session_id}/end",
        headers=student_headers,
    )

    assert response.status_code == 403
    assert response.json()["code"] == 40301


def test_end_rollcall_generates_absent_records(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
    student_headers: dict[str, str],
) -> None:
    _add_student(db_session, "20230001", "甲")
    _add_student(db_session, "20230003", "丙")

    data = _start(client, teacher_headers)
    session_id = data["session"]["id"]
    assert data["session"]["total_count"] == 3

    client.post(
        f"/api/v1/rollcalls/{session_id}/checkin",
        headers=student_headers,
    )

    ended = client.post(
        f"/api/v1/rollcalls/{session_id}/end",
        headers=teacher_headers,
    )
    assert ended.status_code == 200
    ended_data = ended.json()["data"]
    session = ended_data["session"]
    assert session["status"] == "ended"
    assert session["ended_at"].endswith("+08:00")
    assert session["total_count"] == 3
    assert session["present_count"] == 1
    assert session["absent_count"] == 2
    assert session["pending_count"] == 0

    records = {
        record["student_no"]: record
        for record in ended_data["records"]
    }
    assert records["20230002"]["status"] == "present"
    assert records["20230001"]["status"] == "absent"
    assert records["20230003"]["status"] == "absent"
    assert (
        records["20230001"]["checked_at"]
        == session["ended_at"]
    )

    repeat = client.post(
        f"/api/v1/rollcalls/{session_id}/end",
        headers=teacher_headers,
    )
    assert repeat.status_code == 409
    assert repeat.json()["code"] == 40903

    late = client.post(
        f"/api/v1/rollcalls/{session_id}/checkin",
        headers=student_headers,
    )
    assert late.status_code == 409
    assert late.json()["code"] == 40903


def test_missing_session_returns_40402(
    client: TestClient,
    teacher_headers: dict[str, str],
    student_headers: dict[str, str],
) -> None:
    detail = client.get(
        "/api/v1/rollcalls/9999",
        headers=teacher_headers,
    )
    assert detail.status_code == 404
    assert detail.json()["code"] == 40402

    checkin = client.post(
        "/api/v1/rollcalls/9999/checkin",
        headers=student_headers,
    )
    assert checkin.status_code == 404
    assert checkin.json()["code"] == 40402


def test_student_list_only_returns_participated_sessions(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
    student_headers: dict[str, str],
    student_user: User,
) -> None:
    _add_student(db_session, "20230001", "甲")

    first = _start(
        client,
        teacher_headers,
        {"title": "包含学生"},
    )
    first_id = first["session"]["id"]

    student = db_session.get(Student, student_user.student_id)
    assert student is not None
    student.active = False
    db_session.commit()

    second = _start(
        client,
        teacher_headers,
        {"title": "不包含学生"},
    )
    second_id = second["session"]["id"]

    student_list = client.get(
        "/api/v1/rollcalls",
        headers=student_headers,
    )
    assert student_list.status_code == 200
    student_page = student_list.json()["data"]
    assert student_page["total"] == 1
    assert len(student_page["items"]) == 1
    item = student_page["items"][0]
    assert item["id"] == first_id
    assert item["title"] == "包含学生"
    assert item["total_count"] == 1
    assert item["pending_count"] == 1
    assert "my_status" not in item
    assert "my_checked_at" not in item

    teacher_list = client.get(
        "/api/v1/rollcalls",
        headers=teacher_headers,
    )
    assert teacher_list.json()["data"]["total"] == 2

    detail = client.get(
        f"/api/v1/rollcalls/{second_id}",
        headers=student_headers,
    )
    assert detail.status_code == 404
    assert detail.json()["code"] == 40402


def test_session_list_pagination_and_status_filter(
    client: TestClient,
    db_session: Session,
    teacher_headers: dict[str, str],
) -> None:
    _add_student(db_session, "20230001", "甲")

    first = _start(
        client,
        teacher_headers,
        {"title": "第一场"},
    )
    first_id = first["session"]["id"]
    client.post(
        f"/api/v1/rollcalls/{first_id}/end",
        headers=teacher_headers,
    )

    _start(
        client,
        teacher_headers,
        {"title": "第二场"},
    )

    page = client.get(
        "/api/v1/rollcalls",
        params={"page": 1, "page_size": 1},
        headers=teacher_headers,
    )
    page_data = page.json()["data"]
    assert page_data["total"] == 2
    assert page_data["page"] == 1
    assert page_data["page_size"] == 1
    assert len(page_data["items"]) == 1
    assert page_data["items"][0]["title"] == "第二场"

    ended = client.get(
        "/api/v1/rollcalls",
        params={"status": "ended"},
        headers=teacher_headers,
    )
    ended_data = ended.json()["data"]
    assert ended_data["total"] == 1
    assert ended_data["items"][0]["title"] == "第一场"

    calling = client.get(
        "/api/v1/rollcalls",
        params={"status": "calling"},
        headers=teacher_headers,
    )
    calling_data = calling.json()["data"]
    assert calling_data["total"] == 1
    assert calling_data["items"][0]["title"] == "第二场"


def test_concurrent_checkin_only_one_updates(tmp_path) -> None:
    db_path = (tmp_path / "concurrent.db").as_posix()
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={
            "check_same_thread": False,
            "timeout": 30,
        },
    )
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL")

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        student = Student(
            student_no="20239999",
            name="并发学生",
            role="学生",
            active=True,
        )
        db.add(student)
        db.flush()
        session = RollcallSession(
            title="并发点名",
            status="calling",
            order_by="student_no",
            started_at=datetime.now(timezone.utc),
        )
        db.add(session)
        db.flush()
        db.add(
            AttendanceRecord(
                session_id=session.id,
                student_id=student.id,
                student_no=student.student_no,
                student_name=student.name,
                role=student.role,
                order_no=1,
                status="pending",
            )
        )
        session_id = session.id
        student_id = student.id
        db.commit()

    def worker() -> int:
        with Session(engine) as db:
            updated = record_repo.mark_present(
                db,
                session_id,
                student_id,
                datetime.now(timezone.utc),
            )
            db.commit()
            return updated

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))

    assert sorted(results) == [0, 1]

    with Session(engine) as db:
        record = record_repo.get_record(db, session_id, student_id)
        assert record is not None
        assert record.status == "present"

    engine.dispose()