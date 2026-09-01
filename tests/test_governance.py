import pytest

from src.governance.governance_engine import (
    GovernanceEngine,
)


def test_governance_accept():
    engine = GovernanceEngine()

    result = engine.evaluate(
        validation_status="ACCEPTED",
        trust_score=92,
        privacy_status="LOW",
    )

    assert result.decision == "APPROVED"
    assert result.promotion_eligible is True


def test_low_score_requires_review():
    engine = GovernanceEngine()

    result = engine.evaluate(
        validation_status="ACCEPTED",
        trust_score=40,
        privacy_status="LOW",
    )

    assert (
        result.decision
        == "REVIEW_REQUIRED"
    )

    assert (
        result.promotion_eligible
        is False
    )


def test_high_privacy_requires_review():
    engine = GovernanceEngine()

    result = engine.evaluate(
        validation_status="ACCEPTED",
        trust_score=95,
        privacy_status="HIGH",
    )

    assert (
        result.decision
        == "REVIEW_REQUIRED"
    )


def test_critical_privacy_is_rejected():
    engine = GovernanceEngine()

    result = engine.evaluate(
        validation_status="ACCEPTED",
        trust_score=95,
        privacy_status="CRITICAL",
    )

    assert result.decision == "REJECTED"
    assert result.promotion_eligible is False


def test_blocking_issue_is_rejected():
    engine = GovernanceEngine()

    result = engine.evaluate(
        validation_status="ACCEPTED",
        trust_score=95,
        privacy_status="LOW",
        blocking_issue_count=2,
    )

    assert result.decision == "REJECTED"


def test_rejected_validation_is_rejected():
    engine = GovernanceEngine()

    result = engine.evaluate(
        validation_status="REJECTED",
        trust_score=95,
        privacy_status="LOW",
        blocking_issue_count=0,
    )

    assert result.decision == "REJECTED"


def test_medium_privacy_requires_review():
    engine = GovernanceEngine()

    result = engine.evaluate(
        validation_status="ACCEPTED",
        trust_score=95,
        privacy_status="MEDIUM",
    )

    assert (
        result.decision
        == "REVIEW_REQUIRED"
    )


def test_invalid_score_is_rejected():
    engine = GovernanceEngine()

    with pytest.raises(
        ValueError,
        match="0-100",
    ):
        engine.evaluate(
            validation_status="ACCEPTED",
            trust_score=120,
            privacy_status="LOW",
        )