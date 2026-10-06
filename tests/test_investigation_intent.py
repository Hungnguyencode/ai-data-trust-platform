import pytest

from src.assistant.investigation_intent import (
    classify_claim_types,
    classify_investigation_intent,
)


@pytest.mark.parametrize(
    (
        "question",
        "expected_intent",
    ),
    [
        (
            "Why is this dataset currently unhealthy?",
            "CURRENT_STATE_INVESTIGATION",
        ),
        (
            "Why should this version not be promoted?",
            "PROMOTION_DIAGNOSIS",
        ),
        (
            "Which problem should be investigated first?",
            "PRIORITIZATION",
        ),
        (
            "What evidence supports this recommendation?",
            "RECOMMENDATION_EVIDENCE",
        ),
        (
            "What changed since the previous ingestion?",
            "HISTORICAL_COMPARISON",
        ),
    ],
)
def test_classifies_canonical_investigation_intents(
    question,
    expected_intent,
):
    assert (
        classify_investigation_intent(question)
        == expected_intent
    )


@pytest.mark.parametrize(
    (
        "question",
        "expected_claim_types",
    ),
    [
        (
            "What changed since the previous ingestion?",
            ["HISTORICAL_COMPARISON"],
        ),
        (
            "What is the latest volume?",
            ["CURRENT_STATE"],
        ),
        (
            (
                "Compare volume over time and tell me "
                "the latest volume."
            ),
            [
                "HISTORICAL_COMPARISON",
                "CURRENT_STATE",
            ],
        ),
        (
            "Opaque investigation request.",
            [],
        ),
    ],
)
def test_classifies_claim_types(
    question,
    expected_claim_types,
):
    assert (
        classify_claim_types(question)
        == expected_claim_types
    )
