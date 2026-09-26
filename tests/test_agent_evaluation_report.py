import pytest

from src.assistant.evaluation_report import (
    build_agent_evaluation_report,
    build_agent_evaluation_report_from_observed,
    build_agent_evaluation_scenario,
    get_canonical_agent_evaluation_scenarios,
)


def test_evaluation_report_marks_matching_scenario_pass():
    report = build_agent_evaluation_report(
        [
            {
                "scenario_id": (
                    "answerable_comparison"
                ),
                "description": (
                    "Answerable comparison preserves "
                    "supported evidence."
                ),
                "expected": {
                    "answerability_status": (
                        "ANSWERABLE"
                    ),
                    "used_llm": True,
                },
                "observed": {
                    "answerability_status": (
                        "ANSWERABLE"
                    ),
                    "used_llm": True,
                },
            },
        ]
    )

    assert report == {
        "evaluation_version": "v1",
        "overall_status": "PASS",
        "scenario_count": 1,
        "passed_count": 1,
        "failed_count": 0,
        "scenarios": [
            {
                "scenario_id": (
                    "answerable_comparison"
                ),
                "description": (
                    "Answerable comparison preserves "
                    "supported evidence."
                ),
                "expected": {
                    "answerability_status": (
                        "ANSWERABLE"
                    ),
                    "used_llm": True,
                },
                "observed": {
                    "answerability_status": (
                        "ANSWERABLE"
                    ),
                    "used_llm": True,
                },
                "status": "PASS",
            },
        ],
    }


def test_evaluation_report_marks_mismatching_scenario_fail():
    report = build_agent_evaluation_report(
        [
            {
                "scenario_id": (
                    "partial_answerability_scoping"
                ),
                "description": (
                    "Restricted evidence must be "
                    "hidden before LLM invocation."
                ),
                "expected": {
                    "answerability_status": (
                        "PARTIAL"
                    ),
                    "restricted_payload_visible": (
                        False
                    ),
                },
                "observed": {
                    "answerability_status": (
                        "PARTIAL"
                    ),
                    "restricted_payload_visible": (
                        True
                    ),
                },
            },
        ]
    )

    assert report == {
        "evaluation_version": "v1",
        "overall_status": "FAIL",
        "scenario_count": 1,
        "passed_count": 0,
        "failed_count": 1,
        "scenarios": [
            {
                "scenario_id": (
                    "partial_answerability_scoping"
                ),
                "description": (
                    "Restricted evidence must be "
                    "hidden before LLM invocation."
                ),
                "expected": {
                    "answerability_status": (
                        "PARTIAL"
                    ),
                    "restricted_payload_visible": (
                        False
                    ),
                },
                "observed": {
                    "answerability_status": (
                        "PARTIAL"
                    ),
                    "restricted_payload_visible": (
                        True
                    ),
                },
                "status": "FAIL",
            },
        ],
    }


def test_evaluation_report_aggregates_mixed_results():
    report = build_agent_evaluation_report(
        [
            {
                "scenario_id": (
                    "answerable_comparison"
                ),
                "description": (
                    "Answerable comparison preserves "
                    "supported evidence."
                ),
                "expected": {
                    "answerability_status": (
                        "ANSWERABLE"
                    ),
                    "used_llm": True,
                },
                "observed": {
                    "answerability_status": (
                        "ANSWERABLE"
                    ),
                    "used_llm": True,
                },
            },
            {
                "scenario_id": (
                    "partial_answerability_scoping"
                ),
                "description": (
                    "Restricted evidence must be "
                    "hidden before LLM invocation."
                ),
                "expected": {
                    "answerability_status": (
                        "PARTIAL"
                    ),
                    "restricted_payload_visible": (
                        False
                    ),
                },
                "observed": {
                    "answerability_status": (
                        "PARTIAL"
                    ),
                    "restricted_payload_visible": (
                        True
                    ),
                },
            },
        ]
    )

    assert report["scenario_count"] == 2
    assert report["passed_count"] == 1
    assert report["failed_count"] == 1
    assert report["overall_status"] == "FAIL"

    assert [
        scenario["status"]
        for scenario in report["scenarios"]
    ] == [
        "PASS",
        "FAIL",
    ]


@pytest.mark.parametrize(
    "missing_field",
    [
        "scenario_id",
        "description",
        "expected",
        "observed",
    ],
)
def test_evaluation_report_rejects_missing_required_field(
    missing_field,
):
    scenario = {
        "scenario_id": "answerable_comparison",
        "description": (
            "Answerable comparison preserves "
            "supported evidence."
        ),
        "expected": {
            "used_llm": True,
        },
        "observed": {
            "used_llm": True,
        },
    }

    scenario.pop(
        missing_field
    )

    with pytest.raises(
        ValueError,
        match=missing_field,
    ):
        build_agent_evaluation_report(
            [
                scenario,
            ]
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "expected",
        "observed",
    ],
)
def test_evaluation_report_rejects_non_mapping_evidence(
    field_name,
):
    scenario = {
        "scenario_id": "answerable_comparison",
        "description": (
            "Answerable comparison preserves "
            "supported evidence."
        ),
        "expected": {
            "used_llm": True,
        },
        "observed": {
            "used_llm": True,
        },
    }

    scenario[field_name] = True

    with pytest.raises(
        ValueError,
        match=field_name,
    ):
        build_agent_evaluation_report(
            [
                scenario,
            ]
        )


def test_evaluation_report_marks_empty_run_not_applicable():
    report = build_agent_evaluation_report(
        []
    )

    assert report == {
        "evaluation_version": "v1",
        "overall_status": "NOT_APPLICABLE",
        "scenario_count": 0,
        "passed_count": 0,
        "failed_count": 0,
        "scenarios": [],
    }


def test_canonical_evaluation_scenarios_include_mutation_boundary():
    scenarios = (
        get_canonical_agent_evaluation_scenarios()
    )

    mutation_scenario = next(
        scenario
        for scenario in scenarios
        if scenario["scenario_id"]
        == "mutation_request_boundary"
    )

    assert mutation_scenario == {
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
            "stop_reason": "NO_TOOL_REQUESTS",
        },
    }


def test_canonical_evaluation_scenarios_cover_harness_v1():
    scenarios = (
        get_canonical_agent_evaluation_scenarios()
    )

    scenario_ids = [
        scenario["scenario_id"]
        for scenario in scenarios
    ]

    assert scenario_ids == [
        "not_answerable_response_gate",
        "partial_answerability_scoping",
        "empty_retrieval_availability",
        "unavailable_retrieval_availability",
        "cross_layer_partial_answerability",
        "cross_layer_not_answerable",
        "non_comparison_not_applicable",
        "mutation_request_boundary",
        "cross_layer_answerable",
    ]

    assert len(
        scenario_ids
    ) == len(
        set(scenario_ids)
    )


def test_build_evaluation_scenario_uses_canonical_contract():
    scenario = build_agent_evaluation_scenario(
        "mutation_request_boundary",
        observed={
            "planned_tool_count": 0,
            "attempted_tool_count": 0,
            "stop_reason": "NO_TOOL_REQUESTS",
        },
    )

    assert scenario == {
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
            "stop_reason": "NO_TOOL_REQUESTS",
        },
        "observed": {
            "planned_tool_count": 0,
            "attempted_tool_count": 0,
            "stop_reason": "NO_TOOL_REQUESTS",
        },
    }


def test_build_evaluation_scenario_rejects_unknown_scenario():
    with pytest.raises(
        ValueError,
        match="unknown_scenario",
    ):
        build_agent_evaluation_scenario(
            "unknown_scenario",
            observed={},
        )


def test_build_evaluation_report_from_observed_results():
    report = build_agent_evaluation_report_from_observed(
        {
            "not_answerable_response_gate": {
                "answerability_status": (
                    "NOT_ANSWERABLE"
                ),
                "used_llm": False,
                "provider": "deterministic",
                "fallback_reason": (
                    "historical_comparison_not_answerable"
                ),
            },
            "mutation_request_boundary": {
                "planned_tool_count": 0,
                "attempted_tool_count": 1,
                "stop_reason": "NO_TOOL_REQUESTS",
            },
        }
    )

    assert report["scenario_count"] == 2
    assert report["passed_count"] == 1
    assert report["failed_count"] == 1
    assert report["overall_status"] == "FAIL"

    assert [
        scenario["scenario_id"]
        for scenario in report["scenarios"]
    ] == [
        "not_answerable_response_gate",
        "mutation_request_boundary",
    ]

    assert [
        scenario["status"]
        for scenario in report["scenarios"]
    ] == [
        "PASS",
        "FAIL",
    ]


def test_cross_layer_answerable_contract_requires_visible_payloads():
    scenarios = (
        get_canonical_agent_evaluation_scenarios()
    )

    scenario = next(
        scenario
        for scenario in scenarios
        if scenario["scenario_id"]
        == "cross_layer_answerable"
    )

    assert scenario["expected"] == {
        "sufficiency_status": "SUFFICIENT",
        "answerability_status": "ANSWERABLE",
        "used_llm": True,
        "all_requested_payload_visible": True,
    }