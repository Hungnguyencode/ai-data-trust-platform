from __future__ import annotations

import pytest

from src.assistant.platform_reasoning import (
    reason_about_platform_context,
)


def _base_context() -> dict:
    return {
        "catalog_id": 1,
        "dataset": {
            "latest_version_id": 3,
            "version_history": [
                {
                    "version_id": 3,
                    "version_number": 3,
                }
            ],
            "lineage": {
                "summary": {
                    "version_id": 3,
                    "lifecycle_state": "ACTIVE",
                }
            },
        },
        "validation": {
            "latest": {
                "version_id": 3,
                "validation_status": "ACCEPTED",
            },
            "latest_version": {
                "version_id": 3,
                "validation_status": "ACCEPTED",
            },
            "history": [],
        },
        "governance": {
            "latest": {
                "version_id": 3,
                "decision": "APPROVED",
            },
            "latest_version": {
                "version_id": 3,
                "decision": "APPROVED",
            },
            "history": [],
        },
        "observability": {
            "freshness": {
                "latest": {
                    "freshness_status": "FRESH",
                },
                "history": [],
            },
            "volume": {
                "latest": {
                    "volume_status": "NORMAL",
                },
                "history": [],
            },
        },
        "operations": {
            "pipeline_runs": [
                {
                    "pipeline_run_id": 100,
                    "run_status": "SUCCESS",
                }
            ],
            "operational_events": [],
        },
    }


@pytest.mark.parametrize(
    "context",
    [
        None,
        [],
        "bad",
    ],
)
def test_reasoning_rejects_non_dictionary_context(
    context,
):
    with pytest.raises(
        ValueError,
        match="context must be a dictionary",
    ):
        reason_about_platform_context(
            context
        )


def test_reasoning_rejects_invalid_catalog_id():
    context = _base_context()
    context["catalog_id"] = 0

    with pytest.raises(
        ValueError,
        match=(
            "context.catalog_id must be "
            "a positive integer"
        ),
    ):
        reason_about_platform_context(
            context
        )


def test_reasoning_returns_healthy_state():
    result = reason_about_platform_context(
        _base_context()
    )

    assert result["catalog_id"] == 1
    assert result["latest_version_id"] == 3
    assert result["overall_state"] == "HEALTHY"

    codes = {
        finding["code"]
        for finding in result["findings"]
    }

    assert "VALIDATION_ACCEPTED" in codes
    assert "GOVERNANCE_APPROVED" in codes
    assert "LIFECYCLE_ACTIVE" in codes
    assert "FRESHNESS_FRESH" in codes
    assert "VOLUME_NORMAL" in codes
    assert "PIPELINE_SUCCESS" in codes

    assert result["recommended_actions"] == []

    assert result["summary"] == {
        "finding_count": 6,
        "high_count": 0,
        "warning_count": 0,
        "info_count": 6,
        "action_count": 0,
    }


def test_reasoning_uses_latest_version_evidence():
    context = _base_context()

    context["validation"]["latest"] = {
        "version_id": 2,
        "validation_status": "ACCEPTED",
    }

    context["validation"]["latest_version"] = {
        "version_id": 3,
        "validation_status": "REJECTED",
        "blocking_issue_count": 2,
    }

    context["governance"]["latest"] = {
        "version_id": 2,
        "decision": "APPROVED",
    }

    context["governance"]["latest_version"] = {
        "version_id": 3,
        "decision": "REJECTED",
    }

    context["dataset"]["lineage"]["summary"][
        "lifecycle_state"
    ] = "QUARANTINED"

    result = reason_about_platform_context(
        context
    )

    assert (
        result["overall_state"]
        == "ACTION_REQUIRED"
    )

    findings = {
        finding["code"]: finding
        for finding in result["findings"]
    }

    assert (
        findings["VALIDATION_REJECTED"][
            "evidence"
        ]["version_id"]
        == 3
    )

    assert (
        findings["GOVERNANCE_REJECTED"][
            "evidence"
        ]["version_id"]
        == 3
    )

    assert (
        "LIFECYCLE_QUARANTINED"
        in findings
    )

    action_codes = [
        action["code"]
        for action in result[
            "recommended_actions"
        ]
    ]

    assert action_codes[:2] == [
        "REMEDIATE_VALIDATION",
        "RESOLVE_GOVERNANCE",
    ]


def test_reasoning_detects_stale_and_volume_spike():
    context = _base_context()

    context["observability"]["freshness"][
        "latest"
    ] = {
        "freshness_status": "STALE",
        "age_minutes": 180,
        "max_age_minutes": 60,
    }

    context["observability"]["volume"][
        "latest"
    ] = {
        "volume_status": "SPIKE",
        "baseline_row_count": 100,
        "current_row_count": 150,
        "row_change_pct": 50.0,
    }

    result = reason_about_platform_context(
        context
    )

    assert result["overall_state"] == "ATTENTION"

    codes = {
        finding["code"]
        for finding in result["findings"]
    }

    assert "FRESHNESS_STALE" in codes
    assert "VOLUME_SPIKE" in codes

    action_codes = {
        action["code"]
        for action in result[
            "recommended_actions"
        ]
    }

    assert (
        "INVESTIGATE_FRESHNESS"
        in action_codes
    )

    assert (
        "INVESTIGATE_VOLUME"
        in action_codes
    )


def test_reasoning_detects_latest_pipeline_failure():
    context = _base_context()

    context["operations"]["pipeline_runs"] = [
        {
            "pipeline_run_id": 200,
            "run_status": "FAILED",
        },
        {
            "pipeline_run_id": 199,
            "run_status": "SUCCESS",
        },
    ]

    result = reason_about_platform_context(
        context
    )

    assert (
        result["overall_state"]
        == "ACTION_REQUIRED"
    )

    findings = {
        finding["code"]: finding
        for finding in result["findings"]
    }

    assert "PIPELINE_FAILED" in findings

    assert (
        findings["PIPELINE_FAILED"][
            "evidence"
        ]["pipeline_run_id"]
        == 200
    )


def test_reasoning_returns_unknown_without_version():
    context = _base_context()

    context["dataset"][
        "latest_version_id"
    ] = None

    result = reason_about_platform_context(
        context
    )

    assert result["overall_state"] == "UNKNOWN"

    assert result["findings"][0]["code"] == (
        "DATASET_VERSION_MISSING"
    )

    assert (
        result["recommended_actions"][0][
            "code"
        ]
        == "VERIFY_DATASET_INGESTION"
    )


def test_reasoning_marks_review_required_as_attention():
    context = _base_context()

    context["governance"]["latest_version"] = {
        "version_id": 3,
        "decision": "REVIEW_REQUIRED",
    }

    result = reason_about_platform_context(
        context
    )

    assert result["overall_state"] == "ATTENTION"

    codes = {
        finding["code"]
        for finding in result["findings"]
    }

    assert (
        "GOVERNANCE_REVIEW_REQUIRED"
        in codes
    )


def test_reasoning_surfaces_persisted_trust_score_evidence():
    context = _base_context()

    context["governance"]["latest_version"] = {
        "governance_id": 21,
        "version_id": 3,
        "decision": "APPROVED",
        "trust_score": 92.5,
        "privacy_status": "LOW",
    }

    result = reason_about_platform_context(
        context
    )

    findings = {
        finding["code"]: finding
        for finding in result["findings"]
    }

    assert (
        "TRUST_SCORE_RECORDED"
        in findings
    )

    trust_finding = findings[
        "TRUST_SCORE_RECORDED"
    ]

    assert (
        trust_finding["category"]
        == "TRUST_SCORE"
    )
    assert (
        trust_finding["severity"]
        == "INFO"
    )
    assert trust_finding["evidence"] == {
        "version_id": 3,
        "governance_id": 21,
        "trust_score": 92.5,
    }

    assert (
        result["overall_state"]
        == "HEALTHY"
    )
    assert (
        result["recommended_actions"]
        == []
    )


def test_reasoning_surfaces_persisted_privacy_status_evidence():
    context = _base_context()

    context["governance"]["latest_version"] = {
        "governance_id": 22,
        "version_id": 3,
        "decision": "REVIEW_REQUIRED",
        "trust_score": 95.0,
        "privacy_status": "HIGH",
    }

    result = reason_about_platform_context(
        context
    )

    findings = {
        finding["code"]: finding
        for finding in result["findings"]
    }

    assert (
        "PRIVACY_STATUS_RECORDED"
        in findings
    )

    privacy_finding = findings[
        "PRIVACY_STATUS_RECORDED"
    ]

    assert (
        privacy_finding["category"]
        == "PRIVACY"
    )
    assert (
        privacy_finding["severity"]
        == "INFO"
    )
    assert privacy_finding["evidence"] == {
        "version_id": 3,
        "governance_id": 22,
        "privacy_status": "HIGH",
    }

    assert (
        result["overall_state"]
        == "ATTENTION"
    )

    action_codes = {
        action["code"]
        for action in result[
            "recommended_actions"
        ]
    }

    assert action_codes == {
        "REVIEW_GOVERNANCE"
    }


def test_reasoning_surfaces_persisted_quality_summary():
    context = _base_context()

    context["validation"]["latest_version"] = {
        "validation_id": 31,
        "version_id": 3,
        "validation_status": "ACCEPTED",
        "total_issues": 4,
        "high_issues": 0,
        "medium_issues": 3,
        "low_issues": 1,
        "blocking_issue_count": 0,
    }

    result = reason_about_platform_context(
        context
    )

    findings = {
        finding["code"]: finding
        for finding in result["findings"]
    }

    assert (
        "QUALITY_SUMMARY_RECORDED"
        in findings
    )

    quality_finding = findings[
        "QUALITY_SUMMARY_RECORDED"
    ]

    assert (
        quality_finding["category"]
        == "QUALITY"
    )
    assert (
        quality_finding["severity"]
        == "INFO"
    )

    assert quality_finding["evidence"] == {
        "version_id": 3,
        "validation_id": 31,
        "total_issues": 4,
        "high_issues": 0,
        "medium_issues": 3,
        "low_issues": 1,
        "blocking_issue_count": 0,
    }

    assert (
        result["overall_state"]
        == "HEALTHY"
    )

    assert (
        result["recommended_actions"]
        == []
    )