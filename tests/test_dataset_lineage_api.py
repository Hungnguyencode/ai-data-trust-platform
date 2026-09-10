from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.datasets as datasets_route
from api.main import app

client = TestClient(app)


def build_lineage_response() -> dict:
    return {
        "summary": {
            "catalog_id": 1,
            "version_id": 5,
            "version_number": 5,
            "lifecycle_state": "ACTIVE",
            "ingestion_count": 1,
            "validation_count": 1,
            "governance_count": 1,
            "lifecycle_event_count": 2,
            "latest_validation_status": (
                "ACCEPTED"
            ),
            "latest_governance_decision": (
                "APPROVED"
            ),
            "latest_trust_score": 92.5,
            "latest_privacy_status": "LOW",
            "lifecycle_eligible": False,
            "governance_approved": True,
            "promotion_eligible": False,
            "is_active": True,
        },
        "version": {
            "catalog_id": 1,
            "version_id": 5,
            "version_number": 5,
            "file_name": (
                "sample_customers.csv"
            ),
            "lifecycle_state": "ACTIVE",
        },
        "ingestions": [],
        "validations": [],
        "governance_decisions": [],
        "lifecycle_events": [],
        "timeline": [],
    }


def test_get_dataset_lineage_success(
    monkeypatch,
):
    expected = build_lineage_response()

    def fake_get_version_lineage(
        version_id: int,
    ):
        assert version_id == 5
        return expected

    monkeypatch.setattr(
        datasets_route,
        "get_version_lineage",
        fake_get_version_lineage,
    )

    response = client.get(
        "/api/datasets/5/lineage"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["summary"]["version_id"]
        == 5
    )

    assert (
        payload["summary"][
            "latest_governance_decision"
        ]
        == "APPROVED"
    )

    assert (
        payload["summary"][
            "promotion_eligible"
        ]
        is False
    )


def test_get_dataset_lineage_not_found(
    monkeypatch,
):
    def fake_get_version_lineage(
        version_id: int,
    ):
        raise ValueError(
            "Không tìm thấy dataset version "
            f"version_id={version_id}."
        )

    monkeypatch.setattr(
        datasets_route,
        "get_version_lineage",
        fake_get_version_lineage,
    )

    response = client.get(
        "/api/datasets/999/lineage"
    )

    assert response.status_code == 404

    assert (
        "version_id=999"
        in response.json()["detail"]
    )


def test_get_dataset_lineage_internal_error(
    monkeypatch,
):
    def fake_get_version_lineage(
        version_id: int,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        datasets_route,
        "get_version_lineage",
        fake_get_version_lineage,
    )

    response = client.get(
        "/api/datasets/5/lineage"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": (
            "Unable to load "
            "dataset lineage."
        )
    }


def test_get_dataset_lineage_rejects_invalid_id():
    response = client.get(
        "/api/datasets/0/lineage"
    )

    assert response.status_code == 422