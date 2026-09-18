from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.assistant as assistant_route
from api.main import app

client = TestClient(app)


def test_get_catalog_assistant_context(
    monkeypatch,
):
    def fake_build_platform_context(
        catalog_id: int,
    ):
        return {
            "catalog_id": catalog_id,
            "dataset": {
                "latest_version_id": 3,
            },
            "data_contract": {
                "active": {
                    "contract_id": 10,
                },
            },
            "validation": {
                "latest": {
                    "status": "ACCEPTED",
                },
            },
            "governance": {
                "latest": {
                    "decision": "APPROVED",
                },
            },
            "observability": {
                "freshness": {
                    "latest": {
                        "freshness_status": (
                            "STALE"
                        ),
                    },
                },
                "volume": {
                    "latest": {
                        "volume_status": (
                            "NORMAL"
                        ),
                    },
                },
            },
            "operations": {
                "pipeline_runs": [],
                "operational_events": [],
            },
            "evidence_summary": {
                "version_count": 3,
                "has_active_contract": True,
                "validation_count": 1,
                "governance_count": 1,
                "freshness_check_count": 1,
                "volume_check_count": 1,
                "pipeline_run_count": 0,
                "operational_event_count": 0,
                "has_lineage": True,
            },
        }

    monkeypatch.setattr(
        assistant_route,
        "build_platform_context",
        fake_build_platform_context,
    )

    response = client.get(
        "/api/assistant/catalog/1/context"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["catalog_id"] == 1
    assert payload["grounded"] is True
    assert payload["version"] == "2.6"

    assert (
        payload["context"]["dataset"][
            "latest_version_id"
        ]
        == 3
    )

    assert (
        payload["context"]["observability"][
            "freshness"
        ]["latest"]["freshness_status"]
        == "STALE"
    )

    assert (
        payload["evidence_summary"][
            "has_active_contract"
        ]
        is True
    )

    assert (
        payload["evidence_summary"][
            "has_lineage"
        ]
        is True
    )


def test_get_catalog_assistant_context_rejects_invalid_catalog_id():
    response = client.get(
        "/api/assistant/catalog/0/context"
    )

    assert response.status_code == 422


def test_get_catalog_assistant_context_handles_builder_failure(
    monkeypatch,
):
    def fail_build_platform_context(
        catalog_id: int,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        assistant_route,
        "build_platform_context",
        fail_build_platform_context,
    )

    response = client.get(
        "/api/assistant/catalog/1/context"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": (
            "Unable to build assistant "
            "platform context."
        )
    }