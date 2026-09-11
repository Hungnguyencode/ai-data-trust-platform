from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_request_id_is_preserved_when_provided() -> None:
    request_id = "observability-test-001"

    response = client.get(
        "/api/info",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_request_id_is_generated_when_missing() -> None:
    response = client.get("/api/info")

    assert response.status_code == 200

    request_id = response.headers["X-Request-ID"]

    assert request_id
    assert str(UUID(request_id)) == request_id