from __future__ import annotations

import pandas as pd
import pytest

import src.assistant.platform_context as platform_context


@pytest.mark.parametrize(
    "catalog_id",
    [
        0,
        -1,
        True,
        "1",
    ],
)
def test_build_platform_context_rejects_invalid_catalog_id(
    catalog_id,
):
    with pytest.raises(
        ValueError,
        match="catalog_id must be a positive integer",
    ):
        platform_context.build_platform_context(
            catalog_id
        )


def test_build_platform_context_collects_platform_evidence(
    monkeypatch,
):
    monkeypatch.setattr(
        platform_context,
        "get_dataset_version_history",
        lambda catalog_id: pd.DataFrame(
            [
                {
                    "catalog_id": catalog_id,
                    "version_id": 11,
                    "version_number": 1,
                },
                {
                    "catalog_id": catalog_id,
                    "version_id": 13,
                    "version_number": 3,
                },
            ]
        ),
    )

    monkeypatch.setattr(
        platform_context,
        "get_active_data_contract",
        lambda catalog_id: {
            "contract_id": 5,
            "catalog_id": catalog_id,
            "contract_version": 2,
            "enforcement_mode": "BLOCK",
        },
    )

    monkeypatch.setattr(
        platform_context,
        "get_validation_history",
        lambda catalog_id, limit=10: pd.DataFrame(
            [
                {
                    "catalog_id": catalog_id,
                    "version_id": 11,
                    "validation_id": 22,
                    "status": "ACCEPTED",
                },
                {
                    "catalog_id": catalog_id,
                    "version_id": 13,
                    "validation_id": 21,
                    "status": "REJECTED",
                },
            ]
        ),
    )

    monkeypatch.setattr(
        platform_context,
        "get_governance_history",
        lambda catalog_id, limit=10: pd.DataFrame(
            [
                {
                    "catalog_id": catalog_id,
                    "version_id": 11,
                    "governance_id": 32,
                    "decision": "APPROVED",
                },
                {
                    "catalog_id": catalog_id,
                    "version_id": 13,
                    "governance_id": 31,
                    "decision": "REJECTED",
                },
            ]
        ),
    )

    monkeypatch.setattr(
        platform_context,
        "get_freshness_history",
        lambda catalog_id, limit=10: pd.DataFrame(
            [
                {
                    "catalog_id": catalog_id,
                    "freshness_check_id": 41,
                    "freshness_status": "STALE",
                    "checked_at": pd.Timestamp(
                        "2026-09-18 01:00:00"
                    ),
                }
            ]
        ),
    )

    monkeypatch.setattr(
        platform_context,
        "get_volume_history",
        lambda catalog_id, limit=10: pd.DataFrame(
            [
                {
                    "catalog_id": catalog_id,
                    "volume_check_id": 51,
                    "volume_status": "NORMAL",
                }
            ]
        ),
    )

    monkeypatch.setattr(
        platform_context,
        "get_pipeline_run_history",
        lambda limit=100: pd.DataFrame(
            [
                {
                    "pipeline_run_id": 61,
                    "catalog_id": 1,
                    "run_status": "FAILED",
                },
                {
                    "pipeline_run_id": 62,
                    "catalog_id": 2,
                    "run_status": "SUCCESS",
                },
            ]
        ),
    )

    monkeypatch.setattr(
        platform_context,
        "get_operational_event_history",
        lambda limit=100: pd.DataFrame(
            [
                {
                    "operational_event_id": 71,
                    "catalog_id": 1,
                    "event_type": (
                        "DATASET_FRESHNESS_BREACH"
                    ),
                },
                {
                    "operational_event_id": 72,
                    "catalog_id": 2,
                    "event_type": (
                        "DATASET_VOLUME_BREACH"
                    ),
                },
            ]
        ),
    )

    requested_versions: list[int] = []

    def fake_get_version_lineage(
        version_id: int,
    ):
        requested_versions.append(
            version_id
        )

        return {
            "summary": {
                "version_id": version_id,
                "lifecycle_state": "ACTIVE",
            },
            "timeline": [],
        }

    monkeypatch.setattr(
        platform_context,
        "get_version_lineage",
        fake_get_version_lineage,
    )

    result = (
        platform_context.build_platform_context(
            1
        )
    )

    assert result["catalog_id"] == 1

    assert (
        result["dataset"]["latest_version_id"]
        == 13
    )

    assert requested_versions == [13]

    assert (
        result["data_contract"]["active"][
            "contract_id"
        ]
        == 5
    )

    assert (
        result["validation"]["latest"]["status"]
        == "ACCEPTED"
    )

    assert (
        result["validation"]["latest_version"][
            "version_id"
        ]
        == 13
    )

    assert (
        result["validation"]["latest_version"][
            "status"
        ]
        == "REJECTED"
    )

    assert (
        result["governance"]["latest"]["decision"]
        == "APPROVED"
    )

    assert (
        result["governance"]["latest_version"][
            "version_id"
        ]
        == 13
    )

    assert (
        result["governance"]["latest_version"][
            "decision"
        ]
        == "REJECTED"
    )

    assert (
        result["observability"]["freshness"][
            "latest"
        ]["freshness_status"]
        == "STALE"
    )

    assert (
        result["observability"]["freshness"][
            "latest"
        ]["checked_at"]
        == "2026-09-18T01:00:00"
    )

    assert (
        result["observability"]["volume"][
            "latest"
        ]["volume_status"]
        == "NORMAL"
    )

    assert len(
        result["operations"]["pipeline_runs"]
    ) == 1

    assert (
        result["operations"]["pipeline_runs"][0][
            "pipeline_run_id"
        ]
        == 61
    )

    assert len(
        result["operations"][
            "operational_events"
        ]
    ) == 1

    summary = result["evidence_summary"]

    assert summary["version_count"] == 2
    assert summary["has_active_contract"] is True
    assert summary["validation_count"] == 2
    assert summary["governance_count"] == 2
    assert summary["freshness_check_count"] == 1
    assert summary["volume_check_count"] == 1
    assert summary["pipeline_run_count"] == 1
    assert summary["operational_event_count"] == 1
    assert summary["has_lineage"] is True


def test_build_platform_context_handles_missing_evidence(
    monkeypatch,
):
    empty_frame = pd.DataFrame()

    monkeypatch.setattr(
        platform_context,
        "get_dataset_version_history",
        lambda catalog_id: empty_frame,
    )

    monkeypatch.setattr(
        platform_context,
        "get_active_data_contract",
        lambda catalog_id: None,
    )

    monkeypatch.setattr(
        platform_context,
        "get_validation_history",
        lambda catalog_id, limit=10: empty_frame,
    )

    monkeypatch.setattr(
        platform_context,
        "get_governance_history",
        lambda catalog_id, limit=10: empty_frame,
    )

    monkeypatch.setattr(
        platform_context,
        "get_freshness_history",
        lambda catalog_id, limit=10: empty_frame,
    )

    monkeypatch.setattr(
        platform_context,
        "get_volume_history",
        lambda catalog_id, limit=10: empty_frame,
    )

    monkeypatch.setattr(
        platform_context,
        "get_pipeline_run_history",
        lambda limit=100: empty_frame,
    )

    monkeypatch.setattr(
        platform_context,
        "get_operational_event_history",
        lambda limit=100: empty_frame,
    )

    def fail_if_lineage_called(
        version_id: int,
    ):
        raise AssertionError(
            "Lineage must not be loaded "
            "without a dataset version."
        )

    monkeypatch.setattr(
        platform_context,
        "get_version_lineage",
        fail_if_lineage_called,
    )

    result = (
        platform_context.build_platform_context(
            1
        )
    )

    assert (
        result["dataset"]["latest_version_id"]
        is None
    )

    assert result["dataset"]["lineage"] is None

    assert (
        result["data_contract"]["active"]
        is None
    )

    assert result["validation"]["latest"] is None
    assert result["governance"]["latest"] is None

    assert (
        result["observability"]["freshness"][
            "latest"
        ]
        is None
    )

    assert (
        result["observability"]["volume"][
            "latest"
        ]
        is None
    )

    assert (
        result["operations"]["pipeline_runs"]
        == []
    )

    assert (
        result["operations"][
            "operational_events"
        ]
        == []
    )

    summary = result["evidence_summary"]

    assert summary["version_count"] == 0
    assert summary["has_active_contract"] is False
    assert summary["has_lineage"] is False