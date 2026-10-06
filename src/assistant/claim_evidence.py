from __future__ import annotations

from collections.abc import Mapping

from src.assistant.investigation_intent import (
    classify_claim_types,
)


def build_claim_evidence_requirement(
    *,
    claim_type: str,
    evidence_type: str,
) -> dict[str, object]:
    normalized_claim_type = (
        claim_type
        .strip()
        .upper()
    )

    minimum_item_count_by_claim = {
        "CURRENT_STATE": 1,
        "HISTORICAL_COMPARISON": 2,
    }

    if (
        normalized_claim_type
        not in minimum_item_count_by_claim
    ):
        raise ValueError(
            "Unsupported claim type: "
            f"{claim_type}."
        )

    return {
        "claim_type": normalized_claim_type,
        "evidence_type": evidence_type,
        "minimum_item_count": (
            minimum_item_count_by_claim[
                normalized_claim_type
            ]
        ),
    }


def assess_claim_evidence(
    *,
    requirement: dict[str, object],
    observed_item_count: int | None,
) -> dict[str, object]:
    minimum_item_count = int(
        requirement["minimum_item_count"]
    )

    if observed_item_count is None:
        requirement_status = "UNAVAILABLE"

    elif (
        isinstance(observed_item_count, int)
        and not isinstance(
            observed_item_count,
            bool,
        )
        and observed_item_count
        >= minimum_item_count
    ):
        requirement_status = "SATISFIED"

    else:
        requirement_status = "INSUFFICIENT_ITEMS"

    return {
        "claim_type": requirement["claim_type"],
        "evidence_type": requirement["evidence_type"],
        "minimum_item_count": minimum_item_count,
        "observed_item_count": observed_item_count,
        "requirement_status": requirement_status,
    }


def build_claim_evidence_assessment(
    *,
    requirements: list[dict[str, object]],
    observed_item_counts: dict[str, int | None],
) -> dict[str, object]:
    if not requirements:
        raise ValueError(
            "At least one claim evidence requirement "
            "is required"
        )

    claim_types = {
        str(requirement["claim_type"])
        for requirement in requirements
    }

    if len(claim_types) != 1:
        raise ValueError(
            "All claim evidence requirements must "
            "use the same claim type"
        )

    evidence_types = [
        str(requirement["evidence_type"])
        for requirement in requirements
    ]

    if len(set(evidence_types)) != len(
        evidence_types
    ):
        raise ValueError(
            "Duplicate claim evidence requirement"
        )

    claim_type = str(
        requirements[0]["claim_type"]
    )

    assessed_evidence: list[str] = []
    satisfied_evidence: list[str] = []
    insufficient_evidence: list[str] = []
    unavailable_evidence: list[str] = []
    evidence_requirements: list[
        dict[str, object]
    ] = []

    for requirement in requirements:
        evidence_type = str(
            requirement["evidence_type"]
        )

        assessed_evidence.append(
            evidence_type
        )

        assessment = assess_claim_evidence(
            requirement=requirement,
            observed_item_count=(
                observed_item_counts.get(
                    evidence_type
                )
            ),
        )

        evidence_requirements.append(
            assessment
        )

        requirement_status = str(
            assessment["requirement_status"]
        )

        if requirement_status == "SATISFIED":
            satisfied_evidence.append(
                evidence_type
            )

        elif (
            requirement_status
            == "INSUFFICIENT_ITEMS"
        ):
            insufficient_evidence.append(
                evidence_type
            )

        elif requirement_status == "UNAVAILABLE":
            unavailable_evidence.append(
                evidence_type
            )

    if (
        len(satisfied_evidence)
        == len(assessed_evidence)
    ):
        answerability_status = "ANSWERABLE"

    elif satisfied_evidence:
        answerability_status = "PARTIAL"

    else:
        answerability_status = (
            "NOT_ANSWERABLE"
        )

    return {
        "claim_type": claim_type,
        "assessed_evidence": assessed_evidence,
        "satisfied_evidence": satisfied_evidence,
        "insufficient_evidence": (
            insufficient_evidence
        ),
        "unavailable_evidence": (
            unavailable_evidence
        ),
        "evidence_requirements": (
            evidence_requirements
        ),
        "answerability_status": (
            answerability_status
        ),
    }


def build_claim_evidence_assessment_from_sufficiency(
    *,
    requirements: list[dict[str, object]],
    evidence_sufficiency: Mapping[str, object],
) -> dict[str, object]:
    observed_item_counts: dict[
        str,
        int | None,
    ] = {}

    evidence_details = (
        evidence_sufficiency.get(
            "evidence_details",
            [],
        )
        or []
    )

    if isinstance(evidence_details, list):
        for detail in evidence_details:
            if not isinstance(detail, Mapping):
                continue

            evidence_type = str(
                detail.get(
                    "evidence_type",
                    "",
                )
                or ""
            )

            if not evidence_type:
                continue

            availability_status = str(
                detail.get(
                    "availability_status",
                    "",
                )
                or ""
            ).strip().upper()

            item_count = detail.get(
                "item_count"
            )

            if availability_status == "UNAVAILABLE":
                observed_item_counts[
                    evidence_type
                ] = None

            elif (
                isinstance(item_count, int)
                and not isinstance(
                    item_count,
                    bool,
                )
            ):
                observed_item_counts[
                    evidence_type
                ] = item_count

            else:
                observed_item_counts[
                    evidence_type
                ] = None

    return build_claim_evidence_assessment(
        requirements=requirements,
        observed_item_counts=(
            observed_item_counts
        ),
    )


def build_claim_evidence_assessments_from_sufficiency(
    *,
    requirements: list[dict[str, object]],
    evidence_sufficiency: Mapping[str, object],
) -> list[dict[str, object]]:
    requirements_by_claim_type: dict[
        str,
        list[dict[str, object]],
    ] = {}

    claim_type_order: list[str] = []

    for requirement in requirements:
        claim_type = str(
            requirement["claim_type"]
        )

        if claim_type not in requirements_by_claim_type:
            requirements_by_claim_type[
                claim_type
            ] = []
            claim_type_order.append(
                claim_type
            )

        requirements_by_claim_type[
            claim_type
        ].append(
            requirement
        )

    assessments: list[
        dict[str, object]
    ] = []

    for claim_type in claim_type_order:
        assessments.append(
            build_claim_evidence_assessment_from_sufficiency(
                requirements=(
                    requirements_by_claim_type[
                        claim_type
                    ]
                ),
                evidence_sufficiency=(
                    evidence_sufficiency
                ),
            )
        )

    return assessments


def plan_claim_evidence_requirements(
    *,
    question: str,
    requested_evidence: list[str],
) -> list[dict[str, object]]:
    if not isinstance(question, str):
        raise ValueError(
            "question must be a string"
        )

    normalized_question = (
        question
        .strip()
        .lower()
    )

    if not normalized_question:
        return []

    claim_types = classify_claim_types(
        question
    )

    evidence_types = list(
        dict.fromkeys(
            requested_evidence
        )
    )

    return [
        build_claim_evidence_requirement(
            claim_type=claim_type,
            evidence_type=evidence_type,
        )
        for claim_type in claim_types
        for evidence_type in evidence_types
    ]