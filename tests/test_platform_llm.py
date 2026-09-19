from __future__ import annotations

from types import SimpleNamespace

from src.assistant.llm_provider import (
    LLMProviderConfig,
)
from src.assistant.platform_llm import (
    build_grounded_explanation_prompt,
    enhance_platform_explanation,
)


def _sample_explanation():
    return {
        "catalog_id": 1,
        "latest_version_id": 3,
        "overall_state": (
            "ACTION_REQUIRED"
        ),
        "headline": (
            "Dataset requires remediation."
        ),
        "summary": (
            "Validation and governance "
            "controls rejected the dataset."
        ),
        "explanation": (
            "The dataset failed validation "
            "and governance checks."
        ),
        "source_finding_codes": [
            "VALIDATION_REJECTED",
            "GOVERNANCE_REJECTED",
        ],
        "source_action_codes": [
            "REMEDIATE_VALIDATION",
            "RESOLVE_GOVERNANCE",
        ],
    }


def test_prompt_contains_grounded_constraints():
    prompt = (
        build_grounded_explanation_prompt(
            _sample_explanation()
        )
    )

    assert (
        "Do not change the overall_state."
        in prompt
    )

    assert (
        "ACTION_REQUIRED"
        in prompt
    )

    assert (
        "VALIDATION_REJECTED"
        in prompt
    )

    assert (
        "REMEDIATE_VALIDATION"
        in prompt
    )


def test_disabled_provider_uses_deterministic_fallback():
    explanation = _sample_explanation()

    config = LLMProviderConfig(
        provider="disabled",
        model=None,
        api_key=None,
        timeout_seconds=30.0,
    )

    result = enhance_platform_explanation(
        explanation,
        config=config,
    )

    assert result["used_llm"] is False

    assert (
        result["fallback_reason"]
        == "provider_disabled"
    )

    assert (
        result["enhanced_explanation"]
        == explanation["explanation"]
    )

    assert (
        result["overall_state"]
        == "ACTION_REQUIRED"
    )


def test_gemini_enhances_text_without_changing_grounding():
    class FakeModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            assert (
                model
                == "gemini-test-model"
            )

            assert (
                "ACTION_REQUIRED"
                in contents
            )

            return SimpleNamespace(
                text=(
                    "Polished grounded "
                    "explanation."
                )
            )

    fake_client = SimpleNamespace(
        models=FakeModels()
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    explanation = _sample_explanation()

    result = enhance_platform_explanation(
        explanation,
        config=config,
        client=fake_client,
    )

    assert result["used_llm"] is True

    assert (
        result["enhanced_explanation"]
        == (
            "Polished grounded "
            "explanation."
        )
    )

    assert (
        result["overall_state"]
        == explanation["overall_state"]
    )

    assert (
        result["source_finding_codes"]
        == explanation[
            "source_finding_codes"
        ]
    )

    assert (
        result["source_action_codes"]
        == explanation[
            "source_action_codes"
        ]
    )


def test_provider_error_falls_back_to_deterministic_text():
    class FakeModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            raise RuntimeError(
                "provider unavailable"
            )

    fake_client = SimpleNamespace(
        models=FakeModels()
    )

    config = LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )

    explanation = _sample_explanation()

    result = enhance_platform_explanation(
        explanation,
        config=config,
        client=fake_client,
    )

    assert result["used_llm"] is False

    assert (
        result["fallback_reason"]
        == "provider_error"
    )

    assert (
        result["error_type"]
        == "RuntimeError"
    )

    assert (
        result["enhanced_explanation"]
        == explanation["explanation"]
    )