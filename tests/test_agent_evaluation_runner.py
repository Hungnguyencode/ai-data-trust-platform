from src.assistant import evaluation_runner
from src.assistant.evaluation_runner import (
    run_agent_evaluation_suite,
    run_cross_layer_answerable_evaluation,
    run_cross_layer_not_answerable_evaluation,
    run_cross_layer_partial_answerability_evaluation,
    run_empty_retrieval_availability_evaluation,
    run_mixed_claim_scoped_answerability_evaluation,
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
    assert report["scenario_count"] == 11
    assert report["passed_count"] == 11
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
        "mixed_claim_scoped_answerability",
        "claim_level_response_isolation",
    ]

    assert all(
        scenario["status"] == "PASS"
        for scenario in report["scenarios"]
    )


def test_mixed_claim_scoped_answerability_uses_real_pipeline():
    observed = (
        run_mixed_claim_scoped_answerability_evaluation()
    )

    assert observed == {
        "historical_claim_status": (
            "NOT_ANSWERABLE"
        ),
        "current_claim_status": "ANSWERABLE",
        "historical_payload_count": 0,
        "current_payload_count": 1,
        "used_llm": True,
    }


def test_claim_level_response_isolation_uses_real_copilot_path():
    observed = (
        evaluation_runner
        .run_claim_level_response_isolation_evaluation()
    )

    assert observed == {
        "provider_call_count": 1,
        "supported_claim_visible": True,
        "unsupported_claim_visible": False,
        "supported_payload_visible": True,
        "cross_claim_payload_visible": False,
        "deterministic_limitation_visible": True,
        "supported_answer_visible": True,
        "provenance_claim_count": 2,
        "unsupported_provenance_tool_count": 0,
        "supported_provenance_tool_names": [
            "get_volume_history",
        ],
        "supported_provenance_provider": "gemini",
        "supported_provenance_used_llm": True,
        "unsupported_provenance_evidence_requirements": [
            {
                "evidence_type": (
                    "volume_history"
                ),
                "minimum_item_count": 2,
                "observed_item_count": 1,
                "requirement_status": (
                    "INSUFFICIENT_ITEMS"
                ),
            },
        ],
        "supported_provenance_evidence_requirements": [
            {
                "evidence_type": (
                    "volume_history"
                ),
                "minimum_item_count": 1,
                "observed_item_count": 1,
                "requirement_status": (
                    "SATISFIED"
                ),
            },
        ],
        "raw_evidence_payload_exposed": False,
    }