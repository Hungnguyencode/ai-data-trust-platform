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
        "version_id": 3,
        "version_number": 3,
        "file_name": "sample_customers.csv",
        "content_sha256": "a" * 64,
        "lifecycle_state": lifecycle_state,
        "raw_path": "data/raw/sample_customers.csv",
    }


def test_lineage_timeline_is_chronological():
    timeline = build_lineage_timeline(
        ingestions=[
            {
                "ingestion_event_id": 5,
                "ingested_at": (
                    "2026-09-01T08:20:00+00:00"
                ),
                "raw_path": "raw.csv",
                "is_new_version": True,
            }
        ],
        validations=[
            {
                "validation_id": 4,
                "validation_status": "ACCEPTED",
                "validated_at": (
                    "2026-09-01T08:21:00+00:00"
                ),
                "policy_version": "1.0",
                "high_issues": 0,
                "blocking_issue_count": 0,
                "artifact_path": "processed.csv",
            }
        ],
        lifecycle_events=[
            {
                "lifecycle_event_id": 5,
                "from_state": "VALIDATED",
                "to_state": "ACTIVE",
                "reason": (
                    "Version promoted to ACTIVE."
                ),
                "changed_at": (
                    "2026-09-01T08:22:00+00:00"
                ),
            }
        ],
    )

    assert [
        event["event_type"]
        for event in timeline
    ] == [
        "INGESTION",
        "VALIDATION",
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
        timeline[0]["event_status"]
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
        timeline[0]["event_status"]
        == "REINGESTED"
    )


def test_validated_version_is_promotion_eligible():
    lineage = build_version_lineage(
        version=build_version(
            "VALIDATED"
        ),
        ingestions=[],
        validations=[],
        lifecycle_events=[],
    )

    assert (
        lineage["summary"][
            "promotion_eligible"
        ]
        is True
    )

    assert (
        lineage["summary"][
            "is_active"
        ]
        is False
    )


def test_active_version_is_not_promotion_eligible():
    lineage = build_version_lineage(
        version=build_version(
            "ACTIVE"
        ),
        ingestions=[],
        validations=[],
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


def test_lineage_summary_uses_latest_validation():
    lineage = build_version_lineage(
        version=build_version(),
        ingestions=[],
        validations=[
            {
                "validation_id": 1,
                "validation_status": "REJECTED",
                "validated_at": (
                    "2026-09-01T08:00:00+00:00"
                ),
                "policy_version": "1.0",
            },
            {
                "validation_id": 2,
                "validation_status": "ACCEPTED",
                "validated_at": (
                    "2026-09-01T09:00:00+00:00"
                ),
                "policy_version": "1.0",
            },
        ],
        lifecycle_events=[],
    )

    assert (
        lineage["summary"][
            "latest_validation_status"
        ]
        == "ACCEPTED"
    )

    assert (
        lineage["summary"][
            "validation_count"
        ]
        == 2
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
            lifecycle_events=[],
        )