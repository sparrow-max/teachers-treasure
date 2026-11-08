from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.main import create_app


class SamplePayload(BaseModel):
    name: str


def test_validation_error_returns_unified_envelope() -> None:
    application = create_app()

    @application.post("/api/v1/_test/validate")
    def validate(payload: SamplePayload) -> dict[str, bool]:
        return {"accepted": True}

    with TestClient(application) as client:
        response = client.post("/api/v1/_test/validate", json={})

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == 40001
    assert body["data"] is None
    assert "name" in body["message"]