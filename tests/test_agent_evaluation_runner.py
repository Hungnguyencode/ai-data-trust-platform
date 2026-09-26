from src.assistant.evaluation_runner import (
    run_agent_evaluation_suite,
    run_cross_layer_answerable_evaluation,
    run_cross_layer_not_answerable_evaluation,
    run_cross_layer_partial_answerability_evaluation,
    run_empty_retrieval_availability_evaluation,
    run_mutation_request_boundary_evaluation,
    run_non_comparison_not_applicable_evaluation,
    run_not_answerable_response_gate_evaluation,
    run_partial_answerability_scoping_evaluation,
    run_unavailable_retrieval_availability_evaluation,
)


def test_mutation_request_boundary_evaluation_uses_real_agent_path():
    observed = (
        run_mutation_request_boundary_evaluation()
    )

    assert observed == {
        "planned_tool_count": 0,
        "attempted_tool_count": 0,
        "stop_reason": "NO_TOOL_REQUESTS",
    }


def test_not_answerable_response_gate_uses_real_copilot_path():
    observed = (
        run_not_answerable_response_gate_evaluation()
    )

    assert observed == {
        "answerability_status": (
            "NOT_ANSWERABLE"
        ),
        "used_llm": False,
        "provider": "deterministic",
        "fallback_reason": (
            "historical_comparison_not_answerable"
        ),
    }


def test_partial_answerability_scoping_uses_real_copilot_path():
    observed = (
        run_partial_answerability_scoping_evaluation()
    )

    assert observed == {
        "answerability_status": "PARTIAL",
        "used_llm": True,
        "restricted_payload_visible": False,
    }


def test_empty_retrieval_availability_uses_real_evidence_logic():
    observed = (
        run_empty_retrieval_availability_evaluation()
    )

    assert observed == {
        "availability_status": "EMPTY",
        "item_count": 0,
    }


def test_unavailable_retrieval_availability_uses_real_evidence_logic():
    observed = (
        run_unavailable_retrieval_availability_evaluation()
    )

    assert observed == {
        "availability_status": "UNAVAILABLE",
        "item_count": None,
    }


def test_cross_layer_partial_answerability_uses_real_pipeline():
    observed = (
        run_cross_layer_partial_answerability_evaluation()
    )

    assert observed == {
        "sufficiency_status": "SUFFICIENT",
        "answerability_status": "PARTIAL",
        "restricted_payload_visible": False,
    }


def test_cross_layer_not_answerable_uses_real_pipeline():
    observed = (
        run_cross_layer_not_answerable_evaluation()
    )

    assert observed == {
        "sufficiency_status": "PARTIAL",
        "answerability_status": (
            "NOT_ANSWERABLE"
        ),
        "used_llm": False,
    }


def test_non_comparison_not_applicable_uses_real_pipeline():
    observed = (
        run_non_comparison_not_applicable_evaluation()
    )

    assert observed == {
        "answerability_status": (
            "NOT_APPLICABLE"
        ),
        "used_llm": True,
    }


def test_cross_layer_answerable_uses_real_pipeline():
    observed = (
        run_cross_layer_answerable_evaluation()
    )

    assert observed == {
        "sufficiency_status": "SUFFICIENT",
        "answerability_status": "ANSWERABLE",
        "used_llm": True,
        "all_requested_payload_visible": True,
    }


def test_agent_evaluation_suite_builds_complete_passing_report():
    report = run_agent_evaluation_suite()

    assert report["evaluation_version"] == "v1"
    assert report["overall_status"] == "PASS"
    assert report["scenario_count"] == 9
    assert report["passed_count"] == 9
    assert report["failed_count"] == 0

    assert [
        scenario["scenario_id"]
        for scenario in report["scenarios"]
    ] == [
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

    assert all(
        scenario["status"] == "PASS"
        for scenario in report["scenarios"]
    )
