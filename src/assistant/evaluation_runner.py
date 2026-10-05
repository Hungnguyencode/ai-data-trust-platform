from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

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
    claim_scoped_controlled_tool_results: (
        list[dict[str, Any]] | None
    ) = None,
) -> dict[str, Any]:
    return answer_copilot_question(
        question,
        _evaluation_diagnosis(),
        _evaluation_explanation(),
        controlled_tool_results=(
            controlled_tool_results
        ),
        claim_scoped_controlled_tool_results=(
            claim_scoped_controlled_tool_results
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


def run_cross_domain_investigation_evaluation(
) -> dict[str, Any]:
    question = (
        "Why is this dataset currently unhealthy?"
    )

    initial_tool_requests = (
        controlled_tools
        .plan_controlled_tool_requests(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
        )
    )

    agent_run_summary: dict[str, Any] = {}
    agent_evidence_coverage: dict[str, Any] = {}
    agent_evidence_sufficiency: dict[
        str,
        Any,
    ] = {}

    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": (
                        f"{name}-evaluation-evidence"
                    ),
                },
            ],
        }

    with patch.object(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    ):
        controlled_tool_results = (
            controlled_tools
            .execute_bounded_controlled_tool_rounds(
                question,
                trusted_version_id=7,
                trusted_catalog_id=1,
                initial_tool_requests=(
                    initial_tool_requests
                ),
                agent_run_summary=(
                    agent_run_summary
                ),
                agent_evidence_coverage=(
                    agent_evidence_coverage
                ),
                agent_evidence_sufficiency=(
                    agent_evidence_sufficiency
                ),
            )
        )

    claim_evidence_assessments = (
        controlled_tools
        .build_claim_scoped_evidence_assessments(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
            evidence_sufficiency=(
                agent_evidence_sufficiency
            ),
        )
    )

    claim_scoped_results = (
        controlled_tools
        .build_claim_scoped_controlled_tool_results(
            controlled_tool_results=(
                controlled_tool_results
            ),
            claim_evidence_assessments=(
                claim_evidence_assessments
            ),
        )
    )

    current_scope = next(
        scope
        for scope in claim_scoped_results
        if scope["claim_type"] == "CURRENT_STATE"
    )

    return {
        "requested_evidence_count": len(
            agent_evidence_coverage[
                "requested_evidence"
            ]
        ),
        "attempted_tool_count": int(
            agent_run_summary[
                "attempted_tool_count"
            ]
        ),
        "accepted_evidence_count": int(
            agent_run_summary[
                "accepted_evidence_count"
            ]
        ),
        "round_count": int(
            agent_run_summary[
                "round_count"
            ]
        ),
        "coverage_status": str(
            agent_evidence_coverage[
                "coverage_status"
            ]
        ),
        "sufficiency_status": str(
            agent_evidence_sufficiency[
                "sufficiency_status"
            ]
        ),
        "claim_type": str(
            current_scope[
                "claim_type"
            ]
        ),
        "claim_answerability_status": str(
            current_scope[
                "answerability_status"
            ]
        ),
        "permitted_evidence_count": len(
            current_scope[
                "permitted_evidence"
            ]
        ),
    }


def run_cross_domain_response_provenance_evaluation(
) -> dict[str, Any]:
    question = (
        "Why is this dataset currently unhealthy?"
    )

    initial_tool_requests = (
        controlled_tools
        .plan_controlled_tool_requests(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
        )
    )

    agent_run_summary: dict[str, Any] = {}
    agent_evidence_coverage: dict[str, Any] = {}
    agent_evidence_sufficiency: dict[
        str,
        Any,
    ] = {}

    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": (
                        f"{name}-provenance-evidence"
                    ),
                },
            ],
        }

    with patch.object(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    ):
        controlled_tool_results = (
            controlled_tools
            .execute_bounded_controlled_tool_rounds(
                question,
                trusted_version_id=7,
                trusted_catalog_id=1,
                initial_tool_requests=(
                    initial_tool_requests
                ),
                agent_run_summary=(
                    agent_run_summary
                ),
                agent_evidence_coverage=(
                    agent_evidence_coverage
                ),
                agent_evidence_sufficiency=(
                    agent_evidence_sufficiency
                ),
            )
        )

    evidence_answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=question,
            evidence_sufficiency=(
                agent_evidence_sufficiency
            ),
        )
    )

    claim_evidence_assessments = (
        controlled_tools
        .build_claim_scoped_evidence_assessments(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
            evidence_sufficiency=(
                agent_evidence_sufficiency
            ),
        )
    )

    claim_scoped_controlled_tool_results = (
        controlled_tools
        .build_claim_scoped_controlled_tool_results(
            controlled_tool_results=(
                controlled_tool_results
            ),
            claim_evidence_assessments=(
                claim_evidence_assessments
            ),
        )
    )

    provider_observation = {
        "call_count": 0,
    }

    class InspectPromptModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            del model
            del contents

            provider_observation[
                "call_count"
            ] += 1

            return SimpleNamespace(
                text=(
                    "Cross-domain evidence supports "
                    "the current diagnosis."
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
        claim_scoped_controlled_tool_results=(
            claim_scoped_controlled_tool_results
        ),
        models=InspectPromptModels(),
    )

    provenance = list(
        result.get(
            "claim_response_provenance",
            [],
        )
        or []
    )

    claim = (
        provenance[0]
        if len(provenance) == 1
        else {}
    )

    evidence_requirements = list(
        claim.get(
            "evidence_requirements",
            [],
        )
        or []
    )

    evidence_tool_names = list(
        claim.get(
            "evidence_tool_names",
            [],
        )
        or []
    )

    raw_evidence_payload_exposed = any(
        (
            "controlled_tool_results" in item
            or "result" in item
        )
        for item in provenance
        if isinstance(item, dict)
    )

    return {
        "claim_count": len(provenance),
        "claim_type": str(
            claim.get(
                "claim_type",
                "",
            )
        ),
        "answerability_status": str(
            claim.get(
                "answerability_status",
                "",
            )
        ),
        "response_mode": str(
            claim.get(
                "response_mode",
                "",
            )
        ),
        "evidence_tool_count": len(
            evidence_tool_names
        ),
        "evidence_requirement_count": len(
            evidence_requirements
        ),
        "all_requirements_satisfied": (
            bool(evidence_requirements)
            and all(
                requirement.get(
                    "requirement_status"
                )
                == "SATISFIED"
                for requirement
                in evidence_requirements
            )
        ),
        "used_llm": bool(
            claim.get(
                "used_llm",
                False,
            )
            and provider_observation[
                "call_count"
            ]
            == 1
        ),
        "raw_evidence_payload_exposed": (
            raw_evidence_payload_exposed
        ),
    }


def run_mixed_claim_scoped_answerability_evaluation(
) -> dict[str, Any]:
    question = (
        "Compare volume over time "
        "and tell me the latest volume."
    )

    controlled_tool_results = [
        {
            "name": "get_volume_history",
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "marker": "volume-latest-1",
                },
            ],
        },
    ]

    evidence_sufficiency, evidence_answerability = (
        _build_evidence_assessment(
            question=question,
            requested_evidence=[
                "volume_history",
            ],
            controlled_tool_results=(
                controlled_tool_results
            ),
        )
    )

    claim_evidence_assessments = (
        controlled_tools
        .build_claim_scoped_evidence_assessments(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
            evidence_sufficiency=(
                evidence_sufficiency
            ),
        )
    )

    claim_scoped_controlled_tool_results = (
        controlled_tools
        .build_claim_scoped_controlled_tool_results(
            controlled_tool_results=(
                controlled_tool_results
            ),
            claim_evidence_assessments=(
                claim_evidence_assessments
            ),
        )
    )

    historical_scope = next(
        scope
        for scope
        in claim_scoped_controlled_tool_results
        if scope["claim_type"]
        == "HISTORICAL_COMPARISON"
    )

    current_scope = next(
        scope
        for scope
        in claim_scoped_controlled_tool_results
        if scope["claim_type"]
        == "CURRENT_STATE"
    )

    provider_observation = {
        "called": False,
    }

    class InspectPromptModels:
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
                    "Historical comparison is "
                    "unsupported, while the latest "
                    "volume is available."
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
        claim_scoped_controlled_tool_results=(
            claim_scoped_controlled_tool_results
        ),
        models=InspectPromptModels(),
    )

    return {
        "historical_claim_status": str(
            historical_scope[
                "answerability_status"
            ]
        ),
        "current_claim_status": str(
            current_scope[
                "answerability_status"
            ]
        ),
        "historical_payload_count": len(
            historical_scope[
                "controlled_tool_results"
            ]
        ),
        "current_payload_count": len(
            current_scope[
                "controlled_tool_results"
            ]
        ),
        "used_llm": bool(
            result["used_llm"]
            and provider_observation["called"]
        ),
    }


def run_claim_level_response_isolation_evaluation(
) -> dict[str, Any]:
    question = (
        "Compare volume over time "
        "and tell me the latest volume."
    )

    volume_result = {
        "name": "get_volume_history",
        "read_only": True,
        "ok": True,
        "result": [
            {
                "marker": (
                    "supported-volume-only"
                ),
            },
        ],
    }

    unrelated_result = {
        "name": "get_pipeline_run_history",
        "read_only": True,
        "ok": True,
        "result": [
            {
                "marker": (
                    "cross-claim-payload-"
                    "must-not-leak"
                ),
            },
        ],
    }

    controlled_tool_results = [
        volume_result,
        unrelated_result,
    ]

    (
        evidence_sufficiency,
        evidence_answerability,
    ) = _build_evidence_assessment(
        question=question,
        requested_evidence=[
            "volume_history",
        ],
        controlled_tool_results=(
            controlled_tool_results
        ),
    )

    claim_evidence_assessments = (
        controlled_tools
        .build_claim_scoped_evidence_assessments(
            question,
            trusted_version_id=7,
            trusted_catalog_id=1,
            evidence_sufficiency=(
                evidence_sufficiency
            ),
        )
    )

    claim_scoped_controlled_tool_results = (
        controlled_tools
        .build_claim_scoped_controlled_tool_results(
            controlled_tool_results=(
                controlled_tool_results
            ),
            claim_evidence_assessments=(
                claim_evidence_assessments
            ),
        )
    )

    provider_observation = {
        "call_count": 0,
        "contents": "",
    }

    class InspectPromptModels:
        def generate_content(
            self,
            *,
            model,
            contents,
        ):
            del model

            provider_observation[
                "call_count"
            ] += 1

            provider_observation[
                "contents"
            ] = contents

            return SimpleNamespace(
                text=(
                    "The latest volume is "
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
        claim_scoped_controlled_tool_results=(
            claim_scoped_controlled_tool_results
        ),
        models=InspectPromptModels(),
    )

    prompt = str(
        provider_observation["contents"]
    )

    answer = str(
        result["answer"]
    )

    provenance = list(
        result.get(
            "claim_response_provenance",
            [],
        )
        or []
    )

    unsupported_provenance = (
        provenance[0]
        if len(provenance) > 0
        else {}
    )

    supported_provenance = (
        provenance[1]
        if len(provenance) > 1
        else {}
    )

    raw_evidence_payload_exposed = any(
        (
            "controlled_tool_results" in item
            or "result" in item
        )
        for item in provenance
        if isinstance(item, dict)
    )

    return {
        "provider_call_count": (
            provider_observation[
                "call_count"
            ]
        ),
        "supported_claim_visible": (
            "tell me the latest volume."
            in prompt
        ),
        "unsupported_claim_visible": (
            "Compare volume over time"
            in prompt
        ),
        "supported_payload_visible": (
            "supported-volume-only"
            in prompt
        ),
        "cross_claim_payload_visible": (
            "cross-claim-payload-"
            "must-not-leak"
            in prompt
        ),
        "deterministic_limitation_visible": (
            "Platform evidence is insufficient "
            "for the requested historical "
            "comparison."
            in answer
        ),
        "supported_answer_visible": (
            "The latest volume is available."
            in answer
        ),
        "provenance_claim_count": len(
            provenance
        ),
        "unsupported_provenance_tool_count": len(
            list(
                unsupported_provenance.get(
                    "evidence_tool_names",
                    [],
                )
                or []
            )
        ),
        "supported_provenance_tool_names": list(
            supported_provenance.get(
                "evidence_tool_names",
                [],
            )
            or []
        ),
        "supported_provenance_provider": (
            supported_provenance.get(
                "provider"
            )
        ),
        "supported_provenance_used_llm": bool(
            supported_provenance.get(
                "used_llm",
                False,
            )
        ),
        "unsupported_provenance_evidence_requirements": list(
            unsupported_provenance.get(
                "evidence_requirements",
                [],
            )
            or []
        ),
        "supported_provenance_evidence_requirements": list(
            supported_provenance.get(
                "evidence_requirements",
                [],
            )
            or []
        ),
        "raw_evidence_payload_exposed": (
            raw_evidence_payload_exposed
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
        "cross_domain_investigation": (
            run_cross_domain_investigation_evaluation()
        ),
        "cross_domain_response_provenance": (
            run_cross_domain_response_provenance_evaluation()
        ),
        "mixed_claim_scoped_answerability": (
            run_mixed_claim_scoped_answerability_evaluation()
        ),
        "claim_level_response_isolation": (
            run_claim_level_response_isolation_evaluation()
        ),
    }

    return (
        build_agent_evaluation_report_from_observed(
            observed_results
        )
    )
