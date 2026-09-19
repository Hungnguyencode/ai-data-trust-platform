from __future__ import annotations

import pytest

from src.assistant.platform_explanation import (
    explain_platform_diagnosis,
)


def _action_required_diagnosis() -> dict:
    return {
        "catalog_id": 1,
        "latest_version_id": 3,
        "overall_state": "ACTION_REQUIRED",
        "findings": [
            {
                "code": "VALIDATION_REJECTED",
                "category": "VALIDATION",
                "severity": "HIGH",
                "message": (
                    "The latest dataset version "
                    "was rejected by the "
                    "Validation Gate."
                ),
                "evidence": {
                    "version_id": 3,
                },
            },
            {
                "code": "FRESHNESS_STALE",
                "category": "FRESHNESS",
                "severity": "WARNING",
                "message": (
                    "The dataset is currently "
                    "stale."
                ),
                "evidence": {
                    "age_minutes": 2000,
                },
            },
            {
                "code": "VOLUME_NORMAL",
                "category": "VOLUME",
                "severity": "INFO",
                "message": (
                    "The latest ingestion volume "
                    "is within configured "
                    "thresholds."
                ),
                "evidence": {},
            },
        ],
        "recommended_actions": [
            {
                "code": (
                    "INVESTIGATE_FRESHNESS"
                ),
                "priority": 50,
                "action": (
                    "Investigate freshness."
                ),
                "reason": (
                    "Freshness exceeded the SLA."
                ),
            },
            {
                "code": (
                    "REMEDIATE_VALIDATION"
                ),
                "priority": 10,
                "action": (
                    "Inspect blocking "
                    "validation issues."
                ),
                "reason": (
                    "Validation rejected "
                    "the latest version."
                ),
            },
        ],
        "summary": {
            "finding_count": 3,
            "high_count": 1,
            "warning_count": 1,
            "info_count": 1,
            "action_count": 2,
        },
    }


@pytest.mark.parametrize(
    "diagnosis",
    [
        None,
        [],
        "bad",
    ],
)
def test_explanation_rejects_non_dictionary(
    diagnosis,
):
    with pytest.raises(
        ValueError,
        match=(
            "diagnosis must be "
            "a dictionary"
        ),
    ):
        explain_platform_diagnosis(
            diagnosis
        )


def test_explanation_rejects_invalid_catalog_id():
    diagnosis = (
        _action_required_diagnosis()
    )

    diagnosis["catalog_id"] = 0

    with pytest.raises(
        ValueError,
        match=(
            "diagnosis.catalog_id must "
            "be a positive integer"
        ),
    ):
        explain_platform_diagnosis(
            diagnosis
        )


def test_action_required_explanation():
    result = (
        explain_platform_diagnosis(
            _action_required_diagnosis()
        )
    )

    assert result["catalog_id"] == 1
    assert result["latest_version_id"] == 3

    assert (
        result["overall_state"]
        == "ACTION_REQUIRED"
    )

    assert (
        "requires action"
        in result["summary"]
    )

    assert (
        "VALIDATION_REJECTED"
        in result["explanation"]
    )

    assert (
        "FRESHNESS_STALE"
        in result["explanation"]
    )


def test_explanation_preserves_finding_sources():
    diagnosis = (
        _action_required_diagnosis()
    )

    result = (
        explain_platform_diagnosis(
            diagnosis
        )
    )

    expected_codes = [
        finding["code"]
        for finding in diagnosis[
            "findings"
        ]
    ]

    assert (
        result["source_finding_codes"]
        == expected_codes
    )


def test_explanation_sorts_actions_by_priority():
    result = (
        explain_platform_diagnosis(
            _action_required_diagnosis()
        )
    )

    assert (
        result["source_action_codes"]
        == [
            "REMEDIATE_VALIDATION",
            "INVESTIGATE_FRESHNESS",
        ]
    )

    validation_position = (
        result["explanation"].index(
            "REMEDIATE_VALIDATION"
        )
    )

    freshness_position = (
        result["explanation"].index(
            "INVESTIGATE_FRESHNESS"
        )
    )

    assert (
        validation_position
        < freshness_position
    )


def test_healthy_explanation_has_no_action_plan():
    diagnosis = {
        "catalog_id": 1,
        "latest_version_id": 3,
        "overall_state": "HEALTHY",
        "findings": [
            {
                "code": "VOLUME_NORMAL",
                "category": "VOLUME",
                "severity": "INFO",
                "message": (
                    "Volume is normal."
                ),
                "evidence": {},
            }
        ],
        "recommended_actions": [],
        "summary": {
            "finding_count": 1,
            "high_count": 0,
            "warning_count": 0,
            "info_count": 1,
            "action_count": 0,
        },
    }

    result = explain_platform_diagnosis(
        diagnosis
    )

    assert (
        result["overall_state"]
        == "HEALTHY"
    )

    assert (
        result["source_action_codes"]
        == []
    )

    assert (
        "No corrective action"
        in result["explanation"]
    )


def test_unknown_state_is_supported():
    diagnosis = {
        "catalog_id": 1,
        "latest_version_id": None,
        "overall_state": "UNKNOWN",
        "findings": [],
        "recommended_actions": [],
        "summary": {},
    }

    result = explain_platform_diagnosis(
        diagnosis
    )

    assert (
        result["overall_state"]
        == "UNKNOWN"
    )

    assert (
        "enough platform evidence"
        in result["summary"]
    )


def test_unrecognized_state_becomes_unknown():
    diagnosis = {
        "catalog_id": 1,
        "latest_version_id": 3,
        "overall_state": "MAGIC",
        "findings": [],
        "recommended_actions": [],
        "summary": {},
    }

    result = explain_platform_diagnosis(
        diagnosis
    )

    assert (
        result["overall_state"]
        == "UNKNOWN"
    )


def test_explanation_surfaces_trust_and_privacy_findings():
    diagnosis = {
        "catalog_id": 1,
        "latest_version_id": 3,
        "overall_state": "HEALTHY",
        "findings": [
            {
                "code": "TRUST_SCORE_RECORDED",
                "category": "TRUST_SCORE",
                "severity": "INFO",
                "message": (
                    "The latest dataset version "
                    "has persisted Data Trust Score "
                    "92.50."
                ),
                "evidence": {
                    "version_id": 3,
                    "governance_id": 21,
                    "trust_score": 92.5,
                },
            },
            {
                "code": "PRIVACY_STATUS_RECORDED",
                "category": "PRIVACY",
                "severity": "INFO",
                "message": (
                    "The latest dataset version "
                    "has persisted privacy status LOW."
                ),
                "evidence": {
                    "version_id": 3,
                    "governance_id": 21,
                    "privacy_status": "LOW",
                },
            },
        ],
        "recommended_actions": [],
        "summary": {
            "finding_count": 2,
            "high_count": 0,
            "warning_count": 0,
            "info_count": 2,
            "action_count": 0,
        },
    }

    result = explain_platform_diagnosis(
        diagnosis
    )

    assert "92.50" in result["explanation"]
    assert "privacy status LOW" in result["explanation"]

    assert (
        "TRUST_SCORE_RECORDED"
        in result["source_finding_codes"]
    )
    assert (
        "PRIVACY_STATUS_RECORDED"
        in result["source_finding_codes"]
    )

    assert result["overall_state"] == "HEALTHY"
    assert result["source_action_codes"] == []


def test_explanation_surfaces_persisted_quality_summary():
    diagnosis = {
        "catalog_id": 1,
        "latest_version_id": 3,
        "overall_state": "HEALTHY",
        "findings": [
            {
                "code": "QUALITY_SUMMARY_RECORDED",
                "category": "QUALITY",
                "severity": "INFO",
                "message": (
                    "The latest dataset version "
                    "has persisted quality summary: "
                    "4 total issues, 0 high, "
                    "3 medium, 1 low, and "
                    "0 blocking."
                ),
                "evidence": {
                    "version_id": 3,
                    "validation_id": 31,
                    "total_issues": 4,
                    "high_issues": 0,
                    "medium_issues": 3,
                    "low_issues": 1,
                    "blocking_issue_count": 0,
                },
            },
        ],
        "recommended_actions": [],
        "summary": {
            "finding_count": 1,
            "high_count": 0,
            "warning_count": 0,
            "info_count": 1,
            "action_count": 0,
        },
    }

    result = explain_platform_diagnosis(
        diagnosis
    )

    assert (
        "4 total issues"
        in result["explanation"]
    )
    assert (
        "3 medium"
        in result["explanation"]
    )
    assert (
        "0 blocking"
        in result["explanation"]
    )

    assert (
        "QUALITY_SUMMARY_RECORDED"
        in result["source_finding_codes"]
    )

    assert result["overall_state"] == "HEALTHY"
    assert result["source_action_codes"] == []