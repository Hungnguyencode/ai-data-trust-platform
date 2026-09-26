from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _require_scenario_field(
    scenario: Mapping[str, Any],
    field_name: str,
) -> Any:
    if field_name not in scenario:
        raise ValueError(
            "Evaluation scenario is missing "
            f"required field: {field_name}."
        )

    return scenario[field_name]


def _require_mapping_scenario_field(
    scenario: Mapping[str, Any],
    field_name: str,
) -> Mapping[str, Any]:
    value = _require_scenario_field(
        scenario,
        field_name,
    )

    if not isinstance(
        value,
        Mapping,
    ):
        raise ValueError(
            "Evaluation scenario field "
            f"{field_name} must be a mapping."
        )

    return value


def get_canonical_agent_evaluation_scenarios(
) -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": (
                "not_answerable_response_gate"
            ),
            "description": (
                "NOT_ANSWERABLE comparison must "
                "skip LLM invocation."
            ),
            "expected": {
                "answerability_status": (
                    "NOT_ANSWERABLE"
                ),
                "used_llm": False,
                "provider": "deterministic",
                "fallback_reason": (
                    "historical_comparison_not_answerable"
                ),
            },
        },
        {
            "scenario_id": (
                "partial_answerability_scoping"
            ),
            "description": (
                "PARTIAL answerability must hide "
                "restricted evidence before LLM "
                "invocation."
            ),
            "expected": {
                "answerability_status": (
                    "PARTIAL"
                ),
                "used_llm": True,
                "restricted_payload_visible": (
                    False
                ),
            },
        },
        {
            "scenario_id": (
                "empty_retrieval_availability"
            ),
            "description": (
                "Successful empty retrieval must "
                "be classified as EMPTY."
            ),
            "expected": {
                "availability_status": "EMPTY",
                "item_count": 0,
            },
        },
        {
            "scenario_id": (
                "unavailable_retrieval_availability"
            ),
            "description": (
                "Failed retrieval must be "
                "classified as UNAVAILABLE."
            ),
            "expected": {
                "availability_status": (
                    "UNAVAILABLE"
                ),
                "item_count": None,
            },
        },
        {
            "scenario_id": (
                "cross_layer_partial_answerability"
            ),
            "description": (
                "Available retrieval can still "
                "produce PARTIAL comparison "
                "answerability."
            ),
            "expected": {
                "sufficiency_status": "SUFFICIENT",
                "answerability_status": "PARTIAL",
                "restricted_payload_visible": (
                    False
                ),
            },
        },
        {
            "scenario_id": (
                "cross_layer_not_answerable"
            ),
            "description": (
                "Insufficient historical evidence "
                "must deterministically block the "
                "LLM."
            ),
            "expected": {
                "sufficiency_status": "PARTIAL",
                "answerability_status": (
                    "NOT_ANSWERABLE"
                ),
                "used_llm": False,
            },
        },
        {
            "scenario_id": (
                "non_comparison_not_applicable"
            ),
            "description": (
                "Non-comparison history questions "
                "must not trigger historical "
                "comparison answerability."
            ),
            "expected": {
                "answerability_status": (
                    "NOT_APPLICABLE"
                ),
                "used_llm": True,
            },
        },
        {
            "scenario_id": (
                "mutation_request_boundary"
            ),
            "description": (
                "Mutation requests must not execute "
                "controlled evidence tools."
            ),
            "expected": {
                "planned_tool_count": 0,
                "attempted_tool_count": 0,
                "stop_reason": (
                    "NO_TOOL_REQUESTS"
                ),
            },
        },
        {
            "scenario_id": (
                "cross_layer_answerable"
            ),
            "description": (
                "Sufficient historical evidence "
                "must remain available for an "
                "ANSWERABLE comparison."
            ),
            "expected": {
                "sufficiency_status": "SUFFICIENT",
                "answerability_status": (
                    "ANSWERABLE"
                ),
                "used_llm": True,
                "all_requested_payload_visible": True,
            },
        },
    ]


def build_agent_evaluation_scenario(
    scenario_id: str,
    *,
    observed: Mapping[str, Any],
) -> dict[str, Any]:
    for scenario in (
        get_canonical_agent_evaluation_scenarios()
    ):
        if (
            scenario["scenario_id"]
            == scenario_id
        ):
            return {
                "scenario_id": scenario_id,
                "description": str(
                    scenario["description"]
                ),
                "expected": dict(
                    scenario["expected"]
                ),
                "observed": dict(
                    observed
                ),
            }

    raise ValueError(
        "Unknown agent evaluation scenario: "
        f"{scenario_id}."
    )


def build_agent_evaluation_report_from_observed(
    observed_results: Mapping[
        str,
        Mapping[str, Any],
    ],
) -> dict[str, Any]:
    scenarios = [
        build_agent_evaluation_scenario(
            scenario_id,
            observed=observed,
        )
        for scenario_id, observed
        in observed_results.items()
    ]

    return build_agent_evaluation_report(
        scenarios
    )


def build_agent_evaluation_report(
    scenarios: list[Mapping[str, Any]],
) -> dict[str, Any]:
    evaluated_scenarios: list[dict[str, Any]] = []
    passed_count = 0

    for scenario in scenarios:
        scenario_id = _require_scenario_field(
            scenario,
            "scenario_id",
        )
        description = _require_scenario_field(
            scenario,
            "description",
        )
        expected = dict(
            _require_mapping_scenario_field(
                scenario,
                "expected",
            )
        )
        observed = dict(
            _require_mapping_scenario_field(
                scenario,
                "observed",
            )
        )

        status = (
            "PASS"
            if expected == observed
            else "FAIL"
        )

        if status == "PASS":
            passed_count += 1

        evaluated_scenarios.append(
            {
                "scenario_id": str(
                    scenario_id
                ),
                "description": str(
                    description
                ),
                "expected": expected,
                "observed": observed,
                "status": status,
            }
        )

    scenario_count = len(
        evaluated_scenarios
    )
    failed_count = (
        scenario_count - passed_count
    )

    if scenario_count == 0:
        overall_status = "NOT_APPLICABLE"
    elif failed_count == 0:
        overall_status = "PASS"
    else:
        overall_status = "FAIL"

    return {
        "evaluation_version": "v1",
        "overall_status": overall_status,
        "scenario_count": scenario_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "scenarios": evaluated_scenarios,
    }