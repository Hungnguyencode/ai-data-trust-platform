from __future__ import annotations

from uuid import UUID

from fastapi import Request
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


def test_metrics_use_full_included_router_path():
    response = client.get(
        "/api/assistant/status"
    )

    assert response.status_code == 200

    metrics_response = client.get(
        "/metrics"
    )

    assert metrics_response.status_code == 200
    assert (
        'path="/api/assistant/status"'
        in metrics_response.text
    )


def test_resolve_metric_path_keeps_dynamic_route_template():
    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/api/scans/123",
            "raw_path": b"/api/scans/123",
            "query_string": b"",
            "headers": [],
            "client": (
                "testclient",
                50000,
            ),
            "server": (
                "testserver",
                80,
            ),
            "root_path": "",
            "app": app,
        }
    )

    assert (
        api_main.resolve_metric_path(
            request
        )
        == "/api/scans/{scan_id}"
    )