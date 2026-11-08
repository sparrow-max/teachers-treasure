from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.security import hash_password
from app.main import create_app
from app.models import Base, Classroom, Student, User


@event.listens_for(Session, "before_flush")
def _assign_default_class(session, _context, _instances) -> None:
    for instance in session.new:
        if isinstance(instance, Student) and instance.class_id is None:
            instance.class_id = 1


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    with testing_session() as session:
        classroom = Classroom(id=1, name="测试班", code="C-001")
        session.add(classroom)
        session.commit()
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    application = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as test_client:
        original_post = test_client.post

        def post(url: str, **kwargs):
            payload = kwargs.get("json")
            if isinstance(payload, dict):
                if url.endswith("/students") or url.endswith("/rollcalls"):
                    payload = dict(payload)
                    payload.setdefault("class_id", 1)
                    kwargs["json"] = payload
            return original_post(url, **kwargs)

        test_client.post = post  # type: ignore[method-assign]
        yield test_client
    application.dependency_overrides.clear()

def _login_headers(
    client: TestClient,
    username: str,
    password: str,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def teacher_user(db_session: Session) -> User:
    user = User(
        username="teacher",
        password_hash=hash_password("Teacher123"),
        role="teacher",
        display_name="教师",
        student_id=None,
        must_change_password=False,
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def teacher_headers(
    client: TestClient,
    teacher_user: User,
) -> dict[str, str]:
    return _login_headers(client, "teacher", "Teacher123")


@pytest.fixture()
def monitor_user(db_session: Session) -> User:
    student = Student(
        student_no="20230001",
        name="班长甲",
        role="班长",
        active=True,
    )
    db_session.add(student)
    db_session.flush()

    user = User(
        username="20230001",
        password_hash=hash_password("Monitor123"),
        role="monitor",
        display_name="班长甲",
        student_id=student.id,
        must_change_password=False,
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def monitor_headers(
    client: TestClient,
    monitor_user: User,
) -> dict[str, str]:
    return _login_headers(client, "20230001", "Monitor123")


@pytest.fixture()
def student_user(db_session: Session) -> User:
    student = Student(
        student_no="20230002",
        name="学生乙",
        role="学生",
        active=True,
    )
    db_session.add(student)
    db_session.flush()

    user = User(
        username="20230002",
        password_hash=hash_password("Student123"),
        role="student",
        display_name="学生乙",
        student_id=student.id,
        must_change_password=False,
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def student_headers(
    client: TestClient,
    student_user: User,
) -> dict[str, str]:
    return _login_headers(client, "20230002", "Student123")