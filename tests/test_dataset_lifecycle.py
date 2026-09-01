import pytest

from src.lifecycle.dataset_lifecycle import (
    is_governed_promotion_eligible,
    is_promotion_eligible,
    lifecycle_state_from_validation,
    lifecycle_summary,
)


def test_accepted_validation_becomes_validated():
    assert (
        lifecycle_state_from_validation(
            "ACCEPTED"
        )
        == "VALIDATED"
    )


def test_rejected_validation_becomes_quarantined():
    assert (
        lifecycle_state_from_validation(
            "REJECTED"
        )
        == "QUARANTINED"
    )


def test_validation_status_is_case_insensitive():
    assert (
        lifecycle_state_from_validation(
            "accepted"
        )
        == "VALIDATED"
    )


def test_invalid_validation_status_is_rejected():
    with pytest.raises(
        ValueError,
        match="Validation status",
    ):
        lifecycle_state_from_validation(
            "UNKNOWN"
        )


def test_validated_version_is_promotion_eligible():
    assert (
        is_promotion_eligible(
            "VALIDATED"
        )
        is True
    )


def test_quarantined_version_is_not_promotion_eligible():
    assert (
        is_promotion_eligible(
            "QUARANTINED"
        )
        is False
    )


def test_active_version_is_not_promotion_eligible_again():
    assert (
        is_promotion_eligible(
            "ACTIVE"
        )
        is False
    )


def test_lifecycle_summary_for_validated_version():
    result = lifecycle_summary(
        lifecycle_state="VALIDATED"
    )

    assert result["state"] == "VALIDATED"
    assert result["promotion_eligible"] is True


def test_invalid_lifecycle_state_is_rejected():
    with pytest.raises(
        ValueError,
        match="Lifecycle state",
    ):
        lifecycle_summary(
            lifecycle_state="MAGIC"
        )


def test_validated_and_governance_approved_can_promote():
    assert (
        is_governed_promotion_eligible(
            "VALIDATED",
            {
                "decision": "APPROVED",
                "promotion_eligible": True,
            },
        )
        is True
    )


def test_validated_without_governance_cannot_promote():
    assert (
        is_governed_promotion_eligible(
            "VALIDATED",
            None,
        )
        is False
    )


def test_review_required_cannot_promote():
    assert (
        is_governed_promotion_eligible(
            "VALIDATED",
            {
                "decision": "REVIEW_REQUIRED",
                "promotion_eligible": False,
            },
        )
        is False
    )


def test_active_version_is_not_governed_promotion_eligible():
    assert (
        is_governed_promotion_eligible(
            "ACTIVE",
            {
                "decision": "APPROVED",
                "promotion_eligible": True,
            },
        )
        is False
    )