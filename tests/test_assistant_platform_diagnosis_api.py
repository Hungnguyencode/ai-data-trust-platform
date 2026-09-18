from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.assistant as assistant_route
from api.main import app

client = TestClient(app)


def _fake_context() -> dict:
    return {
        "catalog_id": 1,
        "dataset": {
            "latest_version_id": 3,
            "version_history": [],
            "lineage": {
                "summary": {
                    "lifecycle_state": (
                        "QUARANTINED"
                    ),
                }
            },
        },
        "validation": {
            "latest": {
                "version_id": 2,
                "validation_status": (
                    "ACCEPTED"
                ),
            },
            "latest_version": {
                "version_id": 3,
                "validation_status": (
                    "REJECTED"
                ),
            },
            "history": [],
        },
        "governance": {
            "latest": {
                "version_id": 2,
                "decision": "REJECTED",
            },
            "latest_version": {
                "version_id": 3,
                "decision": "REJECTED",
            },
            "history": [],
        },
        "observability": {
            "freshness": {
                "latest": {
                    "freshness_status": (
                        "STALE"
                    ),
                },
                "history": [],
            },
            "volume": {
                "latest": {
                    "volume_status": (
                        "NORMAL"
                    ),
                },
                "history": [],
            },
        },
        "operations": {
            "pipeline_runs": [
                {
                    "pipeline_run_id": 20002,
                    "run_status": "SUCCESS",
                }
            ],
            "operational_events": [],
        },
    }


def test_diagnosis_endpoint_returns_reasoning(
    monkeypatch,
):
    monkeypatch.setattr(
        assistant_route,
        "build_platform_context",
        lambda catalog_id: _fake_context(),
    )

    response = client.get(
        "/api/assistant/catalog/1/diagnosis"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["catalog_id"] == 1
    assert payload["grounded"] is True
    assert payload["version"] == "2.6"
    assert payload["latest_version_id"] == 3

    assert (
        payload["overall_state"]
        == "ACTION_REQUIRED"
    )

    codes = {
        finding["code"]
        for finding in payload["findings"]
    }

    assert "VALIDATION_REJECTED" in codes
    assert "GOVERNANCE_REJECTED" in codes
    assert "LIFECYCLE_QUARANTINED" in codes
    assert "FRESHNESS_STALE" in codes
    assert "VOLUME_NORMAL" in codes
    assert "PIPELINE_SUCCESS" in codes


def test_diagnosis_endpoint_returns_400(
    monkeypatch,
):
    def fail_context(catalog_id):
        raise ValueError("bad context")

    monkeypatch.setattr(
        assistant_route,
        "build_platform_context",
        fail_context,
    )

    response = client.get(
        "/api/assistant/catalog/1/diagnosis"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "bad context"
    )


def test_diagnosis_endpoint_returns_500(
    monkeypatch,
):
    def fail_context(catalog_id):
        raise RuntimeError("database failure")

    monkeypatch.setattr(
        assistant_route,
        "build_platform_context",
        fail_context,
    )

    response = client.get(
        "/api/assistant/catalog/1/diagnosis"
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Unable to build assistant "
        "platform diagnosis."
    )