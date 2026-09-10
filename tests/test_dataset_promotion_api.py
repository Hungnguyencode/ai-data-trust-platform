from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.datasets as datasets_route
from api.main import app

client = TestClient(app)


def lineage_summary(
    *,
    state: str,
) -> dict:
    return {
        "summary": {
            "catalog_id": 1,
            "version_id": 6,
            "version_number": 6,
            "lifecycle_state": state,
            "latest_governance_decision": (
                "APPROVED"
            ),
        },
        "version": {},
        "ingestions": [],
        "validations": [],
        "governance_decisions": [],
        "lifecycle_events": [],
        "timeline": [],
    }


def test_promote_dataset_version_success(
    monkeypatch,
):
    calls = {
        "lineage": 0,
        "promote": [],
    }

    def fake_get_version_lineage(
        version_id: int,
    ):
        assert version_id == 6

        calls["lineage"] += 1

        if calls["lineage"] == 1:
            return lineage_summary(
                state="VALIDATED"
            )

        return lineage_summary(
            state="ACTIVE"
        )

    def fake_promote_version(
        *,
        catalog_id: int,
        version_id: int,
    ):
        calls["promote"].append(
            (
                catalog_id,
                version_id,
            )
        )

        return {
            "catalog_id": catalog_id,
            "version_id": version_id,
            "lifecycle_state": "ACTIVE",
            "changed": True,
        }

    monkeypatch.setattr(
        datasets_route,
        "get_version_lineage",
        fake_get_version_lineage,
    )

    monkeypatch.setattr(
        datasets_route,
        "promote_version",
        fake_promote_version,
    )

    response = client.post(
        "/api/datasets/6/promote"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload == {
        "version_id": 6,
        "catalog_id": 1,
        "previous_state": "VALIDATED",
        "lifecycle_state": "ACTIVE",
        "changed": True,
        "governance_decision": "APPROVED",
        "message": (
            "Dataset version promoted "
            "to ACTIVE successfully."
        ),
    }

    assert calls["promote"] == [
        (1, 6)
    ]


def test_promote_dataset_version_already_active_is_idempotent(
    monkeypatch,
):
    def fake_get_version_lineage(
        version_id: int,
    ):
        return lineage_summary(
            state="ACTIVE"
        )

    def fake_promote_version(
        *,
        catalog_id: int,
        version_id: int,
    ):
        return {
            "catalog_id": catalog_id,
            "version_id": version_id,
            "lifecycle_state": "ACTIVE",
            "changed": False,
        }

    monkeypatch.setattr(
        datasets_route,
        "get_version_lineage",
        fake_get_version_lineage,
    )

    monkeypatch.setattr(
        datasets_route,
        "promote_version",
        fake_promote_version,
    )

    response = client.post(
        "/api/datasets/6/promote"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["previous_state"] == "ACTIVE"
    assert payload["lifecycle_state"] == "ACTIVE"
    assert payload["changed"] is False

    assert payload["message"] == (
        "Dataset version is already ACTIVE; "
        "no changes were applied."
    )


def test_promote_dataset_version_not_found(
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

    response = client.post(
        "/api/datasets/999/promote"
    )

    assert response.status_code == 404


def test_promote_dataset_version_blocked(
    monkeypatch,
):
    def fake_get_version_lineage(
        version_id: int,
    ):
        return lineage_summary(
            state="VALIDATED"
        )

    def fake_promote_version(
        *,
        catalog_id: int,
        version_id: int,
    ):
        raise ValueError(
            "Dataset version is not "
            "governance-approved for promotion."
        )

    monkeypatch.setattr(
        datasets_route,
        "get_version_lineage",
        fake_get_version_lineage,
    )

    monkeypatch.setattr(
        datasets_route,
        "promote_version",
        fake_promote_version,
    )

    response = client.post(
        "/api/datasets/6/promote"
    )

    assert response.status_code == 409

    assert (
        "governance-approved"
        in response.json()["detail"]
    )


def test_promote_dataset_version_internal_error(
    monkeypatch,
):
    def fake_get_version_lineage(
        version_id: int,
    ):
        return lineage_summary(
            state="VALIDATED"
        )

    def fake_promote_version(
        *,
        catalog_id: int,
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

    monkeypatch.setattr(
        datasets_route,
        "promote_version",
        fake_promote_version,
    )

    response = client.post(
        "/api/datasets/6/promote"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": (
            "Unable to promote "
            "dataset version."
        )
    }


def test_promote_dataset_version_rejects_invalid_id():
    response = client.post(
        "/api/datasets/0/promote"
    )

    assert response.status_code == 422