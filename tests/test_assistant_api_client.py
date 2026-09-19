from __future__ import annotations

from typing import Any

import pytest
import requests

import app.services.assistant_api as assistant_api


class FakeResponse:
    def __init__(
        self,
        payload: Any = None,
        *,
        status_error: Exception | None = None,
        json_error: Exception | None = None,
    ):
        self.payload = payload
        self.status_error = status_error
        self.json_error = json_error

    def raise_for_status(
        self,
    ) -> None:
        if self.status_error is not None:
            raise self.status_error

    def json(
        self,
    ) -> Any:
        if self.json_error is not None:
            raise self.json_error

        return self.payload


def test_ask_catalog_copilot(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_post(
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
                "catalog_id": 1,
                "grounded": True,
                "version": "2.6",
                "latest_version_id": 6,
                "overall_state": "HEALTHY",
                "answer": (
                    "Current platform evidence "
                    "does not show a blocking issue."
                ),
                "source_finding_codes": [
                    "VALIDATION_ACCEPTED",
                ],
                "source_action_codes": [],
                "provider": "disabled",
                "model": None,
                "used_llm": False,
                "fallback_reason": (
                    "provider_disabled"
                ),
                "error_type": None,
            }
        )

    monkeypatch.setattr(
        assistant_api.requests,
        "post",
        fake_post,
    )

    result = assistant_api.ask_catalog_copilot(
        catalog_id=1,
        question="What should I fix first?",
    )

    assert result["catalog_id"] == 1
    assert result["grounded"] is True

    assert (
        result["overall_state"]
        == "HEALTHY"
    )

    assert (
        result["fallback_reason"]
        == "provider_disabled"
    )

    assert captured == {
        "url": (
            f"{assistant_api.ASSISTANT_URL}"
            "/catalog/1/copilot"
        ),
        "json": {
            "question": (
                "What should I fix first?"
            ),
        },
        "timeout": 120,
    }


def test_ask_catalog_copilot_wraps_request_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_post(
        url: str,
        *,
        json: dict[str, Any],
        timeout: int,
    ):
        del url
        del json
        del timeout

        raise requests.ConnectionError(
            "connection failed"
        )

    monkeypatch.setattr(
        assistant_api.requests,
        "post",
        fail_post,
    )

    with pytest.raises(
        assistant_api.AssistantApiError,
        match=(
            "Unable to answer "
            "Copilot question"
        ),
    ):
        assistant_api.ask_catalog_copilot(
            catalog_id=1,
            question="What is wrong?",
        )


def test_ask_catalog_copilot_rejects_invalid_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        assistant_api.requests,
        "post",
        lambda url, json, timeout: FakeResponse(
            [
                "invalid",
            ]
        ),
    )

    with pytest.raises(
        assistant_api.AssistantApiError,
        match="invalid response",
    ):
        assistant_api.ask_catalog_copilot(
            catalog_id=1,
            question="What is wrong?",
        )


def test_ask_catalog_copilot_rejects_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        assistant_api.requests,
        "post",
        lambda url, json, timeout: FakeResponse(
            json_error=ValueError(
                "invalid json"
            )
        ),
    )

    with pytest.raises(
        assistant_api.AssistantApiError,
        match="returned invalid JSON",
    ):
        assistant_api.ask_catalog_copilot(
            catalog_id=1,
            question="What is wrong?",
        )