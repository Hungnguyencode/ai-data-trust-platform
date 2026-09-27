import pytest

from src.assistant.claim_evidence import (
    assess_claim_evidence,
    build_claim_evidence_assessment,
    build_claim_evidence_assessment_from_sufficiency,
    build_claim_evidence_requirement,
)


def test_current_state_claim_requires_one_item():
    requirement = build_claim_evidence_requirement(
        claim_type="CURRENT_STATE",
        evidence_type="volume_history",
    )

    assert requirement == {
        "claim_type": "CURRENT_STATE",
        "evidence_type": "volume_history",
        "minimum_item_count": 1,
    }


def test_historical_comparison_claim_requires_two_items():
    requirement = build_claim_evidence_requirement(
        claim_type="HISTORICAL_COMPARISON",
        evidence_type="volume_history",
    )

    assert requirement == {
        "claim_type": "HISTORICAL_COMPARISON",
        "evidence_type": "volume_history",
        "minimum_item_count": 2,
    }


def test_claim_evidence_requirement_rejects_unknown_claim_type():
    with pytest.raises(
        ValueError,
        match="Unsupported claim type",
    ):
        build_claim_evidence_requirement(
            claim_type="UNKNOWN",
            evidence_type="volume_history",
        )


def test_claim_evidence_is_satisfied_when_minimum_is_met():
    requirement = build_claim_evidence_requirement(
        claim_type="HISTORICAL_COMPARISON",
        evidence_type="volume_history",
    )

    assessment = assess_claim_evidence(
        requirement=requirement,
        observed_item_count=2,
    )

    assert assessment == {
        "claim_type": "HISTORICAL_COMPARISON",
        "evidence_type": "volume_history",
        "minimum_item_count": 2,
        "observed_item_count": 2,
        "requirement_status": "SATISFIED",
    }


def test_claim_evidence_is_insufficient_below_minimum():
    requirement = build_claim_evidence_requirement(
        claim_type="HISTORICAL_COMPARISON",
        evidence_type="volume_history",
    )

    assessment = assess_claim_evidence(
        requirement=requirement,
        observed_item_count=1,
    )

    assert assessment == {
        "claim_type": "HISTORICAL_COMPARISON",
        "evidence_type": "volume_history",
        "minimum_item_count": 2,
        "observed_item_count": 1,
        "requirement_status": "INSUFFICIENT_ITEMS",
    }


def test_claim_evidence_is_unavailable_without_item_count():
    requirement = build_claim_evidence_requirement(
        claim_type="CURRENT_STATE",
        evidence_type="volume_history",
    )

    assessment = assess_claim_evidence(
        requirement=requirement,
        observed_item_count=None,
    )

    assert assessment == {
        "claim_type": "CURRENT_STATE",
        "evidence_type": "volume_history",
        "minimum_item_count": 1,
        "observed_item_count": None,
        "requirement_status": "UNAVAILABLE",
    }


def test_same_evidence_count_has_different_claim_answerability():
    current_state_requirement = (
        build_claim_evidence_requirement(
            claim_type="CURRENT_STATE",
            evidence_type="volume_history",
        )
    )

    historical_requirement = (
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="volume_history",
        )
    )

    current_state_assessment = assess_claim_evidence(
        requirement=current_state_requirement,
        observed_item_count=1,
    )

    historical_assessment = assess_claim_evidence(
        requirement=historical_requirement,
        observed_item_count=1,
    )

    assert (
        current_state_assessment[
            "requirement_status"
        ]
        == "SATISFIED"
    )

    assert (
        historical_assessment[
            "requirement_status"
        ]
        == "INSUFFICIENT_ITEMS"
    )


def test_claim_evidence_assessment_is_partial_when_some_requirements_fail():
    requirements = [
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="freshness_history",
        ),
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="volume_history",
        ),
    ]

    assessment = build_claim_evidence_assessment(
        requirements=requirements,
        observed_item_counts={
            "freshness_history": 2,
            "volume_history": 1,
        },
    )

    assert assessment == {
        "claim_type": "HISTORICAL_COMPARISON",
        "assessed_evidence": [
            "freshness_history",
            "volume_history",
        ],
        "satisfied_evidence": [
            "freshness_history",
        ],
        "insufficient_evidence": [
            "volume_history",
        ],
        "unavailable_evidence": [],
        "evidence_requirements": [
            {
                "claim_type": "HISTORICAL_COMPARISON",
                "evidence_type": "freshness_history",
                "minimum_item_count": 2,
                "observed_item_count": 2,
                "requirement_status": "SATISFIED",
            },
            {
                "claim_type": "HISTORICAL_COMPARISON",
                "evidence_type": "volume_history",
                "minimum_item_count": 2,
                "observed_item_count": 1,
                "requirement_status": "INSUFFICIENT_ITEMS",
            },
        ],
        "answerability_status": "PARTIAL",
    }


def test_claim_evidence_assessment_is_answerable_when_all_requirements_pass():
    requirements = [
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="freshness_history",
        ),
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="volume_history",
        ),
    ]

    assessment = build_claim_evidence_assessment(
        requirements=requirements,
        observed_item_counts={
            "freshness_history": 2,
            "volume_history": 3,
        },
    )

    assert assessment["satisfied_evidence"] == [
        "freshness_history",
        "volume_history",
    ]
    assert assessment["insufficient_evidence"] == []
    assert assessment["unavailable_evidence"] == []
    assert (
        assessment["answerability_status"]
        == "ANSWERABLE"
    )


def test_claim_evidence_assessment_is_not_answerable_when_none_pass():
    requirements = [
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="freshness_history",
        ),
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="volume_history",
        ),
    ]

    assessment = build_claim_evidence_assessment(
        requirements=requirements,
        observed_item_counts={
            "freshness_history": 1,
            "volume_history": None,
        },
    )

    assert assessment["satisfied_evidence"] == []
    assert assessment["insufficient_evidence"] == [
        "freshness_history",
    ]
    assert assessment["unavailable_evidence"] == [
        "volume_history",
    ]
    assert (
        assessment["answerability_status"]
        == "NOT_ANSWERABLE"
    )


def test_claim_evidence_assessment_rejects_empty_requirements():
    with pytest.raises(
        ValueError,
        match="At least one claim evidence requirement is required",
    ):
        build_claim_evidence_assessment(
            requirements=[],
            observed_item_counts={},
        )


def test_claim_evidence_assessment_rejects_mixed_claim_types():
    requirements = [
        build_claim_evidence_requirement(
            claim_type="CURRENT_STATE",
            evidence_type="volume_history",
        ),
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="freshness_history",
        ),
    ]

    with pytest.raises(
        ValueError,
        match="All claim evidence requirements must use the same claim type",
    ):
        build_claim_evidence_assessment(
            requirements=requirements,
            observed_item_counts={
                "volume_history": 1,
                "freshness_history": 2,
            },
        )


def test_claim_evidence_assessment_rejects_duplicate_evidence():
    requirements = [
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="volume_history",
        ),
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="volume_history",
        ),
    ]

    with pytest.raises(
        ValueError,
        match="Duplicate claim evidence requirement",
    ):
        build_claim_evidence_assessment(
            requirements=requirements,
            observed_item_counts={
                "volume_history": 2,
            },
        )


def test_build_claim_evidence_assessment_from_sufficiency():
    requirements = [
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="freshness_history",
        ),
        build_claim_evidence_requirement(
            claim_type="HISTORICAL_COMPARISON",
            evidence_type="volume_history",
        ),
    ]

    evidence_sufficiency = {
        "requested_evidence": [
            "freshness_history",
            "volume_history",
        ],
        "evidence_details": [
            {
                "evidence_type": "freshness_history",
                "availability_status": "AVAILABLE",
                "item_count": 2,
            },
            {
                "evidence_type": "volume_history",
                "availability_status": "AVAILABLE",
                "item_count": 1,
            },
        ],
    }

    assessment = (
        build_claim_evidence_assessment_from_sufficiency(
            requirements=requirements,
            evidence_sufficiency=evidence_sufficiency,
        )
    )

    assert assessment["satisfied_evidence"] == [
        "freshness_history",
    ]
    assert assessment["insufficient_evidence"] == [
        "volume_history",
    ]
    assert assessment["unavailable_evidence"] == []
    assert (
        assessment["answerability_status"]
        == "PARTIAL"
    )


def test_claim_evidence_from_sufficiency_treats_empty_as_insufficient():
    requirements = [
        build_claim_evidence_requirement(
            claim_type="CURRENT_STATE",
            evidence_type="volume_history",
        ),
    ]

    assessment = (
        build_claim_evidence_assessment_from_sufficiency(
            requirements=requirements,
            evidence_sufficiency={
                "evidence_details": [
                    {
                        "evidence_type": "volume_history",
                        "availability_status": "EMPTY",
                        "item_count": 0,
                    },
                ],
            },
        )
    )

    assert assessment["insufficient_evidence"] == [
        "volume_history",
    ]
    assert assessment["unavailable_evidence"] == []
    assert (
        assessment["evidence_requirements"][0][
            "requirement_status"
        ]
        == "INSUFFICIENT_ITEMS"
    )


def test_claim_evidence_from_sufficiency_treats_unavailable_as_unavailable():
    requirements = [
        build_claim_evidence_requirement(
            claim_type="CURRENT_STATE",
            evidence_type="volume_history",
        ),
    ]

    assessment = (
        build_claim_evidence_assessment_from_sufficiency(
            requirements=requirements,
            evidence_sufficiency={
                "evidence_details": [
                    {
                        "evidence_type": "volume_history",
                        "availability_status": "UNAVAILABLE",
                        "item_count": None,
                    },
                ],
            },
        )
    )

    assert assessment["insufficient_evidence"] == []
    assert assessment["unavailable_evidence"] == [
        "volume_history",
    ]
    assert (
        assessment["evidence_requirements"][0][
            "requirement_status"
        ]
        == "UNAVAILABLE"
    )
