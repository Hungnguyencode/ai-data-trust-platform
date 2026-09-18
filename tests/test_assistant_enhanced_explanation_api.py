from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_enhanced_explanation_endpoint(
    monkeypatch,
):
    context = {
        "catalog_id": 1,
    }

    diagnosis = {
        "catalog_id": 1,
        "overall_state": (
            "ACTION_REQUIRED"
        ),
    }

    explanation = {
        "catalog_id": 1,
        "latest_version_id": 3,
        "overall_state": (
            "ACTION_REQUIRED"
        ),
        "headline": (
            "Dataset requires remediation."
        ),
        "summary": (
            "Validation and governance "
            "controls rejected the dataset."
        ),
        "explanation": (
            "Deterministic explanation."
        ),
        "source_finding_codes": [
            "VALIDATION_REJECTED",
        ],
        "source_action_codes": [
            "REMEDIATE_VALIDATION",
        ],
    }

    enhanced = {
        **explanation,
        "enhanced_explanation": (
            "Polished grounded explanation."
        ),
        "provider": "gemini",
        "model": "gemini-test-model",
        "used_llm": True,
        "fallback_reason": None,
        "error_type": None,
    }

    monkeypatch.setattr(
        "api.routes.assistant.build_platform_context",
        lambda catalog_id: context,
    )

    monkeypatch.setattr(
        (
            "api.routes.assistant."
            "reason_about_platform_context"
        ),
        lambda value: diagnosis,
    )

    monkeypatch.setattr(
        (
            "api.routes.assistant."
            "explain_platform_diagnosis"
        ),
        lambda value: explanation,
    )

    monkeypatch.setattr(
        (
            "api.routes.assistant."
            "enhance_platform_explanation"
        ),
        lambda value: enhanced,
    )

    response = client.get(
        (
            "/api/assistant/catalog/"
            "1/enhanced-explanation"
        )
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["overall_state"]
        == "ACTION_REQUIRED"
    )

    assert (
        body["explanation"]
        == "Deterministic explanation."
    )

    assert (
        body["enhanced_explanation"]
        == "Polished grounded explanation."
    )

    assert body["used_llm"] is True

    assert (
        body["provider"]
        == "gemini"
    )

    assert (
        body["source_finding_codes"]
        == ["VALIDATION_REJECTED"]
    )

    assert (
        body["source_action_codes"]
        == ["REMEDIATE_VALIDATION"]
    )


def test_enhanced_explanation_endpoint_fallback(
    monkeypatch,
):
    explanation = {
        "catalog_id": 1,
        "latest_version_id": 3,
        "overall_state": (
            "ACTION_REQUIRED"
        ),
        "headline": (
            "Dataset requires remediation."
        ),
        "summary": (
            "Dataset requires remediation."
        ),
        "explanation": (
            "Deterministic explanation."
        ),
        "source_finding_codes": [],
        "source_action_codes": [],
    }

    enhanced = {
        **explanation,
        "enhanced_explanation": (
            explanation["explanation"]
        ),
        "provider": "disabled",
        "model": None,
        "used_llm": False,
        "fallback_reason": (
            "provider_disabled"
        ),
        "error_type": None,
    }

    monkeypatch.setattr(
        "api.routes.assistant.build_platform_context",
        lambda catalog_id: {},
    )

    monkeypatch.setattr(
        (
            "api.routes.assistant."
            "reason_about_platform_context"
        ),
        lambda value: {},
    )

    monkeypatch.setattr(
        (
            "api.routes.assistant."
            "explain_platform_diagnosis"
        ),
        lambda value: explanation,
    )

    monkeypatch.setattr(
        (
            "api.routes.assistant."
            "enhance_platform_explanation"
        ),
        lambda value: enhanced,
    )

    response = client.get(
        (
            "/api/assistant/catalog/"
            "1/enhanced-explanation"
        )
    )

    assert response.status_code == 200

    body = response.json()

    assert body["used_llm"] is False

    assert (
        body["fallback_reason"]
        == "provider_disabled"
    )

    assert (
        body["enhanced_explanation"]
        == body["explanation"]
    )