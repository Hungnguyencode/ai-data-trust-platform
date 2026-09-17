from __future__ import annotations

from typing import Any

import pytest
import requests

import app.services.observability_api as observability_api


class FakeResponse:
    def __init__(
        self,
        payload: Any,
        *,
        status_error: Exception | None = None,
    ):
        self.payload = payload
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


def test_load_observability_overview(
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
                "summary": {
                    "monitored_dataset_count": 1,
                },
                "datasets": [],
            }
        )

    monkeypatch.setattr(
        observability_api.requests,
        "get",
        fake_get,
    )

    result = (
        observability_api
        .load_observability_overview(
            event_limit=25,
            run_limit=30,
        )
    )

    assert result["summary"][
        "monitored_dataset_count"
    ] == 1

    assert captured == {
        "url": (
            f"{observability_api.OBSERVABILITY_URL}"
            "/overview"
        ),
        "params": {
            "event_limit": 25,
            "run_limit": 30,
        },
        "timeout": 15,
    }


def test_load_observability_overview_http_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fake_get(
        url: str,
        *,
        params: dict[str, int],
        timeout: int,
    ):
        del url
        del params
        del timeout

        raise requests.ConnectionError(
            "connection failed"
        )

    monkeypatch.setattr(
        observability_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        observability_api.ObservabilityApiError,
        match=(
            "Unable to load "
            "Observability Overview API"
        ),
    ):
        observability_api.load_observability_overview()


def test_load_observability_overview_invalid_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    def fake_get(
        url: str,
        *,
        params: dict[str, int],
        timeout: int,
    ):
        del url
        del params
        del timeout

        return FakeResponse(
            [
                "invalid",
            ]
        )

    monkeypatch.setattr(
        observability_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        observability_api.ObservabilityApiError,
        match="invalid response",
    ):
        observability_api.load_observability_overview()