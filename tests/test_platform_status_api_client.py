import requests

from app.services import platform_status_api


def test_check_database_connection_returns_ready(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "status": "ready",
                "service": "ai-data-trust-api",
                "version": "2.6.0",
                "dependencies": {
                    "sqlserver": "ok",
                },
            }

    def fake_get(url, *, timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        platform_status_api.requests,
        "get",
        fake_get,
    )

    ok, message = (
        platform_status_api.check_database_connection()
    )

    assert (
        captured["url"]
        == platform_status_api.READINESS_URL
    )
    assert captured["timeout"] == 3

    assert ok is True
    assert (
        message
        == "Kết nối SQL Server thành công."
    )


def test_check_database_connection_handles_request_error(
    monkeypatch,
):
    def fake_get(*args, **kwargs):
        raise requests.ConnectionError(
            "internal network detail"
        )

    monkeypatch.setattr(
        platform_status_api.requests,
        "get",
        fake_get,
    )

    ok, message = (
        platform_status_api.check_database_connection()
    )

    assert ok is False
    assert (
        message
        == "Kết nối SQL Server không khả dụng."
    )
    assert "internal network detail" not in message


def test_check_database_connection_returns_unavailable_for_503(
    monkeypatch,
):
    class FakeResponse:
        status_code = 503

        def json(self):
            return {
                "status": "not_ready",
                "service": "ai-data-trust-api",
                "version": "2.6.0",
                "dependencies": {
                    "sqlserver": "unavailable",
                },
            }

    monkeypatch.setattr(
        platform_status_api.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    ok, message = (
        platform_status_api.check_database_connection()
    )

    assert ok is False
    assert (
        message
        == "Kết nối SQL Server không khả dụng."
    )