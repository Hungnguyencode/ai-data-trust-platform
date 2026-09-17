from __future__ import annotations

from typing import Any

import pytest
import requests

import app.services.freshness_api as freshness_api


class FakeResponse:
    def __init__(
        self,
        payload: Any = None,
        *,
        status_code: int = 200,
        status_error: Exception | None = None,
    ):
        self.payload = payload
        self.status_code = status_code
        self.status_error = status_error

    def raise_for_status(
        self,
    ) -> None:
        if self.status_error is not None:
            raise self.status_error

    def json(
        self,
    ) -> Any:
        return self.payload


def test_load_freshness_policy(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_get(
        url: str,
        *,
        timeout: int,
    ):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "freshness_policy_id": 1,
                "catalog_id": 1,
                "max_age_minutes": 60,
                "is_enabled": True,
            }
        )

    monkeypatch.setattr(
        freshness_api.requests,
        "get",
        fake_get,
    )

    result = freshness_api.load_freshness_policy(
        1
    )

    assert result is not None
    assert result["catalog_id"] == 1

    assert captured == {
        "url": (
            f"{freshness_api.FRESHNESS_URL}"
            "/catalog/1/policy"
        ),
        "timeout": 10,
    }


def test_load_freshness_policy_returns_none_for_404(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        freshness_api.requests,
        "get",
        lambda url, timeout: FakeResponse(
            status_code=404,
        ),
    )

    assert (
        freshness_api.load_freshness_policy(1)
        is None
    )


def test_save_freshness_policy(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_put(
        url: str,
        *,
        json: dict[str, Any],
        timeout: int,
    ):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "freshness_policy_id": 1,
                "catalog_id": 1,
                **json,
            }
        )

    monkeypatch.setattr(
        freshness_api.requests,
        "put",
        fake_put,
    )

    result = freshness_api.save_freshness_policy(
        catalog_id=1,
        max_age_minutes=60,
        is_enabled=True,
    )

    assert result["is_enabled"] is True

    assert captured == {
        "url": (
            f"{freshness_api.FRESHNESS_URL}"
            "/catalog/1/policy"
        ),
        "json": {
            "max_age_minutes": 60,
            "is_enabled": True,
        },
        "timeout": 10,
    }


def test_load_freshness_history(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, int],
        timeout: int,
    ):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "catalog_id": 1,
                "count": 0,
                "items": [],
            }
        )

    monkeypatch.setattr(
        freshness_api.requests,
        "get",
        fake_get,
    )

    result = freshness_api.load_freshness_history(
        1,
        limit=25,
    )

    assert result["items"] == []

    assert captured == {
        "url": (
            f"{freshness_api.FRESHNESS_URL}"
            "/catalog/1/history"
        ),
        "params": {
            "limit": 25,
        },
        "timeout": 10,
    }


def test_run_freshness_check(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_post(
        url: str,
        *,
        timeout: int,
    ):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "check": {
                    "freshness_status": "FRESH",
                }
            }
        )

    monkeypatch.setattr(
        freshness_api.requests,
        "post",
        fake_post,
    )

    result = freshness_api.run_freshness_check(
        1
    )

    assert result["check"][
        "freshness_status"
    ] == "FRESH"

    assert captured == {
        "url": (
            f"{freshness_api.FRESHNESS_URL}"
            "/catalog/1/check"
        ),
        "timeout": 15,
    }


def test_freshness_api_wraps_request_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_get(
        url: str,
        *,
        timeout: int,
    ):
        del url
        del timeout

        raise requests.ConnectionError(
            "connection failed"
        )

    monkeypatch.setattr(
        freshness_api.requests,
        "get",
        fail_get,
    )

    with pytest.raises(
        freshness_api.FreshnessApiError,
        match="Unable to load Freshness Policy",
    ):
        freshness_api.load_freshness_policy(1)


def test_freshness_api_rejects_invalid_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        freshness_api.requests,
        "post",
        lambda url, timeout: FakeResponse(
            [
                "invalid",
            ]
        ),
    )

    with pytest.raises(
        freshness_api.FreshnessApiError,
        match="invalid response",
    ):
        freshness_api.run_freshness_check(1)