from __future__ import annotations

import pandas as pd
import pytest

import src.workflows.dataset_workflow as workflow_module
from src.ingestion.contracts import (
    IngestionMetadata,
    IngestionResult,
)
from src.workflows.contracts import (
    DatasetWorkflowError,
    DatasetWorkflowResult,
)


class FakeResult:
    def __init__(
        self,
        values: dict,
    ) -> None:
        self.values = values

    def to_dict(
        self,
    ) -> dict:
        return dict(
            self.values
        )


def build_ingestion_result() -> IngestionResult:
    dataframe = pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
            ],
            "age": [
                20,
                30,
            ],
        }
    )

    metadata = IngestionMetadata(
        ingestion_id="ingestion-1",
        source_type="upload",
        file_name="customers.csv",
        file_type="CSV",
        extension=".csv",
        content_sha256="a" * 64,
        byte_size=100,
        row_count=2,
        column_count=2,
        ingested_at=(
            "2026-09-02T00:00:00+00:00"
        ),
        raw_path=(
            "data/raw/customers.csv"
        ),
    )

    return IngestionResult(
        dataframe=dataframe,
        metadata=metadata,
    )


def configure_successful_workflow(
    monkeypatch: pytest.MonkeyPatch,
) -> list[str]:
    calls: list[str] = []

    def fake_profile_dataset(
        dataframe: pd.DataFrame,
    ) -> dict:
        calls.append(
            "profile"
        )

        return {
            "basic_info": {
                "total_rows": len(
                    dataframe
                ),
            }
        }

    def fake_register_ingestion(
        metadata: dict,
    ) -> dict:
        calls.append(
            "catalog"
        )

        assert (
            metadata["ingestion_id"]
            == "ingestion-1"
        )

        return {
            "ingestion_event_id": 10,
            "catalog_id": 1,
            "version_id": 4,
            "version_number": 4,
            "is_new_version": True,
        }

    def fake_validation_gate(
        *,
        df: pd.DataFrame,
        ingestion_metadata: dict,
    ) -> FakeResult:
        calls.append(
            "validation_gate"
        )

        assert len(df) == 2
        assert (
            ingestion_metadata[
                "ingestion_id"
            ]
            == "ingestion-1"
        )

        return FakeResult(
            {
                "ingestion_id": (
                    "ingestion-1"
                ),
                "status": "ACCEPTED",
                "policy_version": "1.0",
                "validated_at": (
                    "2026-09-02T00:01:00+00:00"
                ),
                "total_issues": 0,
                "high_issues": 0,
                "medium_issues": 0,
                "low_issues": 0,
                "blocking_issue_count": 0,
                "blocking_issues": [],
                "artifact_path": (
                    "data/processed/"
                    "customers.csv"
                ),
                "validation_metadata_path": (
                    "data/processed/"
                    "customers.validation.json"
                ),
            }
        )

    def fake_register_validation(
        validation_result: dict,
        catalog_registration: dict,
    ) -> dict:
        calls.append(
            "validation_persist"
        )

        assert (
            validation_result["status"]
            == "ACCEPTED"
        )

        assert (
            catalog_registration[
                "version_id"
            ]
            == 4
        )

        return {
            "validation_id": 7,
            "version_id": 4,
            "catalog_id": 1,
        }

    def fake_evaluate_governance(
        *,
        df: pd.DataFrame,
        validation_result: dict,
    ) -> dict:
        calls.append(
            "governance_evaluate"
        )

        assert len(df) == 2
        assert (
            validation_result["status"]
            == "ACCEPTED"
        )

        return {
            "governance_result": (
                FakeResult(
                    {
                        "decision": (
                            "APPROVED"
                        ),
                        "reason": (
                            "Policy passed."
                        ),
                        "promotion_eligible": True,
                        "policy_version": "1.0",
                        "validation_status": (
                            "ACCEPTED"
                        ),
                        "trust_score": 100.0,
                        "privacy_status": "LOW",
                        "blocking_issue_count": 0,
                    }
                )
            ),
            "quality_report": {
                "summary": {
                    "total_issues": 0,
                }
            },
            "trust_score_report": {
                "overall_score": 100.0,
            },
            "privacy_report": {
                "summary": {
                    "risk_level": "Low",
                }
            },
        }

    def fake_register_governance(
        *,
        governance_result: dict,
        catalog_registration: dict,
        validation_registration: dict,
    ) -> dict:
        calls.append(
            "governance_persist"
        )

        assert (
            governance_result["decision"]
            == "APPROVED"
        )

        assert (
            validation_registration[
                "validation_id"
            ]
            == 7
        )

        return {
            "governance_id": 2,
            "catalog_id": 1,
            "version_id": 4,
            "validation_id": 7,
            "decision": "APPROVED",
            "promotion_eligible": True,
        }

    def fake_apply_lifecycle(
        catalog_registration: dict,
        validation_result: dict,
    ) -> dict:
        calls.append(
            "lifecycle"
        )

        assert (
            catalog_registration[
                "version_id"
            ]
            == 4
        )

        assert (
            validation_result["status"]
            == "ACCEPTED"
        )

        return {
            "catalog_id": 1,
            "version_id": 4,
            "version_number": 4,
            "previous_state": "NEW",
            "lifecycle_state": (
                "VALIDATED"
            ),
            "changed": True,
        }

    monkeypatch.setattr(
        workflow_module,
        "profile_dataset",
        fake_profile_dataset,
    )

    monkeypatch.setattr(
        workflow_module,
        "register_ingestion",
        fake_register_ingestion,
    )

    monkeypatch.setattr(
        workflow_module,
        "validate_and_route_dataset",
        fake_validation_gate,
    )

    monkeypatch.setattr(
        workflow_module,
        "register_validation",
        fake_register_validation,
    )

    monkeypatch.setattr(
        workflow_module,
        "evaluate_dataset_governance",
        fake_evaluate_governance,
    )

    monkeypatch.setattr(
        workflow_module,
        "register_governance_decision",
        fake_register_governance,
    )

    monkeypatch.setattr(
        workflow_module,
        "apply_validation_lifecycle",
        fake_apply_lifecycle,
    )

    return calls


def test_continue_dataset_workflow_runs_all_stages(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = configure_successful_workflow(
        monkeypatch
    )

    result = (
        workflow_module.continue_dataset_workflow(
            build_ingestion_result()
        )
    )

    assert isinstance(
        result,
        DatasetWorkflowResult,
    )

    assert calls == [
        "profile",
        "catalog",
        "validation_gate",
        "validation_persist",
        "governance_evaluate",
        "governance_persist",
        "lifecycle",
    ]

    assert (
        result.catalog_registration[
            "version_id"
        ]
        == 4
    )

    assert (
        result.validation_registration[
            "validation_id"
        ]
        == 7
    )

    assert (
        result.governance_registration[
            "governance_id"
        ]
        == 2
    )

    assert (
        result.lifecycle_result[
            "lifecycle_state"
        ]
        == "VALIDATED"
    )


def test_workflow_summary_contains_platform_ids(
    monkeypatch: pytest.MonkeyPatch,
):
    configure_successful_workflow(
        monkeypatch
    )

    result = (
        workflow_module.continue_dataset_workflow(
            build_ingestion_result()
        )
    )

    summary = result.summary()

    assert (
        summary["ingestion_id"]
        == "ingestion-1"
    )

    assert (
        summary["catalog_id"]
        == 1
    )

    assert (
        summary["version_id"]
        == 4
    )

    assert (
        summary["validation_id"]
        == 7
    )

    assert (
        summary["governance_id"]
        == 2
    )

    assert (
        summary["governance_decision"]
        == "APPROVED"
    )

    assert (
        summary["lifecycle_state"]
        == "VALIDATED"
    )


def test_workflow_does_not_auto_promote(
    monkeypatch: pytest.MonkeyPatch,
):
    configure_successful_workflow(
        monkeypatch
    )

    result = (
        workflow_module.continue_dataset_workflow(
            build_ingestion_result()
        )
    )

    assert (
        result.lifecycle_result[
            "lifecycle_state"
        ]
        == "VALIDATED"
    )

    assert (
        result.governance_result[
            "promotion_eligible"
        ]
        is True
    )

    assert not hasattr(
        workflow_module,
        "promote_version",
    )


def test_run_dataset_workflow_starts_with_ingestion(
    monkeypatch: pytest.MonkeyPatch,
):
    expected = (
        build_ingestion_result()
    )

    received: dict = {}

    def fake_ingest_dataset(
        source,
        *,
        persist_raw: bool,
    ):
        received["source"] = source
        received[
            "persist_raw"
        ] = persist_raw

        return expected

    def fake_continue(
        ingestion_result: IngestionResult,
    ):
        assert (
            ingestion_result
            is expected
        )

        return "workflow-result"

    monkeypatch.setattr(
        workflow_module,
        "ingest_dataset",
        fake_ingest_dataset,
    )

    monkeypatch.setattr(
        workflow_module,
        "continue_dataset_workflow",
        fake_continue,
    )

    result = (
        workflow_module.run_dataset_workflow(
            "customers.csv",
            persist_raw=True,
        )
    )

    assert (
        result
        == "workflow-result"
    )

    assert (
        received["source"]
        == "customers.csv"
    )

    assert (
        received["persist_raw"]
        is True
    )


def test_workflow_exposes_failing_stage(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        workflow_module,
        "profile_dataset",
        lambda dataframe: (
            {"basic_info": {}}
        ),
    )

    def fail_catalog(
        metadata: dict,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        workflow_module,
        "register_ingestion",
        fail_catalog,
    )

    with pytest.raises(
        DatasetWorkflowError,
    ) as exc_info:
        workflow_module.continue_dataset_workflow(
            build_ingestion_result()
        )

    assert (
        exc_info.value.stage
        == "CATALOG_REGISTRATION"
    )

    assert (
        "database unavailable"
        in str(
            exc_info.value
        )
    )


def test_empty_dataframe_is_rejected():
    ingestion_result = (
        build_ingestion_result()
    )

    ingestion_result.dataframe = (
        pd.DataFrame()
    )

    with pytest.raises(
        DatasetWorkflowError,
    ) as exc_info:
        workflow_module.continue_dataset_workflow(
            ingestion_result
        )

    assert (
        exc_info.value.stage
        == "INGESTION_RESULT"
    )