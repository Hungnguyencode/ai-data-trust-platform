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

HISTORICAL_REFERENCE_TERMS = (
    "previous ingestion",
    "last ingestion",
    "previous load",
    "last load",
    "previous one",
    "last one",
)

HISTORICAL_RELATION_TERMS = (
    "changed",
    "change",
    "different",
    "difference",
)

PROMOTION_REFERENCE_TERMS = (
    "promotion",
    "promoted",
)

PROMOTION_BLOCKING_TERMS = (
    "blocking",
    "blocked",
    "preventing",
    "prevents",
    "prevent",
)

PRIORITIZATION_ACTION_TERMS = (
    "investigate",
    "investigated",
    "look into",
)

PRIORITIZATION_ORDER_TERMS = (
    "first",
    "priority",
    "prioritize",
)

RECOMMENDATION_REFERENCE_TERMS = (
    "recommendation",
)

EVIDENCE_REFERENCE_TERMS = (
    "evidence",
)

RECOMMENDATION_SUPPORT_TERMS = (
    "support",
    "supports",
    "backs",
    "backed",
    "backing",
)

CURRENT_STATE_CONDITION_TERMS = (
    "unhealthy",
    "bad state",
    "degraded",
)

CURRENT_TIME_REFERENCE_TERMS = (
    "right now",
    "currently",
    "at the moment",
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

    if _is_historical_cross_domain(
        normalized_question
    ):
        return "HISTORICAL_COMPARISON"

    if _is_promotion_diagnosis(
        normalized_question
    ):
        return "PROMOTION_DIAGNOSIS"

    if _is_prioritization(
        normalized_question
    ):
        return "PRIORITIZATION"

    if _is_recommendation_evidence(
        normalized_question
    ):
        return "RECOMMENDATION_EVIDENCE"

    if _is_current_state_investigation(
        normalized_question
    ):
        return "CURRENT_STATE_INVESTIGATION"

    return "UNCLASSIFIED"


def _is_historical_cross_domain(
    normalized_question: str,
) -> bool:
    if any(
        term in normalized_question
        for term in HISTORICAL_CROSS_DOMAIN_TERMS
    ):
        return True

    has_historical_reference = any(
        term in normalized_question
        for term in HISTORICAL_REFERENCE_TERMS
    )

    has_historical_relation = any(
        term in normalized_question
        for term in HISTORICAL_RELATION_TERMS
    )

    return (
        has_historical_reference
        and has_historical_relation
    )


def _is_promotion_diagnosis(
    normalized_question: str,
) -> bool:
    if any(
        term in normalized_question
        for term in PROMOTION_DIAGNOSIS_TERMS
    ):
        return True

    has_promotion_reference = any(
        term in normalized_question
        for term in PROMOTION_REFERENCE_TERMS
    )

    has_blocking_relation = any(
        term in normalized_question
        for term in PROMOTION_BLOCKING_TERMS
    )

    return (
        has_promotion_reference
        and has_blocking_relation
    )


def _is_prioritization(
    normalized_question: str,
) -> bool:
    if any(
        term in normalized_question
        for term in PRIORITIZATION_TERMS
    ):
        return True

    has_investigation_action = any(
        term in normalized_question
        for term in PRIORITIZATION_ACTION_TERMS
    )

    has_priority_relation = any(
        term in normalized_question
        for term in PRIORITIZATION_ORDER_TERMS
    )

    return (
        has_investigation_action
        and has_priority_relation
    )


def _is_recommendation_evidence(
    normalized_question: str,
) -> bool:
    if any(
        term in normalized_question
        for term in RECOMMENDATION_EVIDENCE_TERMS
    ):
        return True

    has_evidence_reference = any(
        term in normalized_question
        for term in EVIDENCE_REFERENCE_TERMS
    )

    has_recommendation_reference = any(
        term in normalized_question
        for term in RECOMMENDATION_REFERENCE_TERMS
    )

    has_support_relation = any(
        term in normalized_question
        for term in RECOMMENDATION_SUPPORT_TERMS
    )

    return (
        has_evidence_reference
        and has_recommendation_reference
        and has_support_relation
    )


def _is_current_state_investigation(
    normalized_question: str,
) -> bool:
    if any(
        term in normalized_question
        for term in CURRENT_STATE_INVESTIGATION_TERMS
    ):
        return True

    has_condition_reference = any(
        term in normalized_question
        for term in CURRENT_STATE_CONDITION_TERMS
    )

    has_current_time_reference = any(
        term in normalized_question
        for term in CURRENT_TIME_REFERENCE_TERMS
    )

    return (
        has_condition_reference
        and has_current_time_reference
    )


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

    if (
        _is_historical_cross_domain(
            normalized_question
        )
        or any(
            term in normalized_question
            for term in HISTORICAL_COMPARISON_TERMS
        )
    ):
        claim_types.append(
            "HISTORICAL_COMPARISON"
        )

    if (
        _is_promotion_diagnosis(
            normalized_question
        )
        or _is_prioritization(
            normalized_question
        )
        or _is_recommendation_evidence(
            normalized_question
        )
        or _is_current_state_investigation(
            normalized_question
        )
        or any(
            term in normalized_question
            for term in CURRENT_STATE_TERMS
        )
    ):
        claim_types.append(
            "CURRENT_STATE"
        )

    return claim_types
