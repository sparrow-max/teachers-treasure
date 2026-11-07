from fastapi.testclient import TestClient


def test_health_returns_unified_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {"status": "ok", "version": "1.1.0"},
    }
    assert response.headers.get("X-Request-ID")


def test_health_keeps_incoming_request_id(client: TestClient) -> None:
    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "test-request-id"},
    )

    assert response.headers["X-Request-ID"] == "test-request-id"