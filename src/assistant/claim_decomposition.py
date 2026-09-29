from __future__ import annotations

import re

_ENGLISH_CLAIM_STARTER_PATTERN = (
    r"(?:"
    r"tell me\b|"
    r"show me\b|"
    r"explain\b|"
    r"compare\b|"
    r"what(?:'s| is)\b"
    r")"
)

_VIETNAMESE_CLAIM_STARTER_PATTERN = (
    r"(?:"
    r"cho tôi biết\b|"
    r"cho mình biết\b"
    r")"
)

_ANY_CLAIM_STARTER_PATTERN = (
    rf"(?:"
    rf"{_ENGLISH_CLAIM_STARTER_PATTERN}|"
    rf"{_VIETNAMESE_CLAIM_STARTER_PATTERN}"
    rf")"
)


def split_claim_segments(
    question: str,
) -> list[str]:
    separator_pattern = (
        rf"\band\s+(?="
        rf"{_ENGLISH_CLAIM_STARTER_PATTERN}"
        rf")"
        rf"|;\s*(?="
        rf"{_ANY_CLAIM_STARTER_PATTERN}"
        rf")"
        rf"|\bthen\s+(?="
        rf"{_ANY_CLAIM_STARTER_PATTERN}"
        rf")"
        rf"|\bvà\s+(?="
        rf"{_VIETNAMESE_CLAIM_STARTER_PATTERN}"
        rf")"
        rf"|\brồi\s+(?="
        rf"{_ANY_CLAIM_STARTER_PATTERN}"
        rf")"
    )

    segments = re.split(
        separator_pattern,
        question,
        flags=re.IGNORECASE,
    )

    normalized_segments = [
        segment.strip().rstrip(",").strip()
        for segment in segments
    ]

    return [
        segment
        for segment in normalized_segments
        if segment
    ]