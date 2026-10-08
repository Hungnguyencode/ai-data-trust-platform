from __future__ import annotations

from typing import Any

import pytest
import requests

import app.services.pipeline_operations_api as pipeline_operations_api


class FakeResponse:
    def __init__(
        self,
        payload: Any,
    ):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self.payload


def test_load_pipeline_runs_uses_pipeline_runs_api(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, int],
        timeout: int,
    ) -> FakeResponse:
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "count": 1,
                "items": [
                    {
                        "pipeline_run_id": 7,
                        "run_status": "SUCCESS",
                    }
                ],
            }
        )

    monkeypatch.setattr(
        pipeline_operations_api.requests,
        "get",
        fake_get,
    )

    result = pipeline_operations_api.load_pipeline_runs(
        limit=25,
    )

    assert result == [
        {
            "pipeline_run_id": 7,
            "run_status": "SUCCESS",
        }
    ]

    assert captured == {
        "url": pipeline_operations_api.PIPELINE_RUNS_URL,
        "params": {
            "limit": 25,
        },
        "timeout": 10,
    }


def test_load_pipeline_run_uses_pipeline_run_detail_api(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_get(
        url: str,
        *,
        timeout: int,
    ) -> FakeResponse:
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "pipeline_run_id": 7,
                "run_status": "FAILED",
            }
        )

    monkeypatch.setattr(
        pipeline_operations_api.requests,
        "get",
        fake_get,
    )

    result = pipeline_operations_api.load_pipeline_run(
        7,
    )

    assert result == {
        "pipeline_run_id": 7,
        "run_status": "FAILED",
    }

    assert captured == {
        "url": (
            f"{pipeline_operations_api.PIPELINE_RUNS_URL}/7"
        ),
        "timeout": 10,
    }


def test_load_operational_events_uses_operational_events_api(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, int],
        timeout: int,
    ) -> FakeResponse:
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "count": 1,
                "items": [
                    {
                        "operational_event_id": 11,
                        "severity": "ERROR",
                    }
                ],
            }
        )

    monkeypatch.setattr(
        pipeline_operations_api.requests,
        "get",
        fake_get,
    )

    result = (
        pipeline_operations_api.load_operational_events(
            limit=50,
        )
    )

    assert result == [
        {
            "operational_event_id": 11,
            "severity": "ERROR",
        }
    ]

    assert captured == {
        "url": (
            pipeline_operations_api
            .OPERATIONAL_EVENTS_URL
        ),
        "params": {
            "limit": 50,
        },
        "timeout": 10,
    }


def test_pipeline_operations_api_wraps_request_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_get(
        url: str,
        *,
        params: dict[str, int],
        timeout: int,
    ) -> FakeResponse:
        del url
        del params
        del timeout

        raise requests.ConnectionError(
            "connection failed"
        )

    monkeypatch.setattr(
        pipeline_operations_api.requests,
        "get",
        fail_get,
    )

    with pytest.raises(
        pipeline_operations_api.PipelineOperationsApiError,
        match="Unable to load Pipeline Runs",
    ):
        pipeline_operations_api.load_pipeline_runs(
            limit=25,
        )


def test_load_pipeline_run_wraps_request_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_get(
        url: str,
        *,
        timeout: int,
    ) -> FakeResponse:
        del url
        del timeout

        raise requests.ConnectionError(
            "connection failed"
        )

    monkeypatch.setattr(
        pipeline_operations_api.requests,
        "get",
        fail_get,
    )

    with pytest.raises(
        pipeline_operations_api.PipelineOperationsApiError,
        match="Unable to load Pipeline Run",
    ):
        pipeline_operations_api.load_pipeline_run(
            7,
        )


def test_load_operational_events_wraps_request_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_get(
        url: str,
        *,
        params: dict[str, int],
        timeout: int,
    ) -> FakeResponse:
        del url
        del params
        del timeout

        raise requests.ConnectionError(
            "connection failed"
        )

    monkeypatch.setattr(
        pipeline_operations_api.requests,
        "get",
        fail_get,
    )

    with pytest.raises(
        pipeline_operations_api.PipelineOperationsApiError,
        match="Unable to load Operational Events",
    ):
        pipeline_operations_api.load_operational_events(
            limit=50,
        )