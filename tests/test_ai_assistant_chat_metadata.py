from __future__ import annotations

from app.services.assistant_chat import (
    build_agent_evidence_coverage_items,
    build_agent_run_summary_items,
    build_copilot_backend_result,
    build_copilot_chat_message,
)


def test_build_copilot_chat_message_preserves_agent_run_summary():
    agent_run_summary = {
        "round_count": 2,
        "stop_reason": "MAX_ROUNDS_REACHED",
        "attempted_tool_count": 4,
        "accepted_evidence_count": 3,
        "failed_tool_count": 1,
    }

    message = build_copilot_chat_message(
        "Grounded answer.",
        {
            "ok": True,
            "source": "FastAPI Copilot",
            "catalog_id": 4,
            "latest_version_id": 6,
            "overall_state": "WARNING",
            "grounded": True,
            "provider": "disabled",
            "model": None,
            "used_llm": False,
            "fallback_reason": "provider_disabled",
            "error_type": None,
            "source_finding_codes": [],
            "source_action_codes": [],
            "tool_execution_trace": [],
            "agent_run_summary": agent_run_summary,
        },
    )

    assert message[
        "copilot_meta"
    ][
        "agent_run_summary"
    ] == agent_run_summary


def test_build_copilot_backend_result_preserves_agent_run_summary():
    agent_run_summary = {
        "round_count": 1,
        "stop_reason": (
            "NO_UNATTEMPTED_REQUESTED_TOOLS"
        ),
        "attempted_tool_count": 1,
        "accepted_evidence_count": 1,
        "failed_tool_count": 0,
    }

    result = build_copilot_backend_result(
        {
            "catalog_id": 4,
            "latest_version_id": 6,
            "overall_state": "WARNING",
            "answer": "Grounded answer.",
            "grounded": True,
            "provider": "disabled",
            "model": None,
            "used_llm": False,
            "fallback_reason": "provider_disabled",
            "error_type": None,
            "source_finding_codes": [],
            "source_action_codes": [],
            "tool_execution_trace": [],
            "agent_run_summary": agent_run_summary,
        }
    )

    assert result[
        "agent_run_summary"
    ] == agent_run_summary

    assert result["ok"] is True

    assert (
        result["source"]
        == "FastAPI Copilot"
    )


def test_build_agent_run_summary_items_exposes_observability_fields():
    items = build_agent_run_summary_items(
        {
            "round_count": 2,
            "stop_reason": "MAX_ROUNDS_REACHED",
            "attempted_tool_count": 4,
            "accepted_evidence_count": 3,
            "failed_tool_count": 1,
        }
    )

    assert items == [
        ("Rounds", 2),
        (
            "Stop reason",
            "MAX_ROUNDS_REACHED",
        ),
        ("Tool attempts", 4),
        ("Accepted evidence", 3),
        ("Failed tools", 1),
    ]


def test_build_agent_run_summary_items_ignores_missing_summary():
    assert build_agent_run_summary_items(
        None
    ) == []


def test_copilot_chat_metadata_preserves_agent_evidence_coverage():
    agent_evidence_coverage = {
        "requested_evidence": [
            "freshness_history",
            "volume_history",
        ],
        "attempted_evidence": [
            "freshness_history",
            "volume_history",
        ],
        "accepted_evidence": [
            "volume_history",
        ],
        "missing_evidence": [
            "freshness_history",
        ],
        "coverage_status": "PARTIAL",
    }

    backend_result = build_copilot_backend_result(
        {
            "catalog_id": 4,
            "latest_version_id": 6,
            "overall_state": "WARNING",
            "answer": "Grounded answer.",
            "grounded": True,
            "provider": "disabled",
            "model": None,
            "used_llm": False,
            "fallback_reason": "provider_disabled",
            "error_type": None,
            "source_finding_codes": [],
            "source_action_codes": [],
            "tool_execution_trace": [],
            "agent_run_summary": None,
            "agent_evidence_coverage": (
                agent_evidence_coverage
            ),
        }
    )

    assert backend_result[
        "agent_evidence_coverage"
    ] == agent_evidence_coverage

    message = build_copilot_chat_message(
        "Grounded answer.",
        backend_result,
    )

    assert message[
        "copilot_meta"
    ][
        "agent_evidence_coverage"
    ] == agent_evidence_coverage


def test_build_agent_evidence_coverage_items_exposes_coverage_fields():
    items = build_agent_evidence_coverage_items(
        {
            "requested_evidence": [
                "freshness_history",
                "volume_history",
            ],
            "attempted_evidence": [
                "freshness_history",
                "volume_history",
            ],
            "accepted_evidence": [
                "volume_history",
            ],
            "missing_evidence": [
                "freshness_history",
            ],
            "coverage_status": "PARTIAL",
        }
    )

    assert items == [
        ("Coverage status", "PARTIAL"),
        (
            "Requested evidence",
            [
                "freshness_history",
                "volume_history",
            ],
        ),
        (
            "Attempted evidence",
            [
                "freshness_history",
                "volume_history",
            ],
        ),
        (
            "Accepted evidence",
            [
                "volume_history",
            ],
        ),
        (
            "Missing evidence",
            [
                "freshness_history",
            ],
        ),
    ]


def test_build_agent_evidence_coverage_items_ignores_missing_coverage():
    assert build_agent_evidence_coverage_items(
        None
    ) == []
