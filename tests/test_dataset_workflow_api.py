from __future__ import annotations

import pandas as pd
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

        self.dataframe = pd.DataFrame()
        self.profile = {}

        self.ingestion_metadata = {
            "ingestion_id": summary["ingestion_id"],
        }

        self.catalog_registration = {
            "catalog_id": summary["catalog_id"],
            "version_id": summary["version_id"],
            "version_number": summary["version_number"],
        }

        self.validation_result = {
            "status": summary["validation_status"],
        }

        self.validation_registration = {
            "validation_id": summary["validation_id"],
        }

        self.governance_result = {
            "decision": summary["governance_decision"],
            "trust_score": summary["trust_score"],
            "privacy_status": summary["privacy_status"],
            "promotion_eligible": summary[
                "promotion_eligible"
            ],
        }

        self.governance_registration = {
            "governance_id": summary["governance_id"],
        }

        self.lifecycle_result = {
            "lifecycle_state": summary[
                "lifecycle_state"
            ],
        }

        self.quality_report = {}

        self.trust_score_report = {
            "trust_score": summary["trust_score"],
        }

        self.privacy_report = {
            "privacy_status": summary[
                "privacy_status"
            ],
        }

        self.data_contract = (
            {
                "contract_id": summary["contract_id"],
                "contract_version": summary[
                    "contract_version"
                ],
                "enforcement_mode": summary[
                    "contract_enforcement_mode"
                ],
            }
            if summary.get("contract_id") is not None
            else None
        )

        self.contract_validation = (
            {
                "validation_id": summary[
                    "contract_validation_id"
                ],
                "status": summary[
                    "contract_validation_status"
                ],
            }
            if summary.get(
                "contract_validation_id"
            )
            is not None
            else None
        )

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
        "contract_id": 3,
        "contract_version": 3,
        "contract_enforcement_mode": "BLOCK",
        "contract_validation_id": 12,
        "contract_validation_status": "COMPATIBLE",
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

    assert payload["contract_id"] == 3
    assert payload["contract_version"] == 3

    assert (
        payload["contract_enforcement_mode"]
        == "BLOCK"
    )

    assert (
        payload["contract_validation_id"]
        == 12
    )

    assert (
        payload["contract_validation_status"]
        == "COMPATIBLE"
    )

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


def test_workflow_api_serializes_dataframe_and_profile(
    monkeypatch,
):
    class RichFakeWorkflowResult:
        dataframe = pd.DataFrame(
            [
                {
                    "customer_id": 1,
                    "age": 25,
                },
                {
                    "customer_id": 2,
                    "age": 30,
                },
            ]
        )

        profile = {
            "basic_info": {
                "total_rows": 2,
            },
            "column_types": {
                "numeric_columns": [
                    "customer_id",
                    "age",
                ],
            },
            "schema_summary": pd.DataFrame(
                [
                    {
                        "column_name": "age",
                        "dtype": "int64",
                    }
                ]
            ),
            "missing_summary": pd.DataFrame(
                [
                    {
                        "column_name": "age",
                        "missing_count": 0,
                    }
                ]
            ),
            "duplicate_summary": {
                "duplicate_rows": 0,
            },
            "numeric_summary": pd.DataFrame(
                [
                    {
                        "column_name": "age",
                        "mean": 27.5,
                    }
                ]
            ),
            "categorical_summary": pd.DataFrame(
                [
                    {
                        "column_name": "segment",
                        "unique_count": 2,
                    }
                ]
            ),
        }

        ingestion_metadata = {
            "ingestion_id": "ingestion-123",
            "file_name": "customers.csv",
        }

        catalog_registration = {
            "catalog_id": 1,
            "version_id": 7,
            "version_number": 3,
        }

        validation_result = {
            "status": "ACCEPTED",
            "blocking_issue_count": 0,
        }

        validation_registration = {
            "validation_id": 9,
        }

        governance_result = {
            "decision": "APPROVED",
            "promotion_eligible": True,
        }

        governance_registration = {
            "governance_id": 4,
        }

        lifecycle_result = {
            "lifecycle_state": "VALIDATED",
        }

        quality_report = {
            "status": "PASS",
        }

        trust_score_report = {
            "trust_score": 94.5,
        }

        privacy_report = {
            "privacy_status": "LOW",
        }

        data_contract = {
            "contract_id": 3,
        }

        contract_validation = {
            "status": "COMPATIBLE",
        }

        def summary(self):
            return build_summary()

    def fake_run_dataset_workflow(
        source,
        *,
        persist_raw: bool,
    ):
        return RichFakeWorkflowResult()

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

    assert payload["records"] == [
        {
            "customer_id": 1,
            "age": 25,
        },
        {
            "customer_id": 2,
            "age": 30,
        },
    ]

    assert payload["profile"]["schema_summary"] == [
        {
            "column_name": "age",
            "dtype": "int64",
        }
    ]

    assert payload["profile"]["missing_summary"] == [
        {
            "column_name": "age",
            "missing_count": 0,
        }
    ]

    assert payload["profile"]["numeric_summary"] == [
        {
            "column_name": "age",
            "mean": 27.5,
        }
    ]

    assert payload["profile"]["categorical_summary"] == [
        {
            "column_name": "segment",
            "unique_count": 2,
        }
    ]

    assert payload["profile"]["duplicate_summary"] == {
        "duplicate_rows": 0,
    }

    assert payload["ingestion_metadata"] == (
        RichFakeWorkflowResult.ingestion_metadata
    )
    assert payload["catalog_registration"] == (
        RichFakeWorkflowResult.catalog_registration
    )
    assert payload["validation_result"] == (
        RichFakeWorkflowResult.validation_result
    )
    assert payload["validation_registration"] == (
        RichFakeWorkflowResult.validation_registration
    )
    assert payload["governance_result"] == (
        RichFakeWorkflowResult.governance_result
    )
    assert payload["governance_registration"] == (
        RichFakeWorkflowResult.governance_registration
    )
    assert payload["lifecycle_result"] == (
        RichFakeWorkflowResult.lifecycle_result
    )
    assert payload["quality_report"] == (
        RichFakeWorkflowResult.quality_report
    )
    assert payload["trust_score_report"] == (
        RichFakeWorkflowResult.trust_score_report
    )
    assert payload["privacy_report"] == (
        RichFakeWorkflowResult.privacy_report
    )
    assert payload["data_contract"] == (
        RichFakeWorkflowResult.data_contract
    )
    assert payload["contract_validation"] == (
        RichFakeWorkflowResult.contract_validation
    )


def test_continue_dataset_workflow_reuses_ingestion(
    monkeypatch,
):
    captured = {}

    def fake_continue_dataset_workflow(
        ingestion_result,
    ):
        captured["dataframe"] = (
            ingestion_result.dataframe.copy()
        )
        captured["metadata"] = (
            ingestion_result.metadata
        )

        return FakeWorkflowResult(
            build_summary()
        )

    monkeypatch.setattr(
        workflow_route,
        "continue_dataset_workflow",
        fake_continue_dataset_workflow,
        raising=False,
    )

    response = client.post(
        "/api/workflows/continue",
        json={
            "records": [
                {
                    "customer_id": 1,
                    "age": 25,
                },
                {
                    "customer_id": 2,
                    "age": 30,
                },
            ],
            "ingestion_metadata": {
                "ingestion_id": "ingestion-123",
                "source_type": "upload",
                "file_name": "customers.csv",
                "file_type": "csv",
                "extension": ".csv",
                "content_sha256": "abc123",
                "byte_size": 26,
                "row_count": 2,
                "column_count": 2,
                "ingested_at": (
                    "2026-09-18T10:00:00"
                ),
                "raw_path": (
                    "data/raw/customers.csv"
                ),
            },
        },
    )

    assert response.status_code == 200

    assert captured[
        "dataframe"
    ].to_dict(
        orient="records"
    ) == [
        {
            "customer_id": 1,
            "age": 25,
        },
        {
            "customer_id": 2,
            "age": 30,
        },
    ]

    assert (
        captured["metadata"].ingestion_id
        == "ingestion-123"
    )

    assert (
        captured["metadata"].content_sha256
        == "abc123"
    )

    assert (
        response.json()["ingestion_id"]
        == "ingestion-123"
    )


def test_ingest_dataset_api_returns_reusable_ingestion(
    monkeypatch,
):
    captured = {}

    class FakeMetadata:
        def to_dict(self):
            return {
                "ingestion_id": "ingestion-123",
                "source_type": "upload",
                "file_name": "customers.csv",
                "file_type": "csv",
                "extension": ".csv",
                "content_sha256": "abc123",
                "byte_size": 26,
                "row_count": 2,
                "column_count": 2,
                "ingested_at": "2026-09-18T10:00:00",
                "raw_path": "data/raw/customers.csv",
            }

    class FakeIngestionResult:
        dataframe = pd.DataFrame(
            [
                {
                    "customer_id": 1,
                    "age": 25,
                },
                {
                    "customer_id": 2,
                    "age": 30,
                },
            ]
        )

        metadata = FakeMetadata()

    def fake_ingest_dataset(
        source,
        *,
        persist_raw: bool,
    ):
        captured["name"] = source.name
        captured["content"] = source.getvalue()
        captured["persist_raw"] = persist_raw

        return FakeIngestionResult()

    monkeypatch.setattr(
        workflow_route,
        "ingest_dataset",
        fake_ingest_dataset,
        raising=False,
    )

    response = client.post(
        "/api/workflows/ingest",
        files={
            "file": (
                "customers.csv",
                b"customer_id,age\n1,25\n2,30\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    assert captured["name"] == "customers.csv"
    assert captured["content"] == (
        b"customer_id,age\n1,25\n2,30\n"
    )
    assert captured["persist_raw"] is True

    payload = response.json()

    assert payload["records"] == [
        {
            "customer_id": 1,
            "age": 25,
        },
        {
            "customer_id": 2,
            "age": 30,
        },
    ]

    assert payload["ingestion_metadata"][
        "ingestion_id"
    ] == "ingestion-123"

    assert payload["ingestion_metadata"][
        "content_sha256"
    ] == "abc123"