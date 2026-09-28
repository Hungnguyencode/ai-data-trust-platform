from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


def _split_claim_response_segments(
    question: str,
) -> list[str]:
    segments = re.split(
        (
            r"\band\s+(?="
            r"tell me\b|"
            r"show me\b|"
            r"what(?:'s| is)\b"
            r")"
            r"|\bthen\b"
            r"|\bvà\s+(?="
            r"cho tôi biết\b|"
            r"cho mình biết\b"
            r")"
            r"|\brồi\b"
        ),
        question,
        flags=re.IGNORECASE,
    )

    return [
        segment.strip()
        for segment in segments
        if segment.strip()
    ]


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

    segments = _split_claim_response_segments(
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

        plan.append(
            {
                "claim_index": claim_index,
                "claim_text": claim_text,
                "claim_type": claim_type,
                "answerability_status": (
                    answerability_status
                ),
                "response_mode": response_mode,
                "controlled_tool_results": (
                    controlled_tool_results
                ),
            }
        )

    return plan