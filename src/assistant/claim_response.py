from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.assistant.claim_decomposition import (
    split_claim_segments,
)


def build_claim_response_plan(
    *,
    question: str,
    claim_scoped_controlled_tool_results: list[
        Mapping[str, Any]
    ],
) -> list[dict[str, Any]]:
    if not isinstance(question, str):
        raise ValueError(
            "question must be a string."
        )

    if not question.strip():
        return []

    segments = split_claim_segments(
        question
    )

    if (
        len(segments)
        != len(
            claim_scoped_controlled_tool_results
        )
    ):
        raise ValueError(
            "claim segment count must match "
            "claim scope count."
        )

    plan: list[dict[str, Any]] = []

    for claim_index, (
        claim_text,
        claim_scope,
    ) in enumerate(
        zip(
            segments,
            claim_scoped_controlled_tool_results,
            strict=True,
        )
    ):
        if not isinstance(
            claim_scope,
            Mapping,
        ):
            raise ValueError(
                "claim scope must be a mapping."
            )

        claim_type = str(
            claim_scope.get(
                "claim_type",
                "",
            )
            or ""
        ).strip()

        answerability_status = str(
            claim_scope.get(
                "answerability_status",
                "",
            )
            or ""
        ).strip().upper()

        if answerability_status == (
            "NOT_ANSWERABLE"
        ):
            response_mode = (
                "DETERMINISTIC_LIMITATION"
            )
        elif answerability_status in {
            "ANSWERABLE",
            "PARTIAL",
        }:
            response_mode = "LLM"
        else:
            raise ValueError(
                "unsupported claim "
                "answerability status: "
                f"{answerability_status!r}."
            )

        controlled_tool_results = list(
            claim_scope.get(
                "controlled_tool_results",
                [],
            )
            or []
        )

        evidence_requirements = list(
            claim_scope.get(
                "evidence_requirements",
                [],
            )
            or []
        )

        plan.append(
            {
                "claim_index": claim_index,
                "claim_text": claim_text,
                "claim_type": claim_type,
                "answerability_status": (
                    answerability_status
                ),
                "response_mode": response_mode,
                "evidence_requirements": (
                    evidence_requirements
                ),
                "controlled_tool_results": (
                    controlled_tool_results
                ),
            }
        )

    return plan


def execute_claim_response_plan(
    *,
    plan: list[Mapping[str, Any]],
    answer_claim,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for item in plan:
        if not isinstance(item, Mapping):
            raise ValueError(
                "claim response plan item "
                "must be a mapping."
            )

        claim_index = int(
            item.get(
                "claim_index",
                0,
            )
        )

        claim_text = str(
            item.get(
                "claim_text",
                "",
            )
            or ""
        )

        claim_type = str(
            item.get(
                "claim_type",
                "",
            )
            or ""
        )

        answerability_status = str(
            item.get(
                "answerability_status",
                "",
            )
            or ""
        ).strip().upper()

        response_mode = str(
            item.get(
                "response_mode",
                "",
            )
            or ""
        ).strip().upper()

        controlled_tool_results = list(
            item.get(
                "controlled_tool_results",
                [],
            )
            or []
        )

        evidence_requirements = list(
            item.get(
                "evidence_requirements",
                [],
            )
            or []
        )

        evidence_tool_names = [
            str(result.get("name")).strip()
            for result in controlled_tool_results
            if (
                isinstance(result, Mapping)
                and result.get("name")
            )
        ]

        if response_mode == (
            "DETERMINISTIC_LIMITATION"
        ):
            if controlled_tool_results:
                raise ValueError(
                    "unsupported claim must not "
                    "contain controlled tool results."
                )

            results.append(
                {
                    "claim_index": claim_index,
                    "claim_text": claim_text,
                    "claim_type": claim_type,
                    "answerability_status": (
                        answerability_status
                    ),
                    "response_mode": (
                        response_mode
                    ),
                    "evidence_tool_names": (
                        evidence_tool_names
                    ),
                    "evidence_requirements": (
                        evidence_requirements
                    ),
                    "used_llm": False,
                    "answer": None,
                }
            )
            continue

        if response_mode != "LLM":
            raise ValueError(
                "unsupported claim "
                "response mode: "
                f"{response_mode!r}."
            )

        claim_output = answer_claim(
            claim_text=claim_text,
            controlled_tool_results=(
                controlled_tool_results
            ),
        )

        if isinstance(claim_output, Mapping):
            results.append(
                {
                    "claim_index": claim_index,
                    "claim_text": claim_text,
                    "claim_type": claim_type,
                    "answerability_status": (
                        answerability_status
                    ),
                    "response_mode": response_mode,
                    "evidence_tool_names": (
                        evidence_tool_names
                    ),
                    "evidence_requirements": (
                        evidence_requirements
                    ),
                    "provider": claim_output.get(
                        "provider"
                    ),
                    "model": claim_output.get(
                        "model"
                    ),
                    "used_llm": bool(
                        claim_output.get(
                            "used_llm",
                            False,
                        )
                    ),
                    "fallback_reason": (
                        claim_output.get(
                            "fallback_reason"
                        )
                    ),
                    "error_type": claim_output.get(
                        "error_type"
                    ),
                    "answer": claim_output.get(
                        "answer"
                    ),
                }
            )
            continue

        results.append(
            {
                "claim_index": claim_index,
                "claim_text": claim_text,
                "claim_type": claim_type,
                "answerability_status": (
                    answerability_status
                ),
                "response_mode": response_mode,
                "evidence_tool_names": (
                    evidence_tool_names
                ),
                "evidence_requirements": (
                    evidence_requirements
                ),
                "used_llm": True,
                "answer": claim_output,
            }
        )

    return results