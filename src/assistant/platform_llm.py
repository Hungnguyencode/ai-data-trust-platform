from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from src.assistant.llm_provider import (
    LLMProviderConfig,
    generate_llm_text,
)


def build_grounded_explanation_prompt(
    explanation: Mapping[str, Any],
) -> str:
    deterministic_text = str(
        explanation.get(
            "explanation",
            "",
        )
        or ""
    ).strip()

    if not deterministic_text:
        raise ValueError(
            "explanation must contain "
            "non-empty deterministic text."
        )

    payload = {
        "catalog_id": explanation.get(
            "catalog_id"
        ),
        "latest_version_id": explanation.get(
            "latest_version_id"
        ),
        "overall_state": explanation.get(
            "overall_state"
        ),
        "headline": explanation.get(
            "headline"
        ),
        "summary": explanation.get(
            "summary"
        ),
        "explanation": deterministic_text,
        "source_finding_codes": list(
            explanation.get(
                "source_finding_codes",
                [],
            )
            or []
        ),
        "source_action_codes": list(
            explanation.get(
                "source_action_codes",
                [],
            )
            or []
        ),
    }

    payload_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )

    return (
        "You are the natural-language presentation "
        "layer of a grounded Data Trust platform.\n\n"
        "Rewrite the deterministic explanation below "
        "into clear, concise, professional prose.\n\n"
        "Strict rules:\n"
        "- Do not change the overall_state.\n"
        "- Do not invent findings, evidence, or actions.\n"
        "- Do not add new severity judgments.\n"
        "- Do not change source finding codes.\n"
        "- Do not change source action codes.\n"
        "- Do not override deterministic conclusions.\n"
        "- Return only the rewritten explanation text.\n\n"
        "Grounded deterministic payload:\n"
        f"{payload_json}"
    )


def enhance_platform_explanation(
    explanation: Mapping[str, Any],
    *,
    config: LLMProviderConfig | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    prompt = build_grounded_explanation_prompt(
        explanation
    )

    result = generate_llm_text(
        prompt,
        config=config,
        client=client,
    )

    deterministic_text = str(
        explanation["explanation"]
    ).strip()

    enhanced_text = (
        result.text
        if result.used_llm
        and result.text
        else deterministic_text
    )

    return {
        "catalog_id": explanation.get(
            "catalog_id"
        ),
        "latest_version_id": explanation.get(
            "latest_version_id"
        ),
        "overall_state": explanation.get(
            "overall_state"
        ),
        "headline": explanation.get(
            "headline"
        ),
        "summary": explanation.get(
            "summary"
        ),
        "explanation": deterministic_text,
        "enhanced_explanation": (
            enhanced_text
        ),
        "source_finding_codes": list(
            explanation.get(
                "source_finding_codes",
                [],
            )
            or []
        ),
        "source_action_codes": list(
            explanation.get(
                "source_action_codes",
                [],
            )
            or []
        ),
        "provider": result.provider,
        "model": result.model,
        "used_llm": result.used_llm,
        "fallback_reason": (
            result.fallback_reason
        ),
        "error_type": result.error_type,
    }