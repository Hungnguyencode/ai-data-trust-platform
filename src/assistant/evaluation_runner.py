from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from src.assistant import controlled_tools
from src.assistant.evaluation_report import (
    build_agent_evaluation_report_from_observed,
)
from src.assistant.llm_provider import (
    LLMProviderConfig,
)
from src.assistant.platform_copilot import (
    answer_copilot_question,
)


def run_mutation_request_boundary_evaluation(
) -> dict[str, Any]:
    question = (
        "Promote this dataset and show "
        "freshness, pipeline, and alerts."
    )

    tool_requests = (
        controlled_tools
        .plan_controlled_tool_requests(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
        )
    )

    agent_run_summary: dict[str, Any] = {}

    controlled_tools.execute_bounded_controlled_tool_rounds(
        question,
        trusted_version_id=7,
        trusted_catalog_id=1,
        initial_tool_requests=tool_requests,
        agent_run_summary=agent_run_summary,
    )

    return {
        "planned_tool_count": len(
            tool_requests
        ),
        "attempted_tool_count": int(
            agent_run_summary[
                "attempted_tool_count"
            ]
        ),
        "stop_reason": str(
            agent_run_summary[
                "stop_reason"
            ]
        ),
    }


def _evaluation_diagnosis() -> dict[str, Any]:
    return {
        "catalog_id": 1,
        "latest_version_id": 7,
        "overall_state": "ACTION_REQUIRED",
        "findings": [
            {
                "code": "FRESHNESS_STALE",
                "category": "freshness",
                "severity": "HIGH",
                "message": (
                    "Dataset freshness is stale."
                ),
                "evidence": {
                    "freshness_status": "STALE",
                },
            },
        ],
        "recommended_actions": [
            {
                "code": "REFRESH_DATASET",
                "priority": 1,
                "action": "Refresh the dataset.",
                "reason": (
                    "The latest freshness check "
                    "is stale."
                ),
            },
        ],
        "summary": {
            "finding_count": 1,
            "high_count": 1,
            "warning_count": 0,
            "info_count": 0,
            "action_count": 1,
        },
    }


def _evaluation_explanation() -> dict[str, Any]:
    return {
        "catalog_id": 1,
        "latest_version_id": 7,
        "overall_state": "ACTION_REQUIRED",
        "headline": (
            "Dataset requires action."
        ),
        "summary": (
            "Freshness evidence requires "
            "operator attention."
        ),
        "explanation": (
            "Dataset requires action because "
            "the latest freshness check is stale."
        ),
        "source_finding_codes": [
            "FRESHNESS_STALE",
        ],
        "source_action_codes": [
            "REFRESH_DATASET",
        ],
    }


def _build_evidence_assessment(
    *,
    question: str,
    requested_evidence: list[str],
    controlled_tool_results: list[dict[str, Any]],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    evidence_sufficiency = (
        controlled_tools
        .build_controlled_evidence_sufficiency(
            requested_evidence=(
                requested_evidence
            ),
            controlled_tool_results=(
                controlled_tool_results
            ),
        )
    )

    evidence_answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=question,
            evidence_sufficiency=(
                evidence_sufficiency
            ),
        )
    )

    return (
        evidence_sufficiency,
        evidence_answerability,
    )


def _evaluation_llm_config(
) -> LLMProviderConfig:
    return LLMProviderConfig(
        provider="gemini",
        model="gemini-test-model",
        api_key="fake-key",
        timeout_seconds=30.0,
    )


def _run_copilot_evaluation(
    *,
    question: str,
    controlled_tool_results: list[
        dict[str, Any]
    ],
    evidence_answerability: dict[
        str,
        Any,
    ],
    models: Any,
) -> dict[str, Any]:
    return answer_copilot_question(
        question,
        _evaluation_diagnosis(),
        _evaluation_explanation(),
        controlled_tool_results=(
            controlled_tool_results
        ),
        agent_evidence_answerability=(
            evidence_answerability
        ),
        config=_evaluation_llm_config(),
        client=SimpleNamespace(
            models=models
        ),
    )


def run_not_answerable_response_gate_evaluation(
) -> dict[str, Any]:
    question = (
        "Compare freshness history over time."
    )

    controlled_tool_results = [
        {
            "name": "get_freshness_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "record_id": "freshness-1",
                },
            ],
        },
    ]

    evidence_sufficiency, evidence_answerability = (
        _build_evidence_assessment(
            question=question,
            requested_evidence=[
                "freshness_history",
            ],
            controlled_tool_results=(
                controlled_tool_results
            ),
        )
    )

    class FailIfCalledModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            del model
            del contents

            raise AssertionError(
                "LLM provider must not be called "
                "for NOT_ANSWERABLE evidence."
            )

    result = _run_copilot_evaluation(
        question=question,
        controlled_tool_results=(
            controlled_tool_results
        ),
        evidence_answerability=(
            evidence_answerability
        ),
        models=FailIfCalledModels(),
    )

    return {
        "answerability_status": str(
            evidence_answerability[
                "answerability_status"
            ]
        ),
        "used_llm": bool(
            result["used_llm"]
        ),
        "provider": str(
            result["provider"]
        ),
        "fallback_reason": str(
            result["fallback_reason"]
        ),
    }


def run_partial_answerability_scoping_evaluation(
) -> dict[str, Any]:
    question = (
        "Compare freshness and volume "
        "history over time."
    )

    controlled_tool_results = [
        {
            "name": "get_freshness_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": (
                        "freshness-allowed-marker"
                    ),
                },
                {
                    "marker": (
                        "freshness-allowed-marker-2"
                    ),
                },
            ],
        },
        {
            "name": "get_volume_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": (
                        "volume-restricted-marker"
                    ),
                },
            ],
        },
    ]

    evidence_sufficiency = (
        controlled_tools
        .build_controlled_evidence_sufficiency(
            requested_evidence=[
                "freshness_history",
                "volume_history",
            ],
            controlled_tool_results=(
                controlled_tool_results
            ),
        )
    )

    evidence_answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=question,
            evidence_sufficiency=(
                evidence_sufficiency
            ),
        )
    )

    prompt_observation = {
        "restricted_payload_visible": False,
    }

    class InspectPromptModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            del model

            prompt_observation[
                "restricted_payload_visible"
            ] = (
                "volume-restricted-marker"
                in contents
            )

            return SimpleNamespace(
                text=(
                    "Freshness comparison is "
                    "supported while volume "
                    "comparison is limited."
                )
            )

    result = _run_copilot_evaluation(
        question=question,
        controlled_tool_results=(
            controlled_tool_results
        ),
        evidence_answerability=(
            evidence_answerability
        ),
        models=InspectPromptModels(),
    )

    return {
        "answerability_status": str(
            evidence_answerability[
                "answerability_status"
            ]
        ),
        "used_llm": bool(
            result["used_llm"]
        ),
        "restricted_payload_visible": bool(
            prompt_observation[
                "restricted_payload_visible"
            ]
        ),
    }


def run_empty_retrieval_availability_evaluation(
) -> dict[str, Any]:
    evidence_sufficiency = (
        controlled_tools
        .build_controlled_evidence_sufficiency(
            requested_evidence=[
                "freshness_history",
            ],
            controlled_tool_results=[
                {
                    "name": (
                        "get_freshness_history"
                    ),
                    "read_only": True,
                    "ok": True,
                    "result": [],
                },
            ],
        )
    )

    evidence_detail = (
        evidence_sufficiency[
            "evidence_details"
        ][0]
    )

    return {
        "availability_status": str(
            evidence_detail[
                "availability_status"
            ]
        ),
        "item_count": (
            evidence_detail[
                "item_count"
            ]
        ),
    }


def run_unavailable_retrieval_availability_evaluation(
) -> dict[str, Any]:
    evidence_sufficiency = (
        controlled_tools
        .build_controlled_evidence_sufficiency(
            requested_evidence=[
                "freshness_history",
            ],
            controlled_tool_results=[],
        )
    )

    evidence_detail = (
        evidence_sufficiency[
            "evidence_details"
        ][0]
    )

    return {
        "availability_status": str(
            evidence_detail[
                "availability_status"
            ]
        ),
        "item_count": (
            evidence_detail[
                "item_count"
            ]
        ),
    }


def run_cross_layer_partial_answerability_evaluation(
) -> dict[str, Any]:
    question = (
        "Compare freshness and volume "
        "history over time."
    )

    controlled_tool_results = [
        {
            "name": "get_freshness_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": "freshness-1",
                },
                {
                    "marker": "freshness-2",
                },
            ],
        },
        {
            "name": "get_volume_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": (
                        "volume-restricted-marker"
                    ),
                },
            ],
        },
    ]

    evidence_sufficiency = (
        controlled_tools
        .build_controlled_evidence_sufficiency(
            requested_evidence=[
                "freshness_history",
                "volume_history",
            ],
            controlled_tool_results=(
                controlled_tool_results
            ),
        )
    )

    evidence_answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=question,
            evidence_sufficiency=(
                evidence_sufficiency
            ),
        )
    )

    prompt_observation = {
        "restricted_payload_visible": False,
    }

    class InspectPromptModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            del model

            prompt_observation[
                "restricted_payload_visible"
            ] = (
                "volume-restricted-marker"
                in contents
            )

            return SimpleNamespace(
                text=(
                    "Freshness comparison is "
                    "supported while volume "
                    "comparison is limited."
                )
            )

    _run_copilot_evaluation(
        question=question,
        controlled_tool_results=(
            controlled_tool_results
        ),
        evidence_answerability=(
            evidence_answerability
        ),
        models=InspectPromptModels(),
    )

    return {
        "sufficiency_status": str(
            evidence_sufficiency[
                "sufficiency_status"
            ]
        ),
        "answerability_status": str(
            evidence_answerability[
                "answerability_status"
            ]
        ),
        "restricted_payload_visible": bool(
            prompt_observation[
                "restricted_payload_visible"
            ]
        ),
    }


def run_cross_layer_not_answerable_evaluation(
) -> dict[str, Any]:
    question = (
        "Compare freshness and volume "
        "history over time."
    )

    controlled_tool_results = [
        {
            "name": "get_freshness_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": "freshness-1",
                },
            ],
        },
        {
            "name": "get_volume_history",
            "read_only": True,
            "ok": True,
            "result": [],
        },
    ]

    evidence_sufficiency = (
        controlled_tools
        .build_controlled_evidence_sufficiency(
            requested_evidence=[
                "freshness_history",
                "volume_history",
            ],
            controlled_tool_results=(
                controlled_tool_results
            ),
        )
    )

    evidence_answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=question,
            evidence_sufficiency=(
                evidence_sufficiency
            ),
        )
    )

    class FailIfCalledModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            del model
            del contents

            raise AssertionError(
                "LLM provider must not be called "
                "for NOT_ANSWERABLE evidence."
            )

    result = _run_copilot_evaluation(
        question=question,
        controlled_tool_results=(
            controlled_tool_results
        ),
        evidence_answerability=(
            evidence_answerability
        ),
        models=FailIfCalledModels(),
    )

    return {
        "sufficiency_status": str(
            evidence_sufficiency[
                "sufficiency_status"
            ]
        ),
        "answerability_status": str(
            evidence_answerability[
                "answerability_status"
            ]
        ),
        "used_llm": bool(
            result["used_llm"]
        ),
    }


def run_non_comparison_not_applicable_evaluation(
) -> dict[str, Any]:
    question = (
        "Show freshness history."
    )

    controlled_tool_results = [
        {
            "name": "get_freshness_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": "freshness-1",
                },
            ],
        },
    ]

    evidence_sufficiency = (
        controlled_tools
        .build_controlled_evidence_sufficiency(
            requested_evidence=[
                "freshness_history",
            ],
            controlled_tool_results=(
                controlled_tool_results
            ),
        )
    )

    evidence_answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=question,
            evidence_sufficiency=(
                evidence_sufficiency
            ),
        )
    )

    provider_observation = {
        "called": False,
    }

    class ObserveProviderModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            del model
            del contents

            provider_observation[
                "called"
            ] = True

            return SimpleNamespace(
                text=(
                    "Freshness history is "
                    "available."
                )
            )

    result = _run_copilot_evaluation(
        question=question,
        controlled_tool_results=(
            controlled_tool_results
        ),
        evidence_answerability=(
            evidence_answerability
        ),
        models=ObserveProviderModels(),
    )

    return {
        "answerability_status": str(
            evidence_answerability[
                "answerability_status"
            ]
        ),
        "used_llm": bool(
            result["used_llm"]
            and provider_observation[
                "called"
            ]
        ),
    }


def run_cross_layer_answerable_evaluation(
) -> dict[str, Any]:
    question = (
        "Compare freshness and volume "
        "history over time."
    )

    controlled_tool_results = [
        {
            "name": "get_freshness_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": (
                        "freshness-visible-marker-1"
                    ),
                },
                {
                    "marker": (
                        "freshness-visible-marker-2"
                    ),
                },
            ],
        },
        {
            "name": "get_volume_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": (
                        "volume-visible-marker-1"
                    ),
                },
                {
                    "marker": (
                        "volume-visible-marker-2"
                    ),
                },
            ],
        },
    ]

    evidence_sufficiency = (
        controlled_tools
        .build_controlled_evidence_sufficiency(
            requested_evidence=[
                "freshness_history",
                "volume_history",
            ],
            controlled_tool_results=(
                controlled_tool_results
            ),
        )
    )

    evidence_answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=question,
            evidence_sufficiency=(
                evidence_sufficiency
            ),
        )
    )

    prompt_observation = {
        "freshness_visible": False,
        "volume_visible": False,
        "provider_called": False,
    }

    class InspectPromptModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            del model

            prompt_observation[
                "provider_called"
            ] = True

            prompt_observation[
                "freshness_visible"
            ] = (
                "freshness-visible-marker-1"
                in contents
            )

            prompt_observation[
                "volume_visible"
            ] = (
                "volume-visible-marker-1"
                in contents
            )

            return SimpleNamespace(
                text=(
                    "Freshness and volume "
                    "comparison is supported."
                )
            )

    result = _run_copilot_evaluation(
        question=question,
        controlled_tool_results=(
            controlled_tool_results
        ),
        evidence_answerability=(
            evidence_answerability
        ),
        models=InspectPromptModels(),
    )

    _run_copilot_evaluation(
        question=question,
        controlled_tool_results=(
            controlled_tool_results
        ),
        evidence_answerability=(
            evidence_answerability
        ),
        models=InspectPromptModels(),
    )

    return {
        "sufficiency_status": str(
            evidence_sufficiency[
                "sufficiency_status"
            ]
        ),
        "answerability_status": str(
            evidence_answerability[
                "answerability_status"
            ]
        ),
        "used_llm": bool(
            result["used_llm"]
            and prompt_observation[
                "provider_called"
            ]
        ),
        "all_requested_payload_visible": (
            bool(
                prompt_observation[
                    "freshness_visible"
                ]
            )
            and bool(
                prompt_observation[
                    "volume_visible"
                ]
            )
        ),
    }


def run_agent_evaluation_suite(
) -> dict[str, Any]:
    observed_results = {
        "not_answerable_response_gate": (
            run_not_answerable_response_gate_evaluation()
        ),
        "partial_answerability_scoping": (
            run_partial_answerability_scoping_evaluation()
        ),
        "empty_retrieval_availability": (
            run_empty_retrieval_availability_evaluation()
        ),
        "unavailable_retrieval_availability": (
            run_unavailable_retrieval_availability_evaluation()
        ),
        "cross_layer_partial_answerability": (
            run_cross_layer_partial_answerability_evaluation()
        ),
        "cross_layer_not_answerable": (
            run_cross_layer_not_answerable_evaluation()
        ),
        "non_comparison_not_applicable": (
            run_non_comparison_not_applicable_evaluation()
        ),
        "mutation_request_boundary": (
            run_mutation_request_boundary_evaluation()
        ),
        "cross_layer_answerable": (
            run_cross_layer_answerable_evaluation()
        ),
    }

    return (
        build_agent_evaluation_report_from_observed(
            observed_results
        )
    )
