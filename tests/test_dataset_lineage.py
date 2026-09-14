from __future__ import annotations

import pytest

from src.lineage.dataset_lineage import (
    build_lineage_timeline,
    build_version_lineage,
)


def build_version(
    lifecycle_state: str = "VALIDATED",
) -> dict:
    return {
        "catalog_id": 1,
        "version_id": 4,
        "version_number": 4,
        "file_name": (
            "sample_customers.csv"
        ),
        "content_sha256": (
            "a" * 64
        ),
        "lifecycle_state": (
            lifecycle_state
        ),
        "raw_path": (
            "data/raw/"
            "sample_customers.csv"
        ),
    }


def build_validation(
    *,
    validation_id: int = 7,
    validated_at: str = (
        "2026-09-01T08:21:00+00:00"
    ),
    status: str = "ACCEPTED",
) -> dict:
    return {
        "validation_id": (
            validation_id
        ),
        "validation_status": (
            status
        ),
        "validated_at": (
            validated_at
        ),
        "policy_version": "1.0",
        "high_issues": 0,
        "blocking_issue_count": 0,
        "artifact_path": (
            "processed.csv"
        ),
    }


def build_contract_validation(
    *,
    contract_validation_id: int = 11,
    contract_id: int = 3,
    contract_version: int = 1,
    validation_status: str = "COMPATIBLE",
    enforcement_mode: str = "BLOCK",
    violation_count: int = 0,
    validated_at: str = (
        "2026-09-01T08:20:30+00:00"
    ),
) -> dict:
    return {
        "contract_validation_id": (
            contract_validation_id
        ),
        "contract_id": contract_id,
        "contract_version": (
            contract_version
        ),
        "validation_status": (
            validation_status
        ),
        "enforcement_mode": (
            enforcement_mode
        ),
        "violation_count": (
            violation_count
        ),
        "validated_at": validated_at,
    }


def build_governance(
    *,
    governance_id: int = 2,
    validation_id: int = 7,
    decision: str = "APPROVED",
    promotion_eligible: bool = True,
    created_at: str = (
        "2026-09-01T08:21:30+00:00"
    ),
) -> dict:
    return {
        "governance_id": (
            governance_id
        ),
        "validation_id": (
            validation_id
        ),
        "policy_version": "1.0",
        "decision": decision,
        "reason": (
            "Governance test decision."
        ),
        "promotion_eligible": (
            promotion_eligible
        ),
        "trust_score": 95.0,
        "validation_status": (
            "ACCEPTED"
        ),
        "privacy_status": "LOW",
        "blocking_issue_count": 0,
        "created_at": (
            created_at
        ),
    }


def test_lineage_timeline_is_chronological():
    timeline = build_lineage_timeline(
        ingestions=[
            {
                "ingestion_event_id": 8,
                "ingested_at": (
                    "2026-09-01T08:20:00+00:00"
                ),
                "raw_path": "raw.csv",
                "is_new_version": True,
            }
        ],
        contract_validations=[
            build_contract_validation()
        ],
        validations=[
            build_validation()
        ],
        governance_decisions=[
            build_governance()
        ],
        lifecycle_events=[
            {
                "lifecycle_event_id": 8,
                "from_state": (
                    "VALIDATED"
                ),
                "to_state": "ACTIVE",
                "reason": (
                    "Version promoted."
                ),
                "changed_at": (
                    "2026-09-01T08:22:00+00:00"
                ),
            }
        ],
    )

    assert [
        event[
            "event_type"
        ]
        for event in timeline
    ] == [
        "INGESTION",
        "DATA_CONTRACT",
        "VALIDATION",
        "GOVERNANCE",
        "LIFECYCLE",
    ]


def test_same_timestamp_uses_pipeline_stage_order():
    occurred_at = (
        "2026-09-01T08:20:00+00:00"
    )

    timeline = build_lineage_timeline(
        ingestions=[
            {
                "ingestion_event_id": 1,
                "ingested_at": occurred_at,
                "is_new_version": True,
            }
        ],
        contract_validations=[
            build_contract_validation(
                validated_at=occurred_at
            )
        ],
        validations=[
            build_validation(
                validated_at=occurred_at
            )
        ],
        governance_decisions=[
            build_governance(
                created_at=occurred_at
            )
        ],
        lifecycle_events=[
            {
                "lifecycle_event_id": 1,
                "from_state": "NEW",
                "to_state": "VALIDATED",
                "changed_at": occurred_at,
            }
        ],
    )

    assert [
        event["event_type"]
        for event in timeline
    ] == [
        "INGESTION",
        "DATA_CONTRACT",
        "VALIDATION",
        "GOVERNANCE",
        "LIFECYCLE",
    ]


def test_new_ingestion_is_marked_as_new_version():
    timeline = build_lineage_timeline(
        ingestions=[
            {
                "ingestion_event_id": 1,
                "ingested_at": (
                    "2026-09-01T08:00:00+00:00"
                ),
                "is_new_version": True,
            }
        ],
        validations=[],
        lifecycle_events=[],
    )

    assert (
        timeline[0][
            "event_status"
        ]
        == "NEW_VERSION"
    )


def test_reingestion_is_marked_as_reingested():
    timeline = build_lineage_timeline(
        ingestions=[
            {
                "ingestion_event_id": 2,
                "ingested_at": (
                    "2026-09-01T09:00:00+00:00"
                ),
                "is_new_version": False,
            }
        ],
        validations=[],
        lifecycle_events=[],
    )

    assert (
        timeline[0][
            "event_status"
        ]
        == "REINGESTED"
    )


def test_governance_event_contains_evidence():
    timeline = build_lineage_timeline(
        ingestions=[],
        validations=[],
        governance_decisions=[
            build_governance()
        ],
        lifecycle_events=[],
    )

    assert (
        timeline[0][
            "event_type"
        ]
        == "GOVERNANCE"
    )

    assert (
        timeline[0][
            "event_status"
        ]
        == "APPROVED"
    )

    assert "trust_score=95.0" in (
        timeline[0]["detail"]
    )

    assert "privacy=LOW" in (
        timeline[0]["detail"]
    )


def test_data_contract_event_contains_evidence():
    timeline = build_lineage_timeline(
        ingestions=[],
        contract_validations=[
            build_contract_validation(
                validation_status="BREAKING",
                enforcement_mode="BLOCK",
                violation_count=3,
            )
        ],
        validations=[],
        governance_decisions=[],
        lifecycle_events=[],
    )

    event = timeline[0]

    assert event["event_type"] == "DATA_CONTRACT"
    assert event["event_status"] == "BREAKING"
    assert event["reference_id"] == 11

    assert "contract_id=3" in event["detail"]
    assert "contract_version=1" in event["detail"]
    assert "enforcement=BLOCK" in event["detail"]
    assert "violations=3" in event["detail"]


def test_lineage_summary_uses_latest_contract_validation():
    lineage = build_version_lineage(
        version=build_version(),
        ingestions=[],
        contract_validations=[
            build_contract_validation(
                contract_validation_id=10,
                contract_id=2,
                contract_version=1,
                validation_status="BREAKING",
                enforcement_mode="WARN",
                violation_count=4,
                validated_at=(
                    "2026-09-01T08:00:00+00:00"
                ),
            ),
            build_contract_validation(
                contract_validation_id=12,
                contract_id=3,
                contract_version=2,
                validation_status="COMPATIBLE",
                enforcement_mode="BLOCK",
                violation_count=0,
                validated_at=(
                    "2026-09-01T09:00:00+00:00"
                ),
            ),
        ],
        validations=[],
        governance_decisions=[],
        lifecycle_events=[],
    )

    summary = lineage["summary"]

    assert summary["contract_validation_count"] == 2
    assert (
        summary["latest_contract_validation_id"]
        == 12
    )
    assert summary["latest_contract_id"] == 3
    assert summary["latest_contract_version"] == 2
    assert (
        summary["latest_contract_validation_status"]
        == "COMPATIBLE"
    )
    assert (
        summary["latest_contract_enforcement_mode"]
        == "BLOCK"
    )
    assert (
        summary["latest_contract_violation_count"]
        == 0
    )

    assert len(lineage["contract_validations"]) == 2


def test_validated_and_approved_version_can_promote():
    lineage = build_version_lineage(
        version=build_version(
            "VALIDATED"
        ),
        ingestions=[],
        validations=[
            build_validation()
        ],
        governance_decisions=[
            build_governance()
        ],
        lifecycle_events=[],
    )

    summary = lineage[
        "summary"
    ]

    assert (
        summary[
            "lifecycle_eligible"
        ]
        is True
    )

    assert (
        summary[
            "governance_approved"
        ]
        is True
    )

    assert (
        summary[
            "promotion_eligible"
        ]
        is True
    )


def test_validated_without_governance_cannot_promote():
    lineage = build_version_lineage(
        version=build_version(
            "VALIDATED"
        ),
        ingestions=[],
        validations=[
            build_validation()
        ],
        governance_decisions=[],
        lifecycle_events=[],
    )

    summary = lineage[
        "summary"
    ]

    assert (
        summary[
            "lifecycle_eligible"
        ]
        is True
    )

    assert (
        summary[
            "governance_approved"
        ]
        is False
    )

    assert (
        summary[
            "promotion_eligible"
        ]
        is False
    )


def test_review_required_cannot_promote():
    lineage = build_version_lineage(
        version=build_version(
            "VALIDATED"
        ),
        ingestions=[],
        validations=[
            build_validation()
        ],
        governance_decisions=[
            build_governance(
                decision=(
                    "REVIEW_REQUIRED"
                ),
                promotion_eligible=False,
            )
        ],
        lifecycle_events=[],
    )

    assert (
        lineage["summary"][
            "governance_approved"
        ]
        is False
    )

    assert (
        lineage["summary"][
            "promotion_eligible"
        ]
        is False
    )


def test_active_version_is_not_promotion_eligible():
    lineage = build_version_lineage(
        version=build_version(
            "ACTIVE"
        ),
        ingestions=[],
        validations=[
            build_validation()
        ],
        governance_decisions=[
            build_governance()
        ],
        lifecycle_events=[],
    )

    assert (
        lineage["summary"][
            "promotion_eligible"
        ]
        is False
    )

    assert (
        lineage["summary"][
            "is_active"
        ]
        is True
    )


def test_lineage_summary_uses_governance_for_latest_validation():
    lineage = build_version_lineage(
        version=build_version(),
        ingestions=[],
        validations=[
            build_validation(
                validation_id=1,
                validated_at=(
                    "2026-09-01T08:00:00+00:00"
                ),
            ),
            build_validation(
                validation_id=2,
                validated_at=(
                    "2026-09-01T09:00:00+00:00"
                ),
            ),
        ],
        governance_decisions=[
            build_governance(
                governance_id=1,
                validation_id=1,
                decision="REJECTED",
                promotion_eligible=False,
                created_at=(
                    "2026-09-01T08:01:00+00:00"
                ),
            ),
            build_governance(
                governance_id=2,
                validation_id=2,
                decision="APPROVED",
                promotion_eligible=True,
                created_at=(
                    "2026-09-01T09:01:00+00:00"
                ),
            ),
        ],
        lifecycle_events=[],
    )

    summary = lineage[
        "summary"
    ]

    assert (
        summary[
            "latest_validation_id"
        ]
        == 2
    )

    assert (
        summary[
            "latest_governance_id"
        ]
        == 2
    )

    assert (
        summary[
            "latest_governance_decision"
        ]
        == "APPROVED"
    )

    assert (
        summary[
            "promotion_eligible"
        ]
        is True
    )


def test_old_governance_does_not_approve_new_validation():
    lineage = build_version_lineage(
        version=build_version(),
        ingestions=[],
        validations=[
            build_validation(
                validation_id=1,
                validated_at=(
                    "2026-09-01T08:00:00+00:00"
                ),
            ),
            build_validation(
                validation_id=2,
                validated_at=(
                    "2026-09-01T09:00:00+00:00"
                ),
            ),
        ],
        governance_decisions=[
            build_governance(
                governance_id=1,
                validation_id=1,
                decision="APPROVED",
                promotion_eligible=True,
            )
        ],
        lifecycle_events=[],
    )

    summary = lineage[
        "summary"
    ]

    assert (
        summary[
            "latest_validation_id"
        ]
        == 2
    )

    assert (
        summary[
            "latest_governance_decision"
        ]
        is None
    )

    assert (
        summary[
            "governance_approved"
        ]
        is False
    )

    assert (
        summary[
            "promotion_eligible"
        ]
        is False
    )


def test_missing_required_version_field_is_rejected():
    version = build_version()

    version.pop(
        "content_sha256"
    )

    with pytest.raises(
        ValueError,
        match="content_sha256",
    ):
        build_version_lineage(
            version=version,
            ingestions=[],
            validations=[],
            governance_decisions=[],
            lifecycle_events=[],
        )