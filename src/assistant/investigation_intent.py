from __future__ import annotations

from typing import Literal

InvestigationIntent = Literal[
    "CURRENT_STATE_INVESTIGATION",
    "PROMOTION_DIAGNOSIS",
    "PRIORITIZATION",
    "RECOMMENDATION_EVIDENCE",
    "HISTORICAL_COMPARISON",
    "UNCLASSIFIED",
]


ClaimType = Literal[
    "CURRENT_STATE",
    "HISTORICAL_COMPARISON",
]


HISTORICAL_CROSS_DOMAIN_TERMS = (
    "changed since the previous ingestion",
)

PROMOTION_DIAGNOSIS_TERMS = (
    "not be promoted",
)

PRIORITIZATION_TERMS = (
    "investigated first",
)

RECOMMENDATION_EVIDENCE_TERMS = (
    "evidence supports this recommendation",
)

CURRENT_STATE_INVESTIGATION_TERMS = (
    "unhealthy",
)

HISTORICAL_COMPARISON_TERMS = (
    "compare",
    "comparison",
    "trend",
    "over time",
    *HISTORICAL_CROSS_DOMAIN_TERMS,
    "so sánh",
    "xu hướng",
    "theo thời gian",
)

CURRENT_STATE_TERMS = (
    "latest",
    "current",
    "most recent",
    "newest",
    *PROMOTION_DIAGNOSIS_TERMS,
    *PRIORITIZATION_TERMS,
    *RECOMMENDATION_EVIDENCE_TERMS,
    "mới nhất",
    "hiện tại",
    "gần nhất",
)


def classify_investigation_intent(
    question: str,
) -> InvestigationIntent:
    if not isinstance(question, str):
        raise ValueError(
            "question must be a string."
        )

    normalized_question = (
        question
        .strip()
        .lower()
    )

    if not normalized_question:
        return "UNCLASSIFIED"

    if any(
        term in normalized_question
        for term in HISTORICAL_CROSS_DOMAIN_TERMS
    ):
        return "HISTORICAL_COMPARISON"

    if any(
        term in normalized_question
        for term in PROMOTION_DIAGNOSIS_TERMS
    ):
        return "PROMOTION_DIAGNOSIS"

    if any(
        term in normalized_question
        for term in PRIORITIZATION_TERMS
    ):
        return "PRIORITIZATION"

    if any(
        term in normalized_question
        for term in RECOMMENDATION_EVIDENCE_TERMS
    ):
        return "RECOMMENDATION_EVIDENCE"

    if any(
        term in normalized_question
        for term in CURRENT_STATE_INVESTIGATION_TERMS
    ):
        return "CURRENT_STATE_INVESTIGATION"

    return "UNCLASSIFIED"


def classify_claim_types(
    question: str,
) -> list[ClaimType]:
    if not isinstance(question, str):
        raise ValueError(
            "question must be a string."
        )

    normalized_question = (
        question
        .strip()
        .lower()
    )

    if not normalized_question:
        return []

    claim_types: list[ClaimType] = []

    if any(
        term in normalized_question
        for term in HISTORICAL_COMPARISON_TERMS
    ):
        claim_types.append(
            "HISTORICAL_COMPARISON"
        )

    if any(
        term in normalized_question
        for term in CURRENT_STATE_TERMS
    ):
        claim_types.append(
            "CURRENT_STATE"
        )

    return claim_types
