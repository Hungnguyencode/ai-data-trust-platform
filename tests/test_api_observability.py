from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from api import main as api_main
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


def test_readiness_returns_ready_when_database_is_available(monkeypatch):
    monkeypatch.setattr(
        api_main,
        "test_connection",
        lambda: (True, "SQL Server connection successful."),
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "ai-data-trust-api",
        "version": "2.6.0",
        "dependencies": {
            "sqlserver": "ok",
        },
    }


def test_readiness_returns_503_when_database_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        api_main,
        "test_connection",
        lambda: (False, "SQL Server unavailable."),
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "ai-data-trust-api",
        "version": "2.6.0",
        "dependencies": {
            "sqlserver": "unavailable",
        },
    }