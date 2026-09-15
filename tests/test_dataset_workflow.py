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


def capture_operational_events(
    monkeypatch: pytest.MonkeyPatch,
) -> list[dict]:
    events: list[dict] = []

    def fake_emit_operational_event(
        **kwargs,
    ):
        events.append(
            kwargs
        )

        return None

    monkeypatch.setattr(
        workflow_module,
        "emit_operational_event",
        fake_emit_operational_event,
    )

    return events


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

    def fake_get_active_contract(
        catalog_id: int,
    ):
        assert catalog_id == 1
        return None

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
        "get_active_data_contract",
        fake_get_active_contract,
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


def test_compatible_data_contract_allows_workflow(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = configure_successful_workflow(
        monkeypatch
    )

    active_contract = {
        "contract_id": 11,
        "catalog_id": 1,
        "contract_version": 2,
        "contract_name": "customers",
        "enforcement_mode": "BLOCK",
        "is_active": True,
        "columns": [
            {
                "column_name": "customer_id",
                "expected_type": "NUMERIC",
                "is_required": True,
                "is_nullable": False,
            },
            {
                "column_name": "age",
                "expected_type": "NUMERIC",
                "is_required": True,
                "is_nullable": False,
            },
        ],
    }

    monkeypatch.setattr(
        workflow_module,
        "get_active_data_contract",
        lambda catalog_id: active_contract,
    )

    monkeypatch.setattr(
        workflow_module,
        "validate_contract",
        lambda dataframe, columns: FakeResult(
            {
                "status": "COMPATIBLE",
                "is_compatible": True,
                "missing_required_count": 0,
                "unexpected_column_count": 0,
                "type_mismatch_count": 0,
                "nullability_violation_count": 0,
                "violation_count": 0,
                "violations": [],
            }
        ),
    )

    def fake_save_contract_validation(
        *,
        contract_id: int,
        catalog_id: int,
        version_id: int,
        validation: dict,
    ) -> dict:
        calls.append(
            "contract_persist"
        )

        assert contract_id == 11
        assert catalog_id == 1
        assert version_id == 4
        assert (
            validation["status"]
            == "COMPATIBLE"
        )

        return {
            "contract_validation_id": 31,
            "contract_id": 11,
            "catalog_id": 1,
            "version_id": 4,
            "validation_status": (
                "COMPATIBLE"
            ),
            "violation_count": 0,
            "violations": [],
        }

    monkeypatch.setattr(
        workflow_module,
        "save_contract_validation",
        fake_save_contract_validation,
    )

    result = (
        workflow_module.continue_dataset_workflow(
            build_ingestion_result()
        )
    )

    assert (
        result.data_contract[
            "contract_id"
        ]
        == 11
    )

    assert (
        result.contract_validation[
            "validation_status"
        ]
        == "COMPATIBLE"
    )

    assert "contract_persist" in calls
    assert "validation_gate" in calls

    summary = result.summary()

    assert summary[
        "contract_id"
    ] == 11

    assert summary[
        "contract_version"
    ] == 2

    assert (
        summary[
            "contract_validation_status"
        ]
        == "COMPATIBLE"
    )


def test_breaking_block_contract_stops_workflow(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = configure_successful_workflow(
        monkeypatch
    )

    events = capture_operational_events(
        monkeypatch
    )

    active_contract = {
        "contract_id": 12,
        "catalog_id": 1,
        "contract_version": 3,
        "contract_name": "customers",
        "enforcement_mode": "BLOCK",
        "is_active": True,
        "columns": [],
    }

    monkeypatch.setattr(
        workflow_module,
        "get_active_data_contract",
        lambda catalog_id: active_contract,
    )

    monkeypatch.setattr(
        workflow_module,
        "validate_contract",
        lambda dataframe, columns: FakeResult(
            {
                "status": "BREAKING",
                "is_compatible": False,
                "missing_required_count": 1,
                "unexpected_column_count": 0,
                "type_mismatch_count": 0,
                "nullability_violation_count": 0,
                "violation_count": 1,
                "violations": [
                    {
                        "violation_type": (
                            "MISSING_REQUIRED_COLUMN"
                        ),
                        "column_name": "email",
                        "expected_value": "present",
                        "actual_value": "missing",
                        "message": (
                            "Required column is missing."
                        ),
                    }
                ],
            }
        ),
    )

    def fake_save_contract_validation(
        **kwargs,
    ):
        calls.append(
            "contract_persist"
        )

        return {
            "contract_validation_id": 32,
            "validation_status": (
                "BREAKING"
            ),
        }

    monkeypatch.setattr(
        workflow_module,
        "save_contract_validation",
        fake_save_contract_validation,
    )

    with pytest.raises(
        DatasetWorkflowError
    ) as exc_info:
        workflow_module.continue_dataset_workflow(
            build_ingestion_result()
        )

    assert (
        exc_info.value.stage
        == "DATA_CONTRACT_GATE"
    )

    assert "contract_persist" in calls

    assert (
        "validation_gate"
        not in calls
    )

    assert len(events) == 1

    assert (
        events[0]["event_type"]
        == "DATA_CONTRACT_BREAKING"
    )

    assert (
        events[0]["severity"]
        == "ERROR"
    )

    assert (
        events[0]["reference_id"]
        == 32
    )

    assert (
        events[0]["event_stage"]
        == "DATA_CONTRACT_GATE"
    )


def test_breaking_warn_contract_continues_workflow(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = configure_successful_workflow(
        monkeypatch
    )

    events = capture_operational_events(
        monkeypatch
    )

    active_contract = {
        "contract_id": 13,
        "catalog_id": 1,
        "contract_version": 4,
        "contract_name": "customers",
        "enforcement_mode": "WARN",
        "is_active": True,
        "columns": [],
    }

    monkeypatch.setattr(
        workflow_module,
        "get_active_data_contract",
        lambda catalog_id: active_contract,
    )

    monkeypatch.setattr(
        workflow_module,
        "validate_contract",
        lambda dataframe, columns: FakeResult(
            {
                "status": "BREAKING",
                "is_compatible": False,
                "missing_required_count": 0,
                "unexpected_column_count": 1,
                "type_mismatch_count": 0,
                "nullability_violation_count": 0,
                "violation_count": 1,
                "violations": [
                    {
                        "violation_type": (
                            "UNEXPECTED_COLUMN"
                        ),
                        "column_name": "legacy",
                        "expected_value": (
                            "not defined"
                        ),
                        "actual_value": "TEXT",
                        "message": (
                            "Unexpected column."
                        ),
                    }
                ],
            }
        ),
    )

    def fake_save_contract_validation(
        **kwargs,
    ):
        calls.append(
            "contract_persist"
        )

        return {
            "contract_validation_id": 33,
            "validation_status": (
                "BREAKING"
            ),
        }

    monkeypatch.setattr(
        workflow_module,
        "save_contract_validation",
        fake_save_contract_validation,
    )

    result = (
        workflow_module.continue_dataset_workflow(
            build_ingestion_result()
        )
    )

    assert "contract_persist" in calls
    assert "validation_gate" in calls

    assert (
        result.contract_validation[
            "validation_status"
        ]
        == "BREAKING"
    )

    assert len(events) == 1

    assert (
        events[0]["event_type"]
        == "DATA_CONTRACT_BREAKING"
    )

    assert (
        events[0]["severity"]
        == "WARNING"
    )

    assert (
        events[0]["reference_id"]
        == 33
    )

    assert (
        events[0]["event_stage"]
        == "DATA_CONTRACT_GATE"
    )



def test_rejected_validation_and_governance_emit_operational_events(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = configure_successful_workflow(
        monkeypatch
    )

    events = capture_operational_events(
        monkeypatch
    )

    def fake_validation_gate(
        *,
        df: pd.DataFrame,
        ingestion_metadata: dict,
    ) -> FakeResult:
        calls.append(
            "validation_gate"
        )

        assert len(df) == 2

        return FakeResult(
            {
                "ingestion_id": "ingestion-1",
                "status": "REJECTED",
                "policy_version": "1.0",
                "validated_at": (
                    "2026-09-02T00:01:00+00:00"
                ),
                "total_issues": 1,
                "high_issues": 1,
                "medium_issues": 0,
                "low_issues": 0,
                "blocking_issue_count": 1,
                "blocking_issues": [
                    {
                        "issue_type": (
                            "MISSING_VALUE"
                        ),
                        "severity": "High",
                    }
                ],
                "artifact_path": (
                    "data/quarantine/"
                    "customers.csv"
                ),
                "validation_metadata_path": (
                    "data/quarantine/"
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
            == "REJECTED"
        )

        return {
            "validation_id": 41,
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

        assert (
            validation_result["status"]
            == "REJECTED"
        )

        return {
            "governance_result": FakeResult(
                {
                    "decision": "REJECTED",
                    "reason": (
                        "Validation Gate "
                        "rejected dataset."
                    ),
                    "promotion_eligible": False,
                    "policy_version": "1.0",
                    "validation_status": (
                        "REJECTED"
                    ),
                    "trust_score": 55.0,
                    "privacy_status": "LOW",
                    "blocking_issue_count": 1,
                }
            ),
            "quality_report": {
                "summary": {
                    "total_issues": 1,
                }
            },
            "trust_score_report": {
                "overall_score": 55.0,
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
            == "REJECTED"
        )

        assert (
            validation_registration[
                "validation_id"
            ]
            == 41
        )

        return {
            "governance_id": 52,
            "catalog_id": 1,
            "version_id": 4,
            "validation_id": 41,
            "decision": "REJECTED",
            "promotion_eligible": False,
        }

    def fake_apply_lifecycle(
        catalog_registration: dict,
        validation_result: dict,
    ) -> dict:
        calls.append(
            "lifecycle"
        )

        assert (
            validation_result["status"]
            == "REJECTED"
        )

        return {
            "catalog_id": 1,
            "version_id": 4,
            "version_number": 4,
            "previous_state": "NEW",
            "lifecycle_state": (
                "QUARANTINED"
            ),
            "changed": True,
        }

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

    result = (
        workflow_module.continue_dataset_workflow(
            build_ingestion_result()
        )
    )

    assert (
        result.validation_result[
            "status"
        ]
        == "REJECTED"
    )

    assert (
        result.governance_result[
            "decision"
        ]
        == "REJECTED"
    )

    assert (
        result.lifecycle_result[
            "lifecycle_state"
        ]
        == "QUARANTINED"
    )

    assert len(events) == 2

    assert [
        event["event_type"]
        for event in events
    ] == [
        "VALIDATION_REJECTED",
        "GOVERNANCE_REJECTED",
    ]

    validation_event = events[0]

    assert (
        validation_event["severity"]
        == "ERROR"
    )

    assert (
        validation_event["event_stage"]
        == "VALIDATION_GATE"
    )

    assert (
        validation_event["reference_id"]
        == 41
    )

    assert (
        validation_event["version_id"]
        == 4
    )

    governance_event = events[1]

    assert (
        governance_event["severity"]
        == "ERROR"
    )

    assert (
        governance_event["event_stage"]
        == "GOVERNANCE"
    )

    assert (
        governance_event["reference_id"]
        == 52
    )

    assert (
        governance_event["detail"][
            "validation_id"
        ]
        == 41
    )


def test_data_contract_lookup_failure_exposes_stage(
    monkeypatch: pytest.MonkeyPatch,
):
    configure_successful_workflow(
        monkeypatch
    )

    def fail_lookup(
        catalog_id: int,
    ):
        raise RuntimeError(
            "contract database unavailable"
        )

    monkeypatch.setattr(
        workflow_module,
        "get_active_data_contract",
        fail_lookup,
    )

    with pytest.raises(
        DatasetWorkflowError
    ) as exc_info:
        workflow_module.continue_dataset_workflow(
            build_ingestion_result()
        )

    assert (
        exc_info.value.stage
        == "DATA_CONTRACT_LOOKUP"
    )

    assert (
        "contract database unavailable"
        in str(exc_info.value)
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