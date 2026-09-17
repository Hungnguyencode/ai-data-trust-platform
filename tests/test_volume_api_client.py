from __future__ import annotations

from typing import Any

import pytest
import requests

import app.services.volume_api as volume_api


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


def test_load_volume_policy(
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
                "volume_policy_id": 1,
                "catalog_id": 1,
                "drop_threshold_pct": 20.0,
                "spike_threshold_pct": 10.0,
                "is_enabled": True,
            }
        )

    monkeypatch.setattr(
        volume_api.requests,
        "get",
        fake_get,
    )

    result = volume_api.load_volume_policy(
        1
    )

    assert result is not None
    assert result["catalog_id"] == 1

    assert captured == {
        "url": (
            f"{volume_api.VOLUME_URL}"
            "/catalog/1/policy"
        ),
        "timeout": 10,
    }


def test_load_volume_policy_returns_none_for_404(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        volume_api.requests,
        "get",
        lambda url, timeout: FakeResponse(
            status_code=404,
        ),
    )

    assert (
        volume_api.load_volume_policy(1)
        is None
    )


def test_save_volume_policy(
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
                "volume_policy_id": 1,
                "catalog_id": 1,
                **json,
            }
        )

    monkeypatch.setattr(
        volume_api.requests,
        "put",
        fake_put,
    )

    result = volume_api.save_volume_policy(
        catalog_id=1,
        drop_threshold_pct=20.0,
        spike_threshold_pct=10.0,
        is_enabled=True,
    )

    assert result["is_enabled"] is True

    assert captured == {
        "url": (
            f"{volume_api.VOLUME_URL}"
            "/catalog/1/policy"
        ),
        "json": {
            "drop_threshold_pct": 20.0,
            "spike_threshold_pct": 10.0,
            "is_enabled": True,
        },
        "timeout": 10,
    }


def test_load_volume_history(
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
        volume_api.requests,
        "get",
        fake_get,
    )

    result = volume_api.load_volume_history(
        1,
        limit=25,
    )

    assert result["items"] == []

    assert captured == {
        "url": (
            f"{volume_api.VOLUME_URL}"
            "/catalog/1/history"
        ),
        "params": {
            "limit": 25,
        },
        "timeout": 10,
    }


def test_run_volume_check(
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
                    "volume_status": "NORMAL",
                }
            }
        )

    monkeypatch.setattr(
        volume_api.requests,
        "post",
        fake_post,
    )

    result = volume_api.run_volume_check(
        1
    )

    assert result["check"][
        "volume_status"
    ] == "NORMAL"

    assert captured == {
        "url": (
            f"{volume_api.VOLUME_URL}"
            "/catalog/1/check"
        ),
        "timeout": 15,
    }


def test_volume_api_wraps_request_error(
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
        volume_api.requests,
        "get",
        fail_get,
    )

    with pytest.raises(
        volume_api.VolumeApiError,
        match="Unable to load Volume Policy",
    ):
        volume_api.load_volume_policy(1)


def test_volume_api_rejects_invalid_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        volume_api.requests,
        "post",
        lambda url, timeout: FakeResponse(
            [
                "invalid",
            ]
        ),
    )

    with pytest.raises(
        volume_api.VolumeApiError,
        match="invalid response",
    ):
        volume_api.run_volume_check(1)