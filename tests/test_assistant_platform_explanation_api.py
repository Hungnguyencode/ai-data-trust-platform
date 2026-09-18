from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.assistant as assistant_route
from api.main import app

client = TestClient(app)


def test_explanation_endpoint_chains_layers(
    monkeypatch,
):
    context = {
        "catalog_id": 1,
        "source": "context",
    }

    diagnosis = {
        "catalog_id": 1,
        "source": "diagnosis",
    }

    explanation = {
        "catalog_id": 1,
        "latest_version_id": 3,
        "overall_state": (
            "ACTION_REQUIRED"
        ),
        "headline": (
            "Action is required before "
            "trusted downstream use."
        ),
        "summary": (
            "Dataset version 3 "
            "requires action."
        ),
        "explanation": (
            "### Platform diagnosis\n\n"
            "Action is required."
        ),
        "source_finding_codes": [
            "VALIDATION_REJECTED",
            "FRESHNESS_STALE",
        ],
        "source_action_codes": [
            "REMEDIATE_VALIDATION",
        ],
    }

    def fake_context(
        catalog_id,
    ):
        assert catalog_id == 1
        return context

    def fake_reasoning(
        received_context,
    ):
        assert received_context is context
        return diagnosis

    def fake_explanation(
        received_diagnosis,
    ):
        assert received_diagnosis is diagnosis
        return explanation

    monkeypatch.setattr(
        assistant_route,
        "build_platform_context",
        fake_context,
    )

    monkeypatch.setattr(
        assistant_route,
        "reason_about_platform_context",
        fake_reasoning,
    )

    monkeypatch.setattr(
        assistant_route,
        "explain_platform_diagnosis",
        fake_explanation,
    )

    response = client.get(
        "/api/assistant/catalog/1/explanation"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["catalog_id"] == 1

    assert (
        payload["latest_version_id"]
        == 3
    )

    assert (
        payload["overall_state"]
        == "ACTION_REQUIRED"
    )

    assert payload["grounded"] is True
    assert payload["version"] == "2.6"

    assert payload[
        "source_finding_codes"
    ] == [
        "VALIDATION_REJECTED",
        "FRESHNESS_STALE",
    ]

    assert payload[
        "source_action_codes"
    ] == [
        "REMEDIATE_VALIDATION",
    ]


def test_explanation_endpoint_returns_400(
    monkeypatch,
):
    def fail_context(
        catalog_id,
    ):
        raise ValueError(
            "bad platform context"
        )

    monkeypatch.setattr(
        assistant_route,
        "build_platform_context",
        fail_context,
    )

    response = client.get(
        "/api/assistant/catalog/1/explanation"
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "bad platform context"
    )


def test_explanation_endpoint_returns_500(
    monkeypatch,
):
    def fail_context(
        catalog_id,
    ):
        raise RuntimeError(
            "database failure"
        )

    monkeypatch.setattr(
        assistant_route,
        "build_platform_context",
        fail_context,
    )

    response = client.get(
        "/api/assistant/catalog/1/explanation"
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Unable to build assistant "
        "platform explanation."
    )