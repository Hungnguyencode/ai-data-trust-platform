from __future__ import annotations

from fastapi.testclient import TestClient

import api.routes.workflows as workflow_route
from api.main import app
from src.workflows import DatasetWorkflowError

client = TestClient(app)


class FakeWorkflowResult:
    def __init__(
        self,
        summary: dict,
    ) -> None:
        self._summary = summary

    def summary(
        self,
    ) -> dict:
        return dict(
            self._summary
        )


def build_summary(
    *,
    validation_status: str = "ACCEPTED",
    governance_decision: str = "APPROVED",
    lifecycle_state: str = "VALIDATED",
    promotion_eligible: bool = True,
) -> dict:
    return {
        "ingestion_id": "ingestion-123",
        "catalog_id": 1,
        "version_id": 7,
        "version_number": 3,
        "validation_id": 9,
        "validation_status": validation_status,
        "governance_id": 4,
        "governance_decision": governance_decision,
        "trust_score": 94.5,
        "privacy_status": "LOW",
        "lifecycle_state": lifecycle_state,
        "promotion_eligible": promotion_eligible,
    }


def test_run_dataset_workflow_api_success(
    monkeypatch,
):
    def fake_run_dataset_workflow(
        source,
        *,
        persist_raw: bool,
    ):
        assert source.name == "customers.csv"

        assert (
            source.getvalue()
            == b"customer_id,age\n1,25\n2,30\n"
        )

        assert persist_raw is True

        return FakeWorkflowResult(
            build_summary()
        )

    monkeypatch.setattr(
        workflow_route,
        "run_dataset_workflow",
        fake_run_dataset_workflow,
    )

    response = client.post(
        "/api/workflows/run",
        files={
            "file": (
                "customers.csv",
                b"customer_id,age\n1,25\n2,30\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["ingestion_id"] == "ingestion-123"
    assert payload["catalog_id"] == 1
    assert payload["version_id"] == 7

    assert (
        payload["validation_status"]
        == "ACCEPTED"
    )

    assert (
        payload["governance_decision"]
        == "APPROVED"
    )

    assert (
        payload["lifecycle_state"]
        == "VALIDATED"
    )

    assert payload["promotion_eligible"] is True

    assert (
        payload["lineage_url"]
        == "/api/datasets/7/lineage"
    )


def test_rejected_dataset_is_valid_workflow_result(
    monkeypatch,
):
    def fake_run_dataset_workflow(
        source,
        *,
        persist_raw: bool,
    ):
        return FakeWorkflowResult(
            build_summary(
                validation_status="REJECTED",
                governance_decision="REJECTED",
                lifecycle_state="QUARANTINED",
                promotion_eligible=False,
            )
        )

    monkeypatch.setattr(
        workflow_route,
        "run_dataset_workflow",
        fake_run_dataset_workflow,
    )

    response = client.post(
        "/api/workflows/run",
        files={
            "file": (
                "customers.csv",
                b"customer_id,age\n1,25\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["validation_status"]
        == "REJECTED"
    )

    assert (
        payload["lifecycle_state"]
        == "QUARANTINED"
    )

    assert payload["promotion_eligible"] is False


def test_workflow_api_maps_ingestion_error_to_400(
    monkeypatch,
):
    def fake_run_dataset_workflow(
        source,
        *,
        persist_raw: bool,
    ):
        raise DatasetWorkflowError(
            stage="INGESTION",
            cause=ValueError(
                "Invalid dataset."
            ),
        )

    monkeypatch.setattr(
        workflow_route,
        "run_dataset_workflow",
        fake_run_dataset_workflow,
    )

    response = client.post(
        "/api/workflows/run",
        files={
            "file": (
                "customers.csv",
                b"invalid-data",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["stage"]
        == "INGESTION"
    )


def test_workflow_api_hides_internal_error(
    monkeypatch,
):
    def fake_run_dataset_workflow(
        source,
        *,
        persist_raw: bool,
    ):
        raise DatasetWorkflowError(
            stage="CATALOG_REGISTRATION",
            cause=RuntimeError(
                "database unavailable"
            ),
        )

    monkeypatch.setattr(
        workflow_route,
        "run_dataset_workflow",
        fake_run_dataset_workflow,
    )

    response = client.post(
        "/api/workflows/run",
        files={
            "file": (
                "customers.csv",
                b"customer_id\n1\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 500

    payload = response.json()

    assert (
        payload["detail"]["stage"]
        == "CATALOG_REGISTRATION"
    )

    assert (
        "database unavailable"
        not in str(payload)
    )


def test_workflow_api_rejects_empty_upload():
    response = client.post(
        "/api/workflows/run",
        files={
            "file": (
                "customers.csv",
                b"",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400