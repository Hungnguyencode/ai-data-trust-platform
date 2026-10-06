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


def test_historical_paraphrase_maps_to_same_classification():
    question = (
        "How is this ingestion different "
        "from the last one?"
    )

    assert (
        classify_investigation_intent(question)
        == "HISTORICAL_COMPARISON"
    )

    assert classify_claim_types(
        question
    ) == [
        "HISTORICAL_COMPARISON",
    ]


def test_promotion_diagnosis_paraphrase_maps_to_same_classification():
    question = (
        "What is blocking this version "
        "from promotion?"
    )

    assert (
        classify_investigation_intent(question)
        == "PROMOTION_DIAGNOSIS"
    )

    assert classify_claim_types(
        question
    ) == [
        "CURRENT_STATE",
    ]


def test_prioritization_paraphrase_maps_to_same_classification():
    question = (
        "Which issue should I "
        "investigate first?"
    )

    assert (
        classify_investigation_intent(question)
        == "PRIORITIZATION"
    )

    assert classify_claim_types(
        question
    ) == [
        "CURRENT_STATE",
    ]


def test_recommendation_evidence_paraphrase_maps_to_same_classification():
    question = (
        "What evidence backs "
        "this recommendation?"
    )

    assert (
        classify_investigation_intent(question)
        == "RECOMMENDATION_EVIDENCE"
    )

    assert classify_claim_types(
        question
    ) == [
        "CURRENT_STATE",
    ]


def test_current_state_investigation_paraphrase_maps_to_same_classification():
    question = (
        "Why is the dataset in a bad state "
        "right now?"
    )

    assert (
        classify_investigation_intent(question)
        == "CURRENT_STATE_INVESTIGATION"
    )

    assert classify_claim_types(
        question
    ) == [
        "CURRENT_STATE",
    ]


def test_rollback_reference_does_not_match_recommendation_support():
    question = (
        "What evidence is available "
        "for this rollback recommendation?"
    )

    assert (
        classify_investigation_intent(question)
        == "UNCLASSIFIED"
    )

    assert classify_claim_types(
        question
    ) == []