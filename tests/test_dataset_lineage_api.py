from __future__ import annotations

import pandas as pd
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
            "contract_validation_count": 1,
            "latest_contract_validation_id": 9,
            "latest_contract_id": 3,
            "latest_contract_version": 2,
            "latest_contract_validation_status": (
                "COMPATIBLE"
            ),
            "latest_contract_enforcement_mode": (
                "BLOCK"
            ),
            "latest_contract_violation_count": 0,
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
        "contract_validations": [
            {
                "contract_validation_id": 9,
                "contract_id": 3,
                "contract_version": 2,
                "validation_status": "COMPATIBLE",
                "enforcement_mode": "BLOCK",
                "violation_count": 0,
                "validated_at": (
                    "2026-09-01T08:20:30+00:00"
                ),
            }
        ],
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

    assert (
        payload["summary"][
            "contract_validation_count"
        ]
        == 1
    )

    assert (
        payload["summary"][
            "latest_contract_validation_status"
        ]
        == "COMPATIBLE"
    )

    assert (
        payload["summary"][
            "latest_contract_enforcement_mode"
        ]
        == "BLOCK"
    )

    assert len(
        payload["contract_validations"]
    ) == 1

    assert (
        payload["contract_validations"][0][
            "contract_id"
        ]
        == 3
    )


def test_get_catalog_lineage_success(
    monkeypatch,
):
    expected = pd.DataFrame(
        [
            {
                "catalog_id": 1,
                "version_id": 5,
                "version_number": 5,
                "file_name": "sample_customers.csv",
                "lifecycle_state": "ACTIVE",
                "ingestion_count": 2,
                "validation_count": 1,
                "governance_count": 1,
                "promotion_eligible": False,
            },
            {
                "catalog_id": 1,
                "version_id": 4,
                "version_number": 4,
                "file_name": "sample_customers.csv",
                "lifecycle_state": "SUPERSEDED",
                "ingestion_count": 1,
                "validation_count": 1,
                "governance_count": 1,
                "promotion_eligible": False,
            },
        ]
    )

    def fake_get_catalog_lineage(
        catalog_id: int,
    ):
        assert catalog_id == 1
        return expected

    monkeypatch.setattr(
        datasets_route,
        "get_catalog_lineage",
        fake_get_catalog_lineage,
        raising=False,
    )

    response = client.get(
        "/api/datasets/catalogs/1/lineage"
    )

    assert response.status_code == 200

    assert response.json() == {
        "records": [
            {
                "catalog_id": 1,
                "version_id": 5,
                "version_number": 5,
                "file_name": "sample_customers.csv",
                "lifecycle_state": "ACTIVE",
                "ingestion_count": 2,
                "validation_count": 1,
                "governance_count": 1,
                "promotion_eligible": False,
            },
            {
                "catalog_id": 1,
                "version_id": 4,
                "version_number": 4,
                "file_name": "sample_customers.csv",
                "lifecycle_state": "SUPERSEDED",
                "ingestion_count": 1,
                "validation_count": 1,
                "governance_count": 1,
                "promotion_eligible": False,
            },
        ]
    }


def test_get_dataset_version_history_success(
    monkeypatch,
):
    expected = pd.DataFrame(
        [
            {
                "version_id": 7,
                "version_number": 2,
                "content_sha256": "sha-v2",
                "file_name": "customers.csv",
                "file_type": "CSV",
                "extension": "csv",
                "byte_size": 2048,
                "row_count": 20,
                "column_count": 4,
                "raw_path": "data/raw/customers_v2.csv",
                "created_at": pd.Timestamp(
                    "2026-10-08T09:00:00"
                ),
                "ingestion_count": 2,
                "last_ingested_at": pd.Timestamp(
                    "2026-10-08T10:00:00"
                ),
            },
            {
                "version_id": 6,
                "version_number": 1,
                "content_sha256": "sha-v1",
                "file_name": "customers.csv",
                "file_type": "CSV",
                "extension": "csv",
                "byte_size": 1024,
                "row_count": 10,
                "column_count": 4,
                "raw_path": "data/raw/customers_v1.csv",
                "created_at": pd.Timestamp(
                    "2026-10-07T09:00:00"
                ),
                "ingestion_count": 0,
                "last_ingested_at": pd.NaT,
            },
        ]
    )

    def fake_get_dataset_version_history(
        catalog_id: int,
    ):
        assert catalog_id == 1
        return expected

    monkeypatch.setattr(
        datasets_route,
        "get_dataset_version_history",
        fake_get_dataset_version_history,
        raising=False,
    )

    response = client.get(
        "/api/datasets/catalogs/1/versions"
    )

    assert response.status_code == 200

    assert response.json() == {
        "records": [
            {
                "version_id": 7,
                "version_number": 2,
                "content_sha256": "sha-v2",
                "file_name": "customers.csv",
                "file_type": "CSV",
                "extension": "csv",
                "byte_size": 2048,
                "row_count": 20,
                "column_count": 4,
                "raw_path": "data/raw/customers_v2.csv",
                "created_at": "2026-10-08T09:00:00",
                "ingestion_count": 2,
                "last_ingested_at": (
                    "2026-10-08T10:00:00"
                ),
            },
            {
                "version_id": 6,
                "version_number": 1,
                "content_sha256": "sha-v1",
                "file_name": "customers.csv",
                "file_type": "CSV",
                "extension": "csv",
                "byte_size": 1024,
                "row_count": 10,
                "column_count": 4,
                "raw_path": "data/raw/customers_v1.csv",
                "created_at": "2026-10-07T09:00:00",
                "ingestion_count": 0,
                "last_ingested_at": None,
            },
        ]
    }


def test_get_dataset_version_history_internal_error(
    monkeypatch,
):
    def fake_get_dataset_version_history(
        catalog_id: int,
    ):
        assert catalog_id == 1
        raise RuntimeError("database exploded")

    monkeypatch.setattr(
        datasets_route,
        "get_dataset_version_history",
        fake_get_dataset_version_history,
    )

    response = client.get(
        "/api/datasets/catalogs/1/versions"
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": (
            "Unable to load "
            "dataset version history."
        )
    }


def test_get_dataset_version_history_invalid_catalog_id():
    response = client.get(
        "/api/datasets/catalogs/0/versions"
    )

    assert response.status_code == 422


def test_get_ingestion_history_success(
    monkeypatch,
):
    expected = pd.DataFrame(
        [
            {
                "ingestion_event_id": 12,
                "ingestion_id": "ing-002",
                "catalog_id": 1,
                "version_id": 7,
                "version_number": 2,
                "source_type": "UPLOAD",
                "ingested_at": pd.Timestamp(
                    "2026-10-08T10:00:00"
                ),
                "is_new_version": False,
                "raw_path": "data/raw/customers_v2.csv",
            },
            {
                "ingestion_event_id": 11,
                "ingestion_id": "ing-001",
                "catalog_id": 1,
                "version_id": 6,
                "version_number": 1,
                "source_type": "UPLOAD",
                "ingested_at": pd.Timestamp(
                    "2026-10-07T09:00:00"
                ),
                "is_new_version": True,
                "raw_path": "data/raw/customers_v1.csv",
            },
        ]
    )

    def fake_get_ingestion_history(
        catalog_id: int,
        limit: int = 50,
    ):
        assert catalog_id == 1
        assert limit == 2
        return expected

    monkeypatch.setattr(
        datasets_route,
        "get_ingestion_history",
        fake_get_ingestion_history,
        raising=False,
    )

    response = client.get(
        "/api/datasets/catalogs/1/ingestions"
        "?limit=2"
    )

    assert response.status_code == 200

    assert response.json() == {
        "records": [
            {
                "ingestion_event_id": 12,
                "ingestion_id": "ing-002",
                "catalog_id": 1,
                "version_id": 7,
                "version_number": 2,
                "source_type": "UPLOAD",
                "ingested_at": "2026-10-08T10:00:00",
                "is_new_version": False,
                "raw_path": "data/raw/customers_v2.csv",
            },
            {
                "ingestion_event_id": 11,
                "ingestion_id": "ing-001",
                "catalog_id": 1,
                "version_id": 6,
                "version_number": 1,
                "source_type": "UPLOAD",
                "ingested_at": "2026-10-07T09:00:00",
                "is_new_version": True,
                "raw_path": "data/raw/customers_v1.csv",
            },
        ]
    }


def test_get_ingestion_history_internal_error(
    monkeypatch,
):
    def fake_get_ingestion_history(
        catalog_id: int,
        limit: int = 50,
    ):
        assert catalog_id == 1
        assert limit == 50
        raise RuntimeError("database exploded")

    monkeypatch.setattr(
        datasets_route,
        "get_ingestion_history",
        fake_get_ingestion_history,
    )

    response = client.get(
        "/api/datasets/catalogs/1/ingestions"
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": (
            "Unable to load "
            "ingestion history."
        )
    }


def test_get_ingestion_history_invalid_catalog_id():
    response = client.get(
        "/api/datasets/catalogs/0/ingestions"
    )

    assert response.status_code == 422


def test_get_ingestion_history_invalid_limit():
    response = client.get(
        "/api/datasets/catalogs/1/ingestions"
        "?limit=0"
    )

    assert response.status_code == 422


def test_get_catalog_lineage_internal_error(
    monkeypatch,
):
    def fake_get_catalog_lineage(
        catalog_id: int,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        datasets_route,
        "get_catalog_lineage",
        fake_get_catalog_lineage,
    )

    response = client.get(
        "/api/datasets/catalogs/1/lineage"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": (
            "Unable to load "
            "catalog lineage."
        )
    }


def test_get_catalog_lineage_rejects_invalid_id():
    response = client.get(
        "/api/datasets/catalogs/0/lineage"
    )

    assert response.status_code == 422


def test_get_validation_history_success(
    monkeypatch,
):
    expected = pd.DataFrame(
        [
            {
                "validation_id": 21,
                "ingestion_event_id": 12,
                "ingestion_id": "ing-002",
                "catalog_id": 1,
                "version_id": 7,
                "version_number": 2,
                "policy_version": "v1",
                "validation_status": "ACCEPTED",
                "validated_at": pd.Timestamp(
                    "2026-10-08T10:30:00"
                ),
                "total_issues": 1,
                "high_issues": 0,
                "medium_issues": 1,
                "low_issues": 0,
                "blocking_issue_count": 0,
                "rejection_reason": None,
                "artifact_path": (
                    "data/processed/customers_v2.csv"
                ),
                "validation_metadata_path": (
                    "data/metadata/validation_21.json"
                ),
            }
        ]
    )

    def fake_get_validation_history(
        catalog_id: int,
        limit: int = 50,
    ):
        assert catalog_id == 1
        assert limit == 2
        return expected

    monkeypatch.setattr(
        datasets_route,
        "get_validation_history",
        fake_get_validation_history,
        raising=False,
    )

    response = client.get(
        "/api/datasets/catalogs/1/validations"
        "?limit=2"
    )

    assert response.status_code == 200
    assert response.json() == {
        "records": [
            {
                "validation_id": 21,
                "ingestion_event_id": 12,
                "ingestion_id": "ing-002",
                "catalog_id": 1,
                "version_id": 7,
                "version_number": 2,
                "policy_version": "v1",
                "validation_status": "ACCEPTED",
                "validated_at": (
                    "2026-10-08T10:30:00"
                ),
                "total_issues": 1,
                "high_issues": 0,
                "medium_issues": 1,
                "low_issues": 0,
                "blocking_issue_count": 0,
                "rejection_reason": None,
                "artifact_path": (
                    "data/processed/customers_v2.csv"
                ),
                "validation_metadata_path": (
                    "data/metadata/validation_21.json"
                ),
            }
        ]
    }


def test_get_validation_history_internal_error(
    monkeypatch,
):
    def fake_get_validation_history(
        catalog_id: int,
        limit: int = 50,
    ):
        assert catalog_id == 1
        assert limit == 50
        raise RuntimeError("database exploded")

    monkeypatch.setattr(
        datasets_route,
        "get_validation_history",
        fake_get_validation_history,
    )

    response = client.get(
        "/api/datasets/catalogs/1/validations"
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": (
            "Unable to load "
            "validation history."
        )
    }


def test_get_validation_history_invalid_catalog_id():
    response = client.get(
        "/api/datasets/catalogs/0/validations"
    )

    assert response.status_code == 422


def test_get_validation_history_invalid_limit():
    response = client.get(
        "/api/datasets/catalogs/1/validations"
        "?limit=0"
    )

    assert response.status_code == 422


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


def test_get_governance_history_success(
    monkeypatch,
):
    expected = pd.DataFrame(
        [
            {
                "governance_id": 31,
                "catalog_id": 1,
                "version_id": 7,
                "version_number": 2,
                "validation_id": 21,
                "policy_version": "v1",
                "decision": "APPROVED",
                "reason": "Policy checks passed.",
                "promotion_eligible": True,
                "trust_score": 92.5,
                "validation_status": "ACCEPTED",
                "privacy_status": "PASS",
                "blocking_issue_count": 0,
                "created_at": pd.Timestamp(
                    "2026-10-08T11:00:00"
                ),
            }
        ]
    )

    def fake_get_governance_history(
        catalog_id: int,
        limit: int = 50,
    ):
        assert catalog_id == 1
        assert limit == 2
        return expected

    monkeypatch.setattr(
        datasets_route,
        "get_governance_history",
        fake_get_governance_history,
        raising=False,
    )

    response = client.get(
        "/api/datasets/catalogs/1/governance"
        "?limit=2"
    )

    assert response.status_code == 200
    assert response.json() == {
        "records": [
            {
                "governance_id": 31,
                "catalog_id": 1,
                "version_id": 7,
                "version_number": 2,
                "validation_id": 21,
                "policy_version": "v1",
                "decision": "APPROVED",
                "reason": "Policy checks passed.",
                "promotion_eligible": True,
                "trust_score": 92.5,
                "validation_status": "ACCEPTED",
                "privacy_status": "PASS",
                "blocking_issue_count": 0,
                "created_at": "2026-10-08T11:00:00",
            }
        ]
    }


def test_get_governance_history_internal_error(
    monkeypatch,
):
    def fake_get_governance_history(
        catalog_id: int,
        limit: int = 50,
    ):
        assert catalog_id == 1
        assert limit == 50
        raise RuntimeError("database exploded")

    monkeypatch.setattr(
        datasets_route,
        "get_governance_history",
        fake_get_governance_history,
    )

    response = client.get(
        "/api/datasets/catalogs/1/governance"
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": (
            "Unable to load "
            "governance history."
        )
    }


def test_get_governance_history_invalid_catalog_id():
    response = client.get(
        "/api/datasets/catalogs/0/governance"
    )

    assert response.status_code == 422


def test_get_governance_history_invalid_limit():
    response = client.get(
        "/api/datasets/catalogs/1/governance"
        "?limit=0"
    )

    assert response.status_code == 422


def test_get_catalog_lifecycle_success(
    monkeypatch,
):
    expected = pd.DataFrame(
        [
            {
                "version_id": 7,
                "catalog_id": 1,
                "version_number": 2,
                "lifecycle_state": "VALIDATED",
                "created_at": pd.Timestamp(
                    "2026-10-08T11:00:00"
                ),
            }
        ]
    )

    def fake_get_catalog_lifecycle(
        catalog_id: int,
    ):
        assert catalog_id == 1
        return expected

    monkeypatch.setattr(
        datasets_route,
        "get_catalog_lifecycle",
        fake_get_catalog_lifecycle,
        raising=False,
    )

    response = client.get(
        "/api/datasets/catalogs/1/lifecycle"
    )

    assert response.status_code == 200

    assert response.json() == {
        "records": [
            {
                "version_id": 7,
                "catalog_id": 1,
                "version_number": 2,
                "lifecycle_state": "VALIDATED",
                "created_at": "2026-10-08T11:00:00",
            }
        ]
    }


def test_get_catalog_lifecycle_internal_error(
    monkeypatch,
):
    def fake_get_catalog_lifecycle(
        catalog_id: int,
    ):
        raise RuntimeError("database exploded")

    monkeypatch.setattr(
        datasets_route,
        "get_catalog_lifecycle",
        fake_get_catalog_lifecycle,
    )

    response = client.get(
        "/api/datasets/catalogs/1/lifecycle"
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Unable to load catalog lifecycle."
    }


def test_get_catalog_lifecycle_invalid_catalog_id():
    response = client.get(
        "/api/datasets/catalogs/0/lifecycle"
    )

    assert response.status_code == 422


def test_get_lifecycle_history_success(
    monkeypatch,
):
    expected = pd.DataFrame(
        [
            {
                "lifecycle_event_id": 41,
                "catalog_id": 1,
                "version_id": 7,
                "from_state": "VALIDATED",
                "to_state": "ACTIVE",
                "reason": "Governance approved.",
                "changed_at": pd.Timestamp(
                    "2026-10-08T12:00:00"
                ),
            }
        ]
    )

    def fake_get_lifecycle_history(
        version_id: int,
    ):
        assert version_id == 7
        return expected

    monkeypatch.setattr(
        datasets_route,
        "get_lifecycle_history",
        fake_get_lifecycle_history,
        raising=False,
    )

    response = client.get(
        "/api/datasets/7/lifecycle"
    )

    assert response.status_code == 200
    assert response.json() == {
        "records": [
            {
                "lifecycle_event_id": 41,
                "catalog_id": 1,
                "version_id": 7,
                "from_state": "VALIDATED",
                "to_state": "ACTIVE",
                "reason": "Governance approved.",
                "changed_at": "2026-10-08T12:00:00",
            }
        ]
    }


def test_get_lifecycle_history_internal_error(
    monkeypatch,
):
    def fake_get_lifecycle_history(
        version_id: int,
    ):
        raise RuntimeError("database exploded")

    monkeypatch.setattr(
        datasets_route,
        "get_lifecycle_history",
        fake_get_lifecycle_history,
    )

    response = client.get(
        "/api/datasets/7/lifecycle"
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Unable to load lifecycle history."
    }


def test_get_lifecycle_history_invalid_version_id():
    response = client.get(
        "/api/datasets/0/lifecycle"
    )

    assert response.status_code == 422