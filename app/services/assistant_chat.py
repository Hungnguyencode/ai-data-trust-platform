from __future__ import annotations

from typing import Any, Dict


def build_agent_run_summary_items(
    agent_run_summary: Any,
) -> list[tuple[str, Any]]:
    if not isinstance(
        agent_run_summary,
        dict,
    ):
        return []

    return [
        (
            "Rounds",
            agent_run_summary.get(
                "round_count"
            ),
        ),
        (
            "Stop reason",
            agent_run_summary.get(
                "stop_reason"
            ),
        ),
        (
            "Tool attempts",
            agent_run_summary.get(
                "attempted_tool_count"
            ),
        ),
        (
            "Accepted evidence",
            agent_run_summary.get(
                "accepted_evidence_count"
            ),
        ),
        (
            "Failed tools",
            agent_run_summary.get(
                "failed_tool_count"
            ),
        ),
    ]


def build_agent_evidence_coverage_items(
    agent_evidence_coverage: Any,
) -> list[tuple[str, Any]]:
    if not isinstance(
        agent_evidence_coverage,
        dict,
    ):
        return []

    return [
        (
            "Coverage status",
            agent_evidence_coverage.get(
                "coverage_status"
            ),
        ),
        (
            "Requested evidence",
            agent_evidence_coverage.get(
                "requested_evidence",
                [],
            ),
        ),
        (
            "Attempted evidence",
            agent_evidence_coverage.get(
                "attempted_evidence",
                [],
            ),
        ),
        (
            "Accepted evidence",
            agent_evidence_coverage.get(
                "accepted_evidence",
                [],
            ),
        ),
        (
            "Missing evidence",
            agent_evidence_coverage.get(
                "missing_evidence",
                [],
            ),
        ),
    ]


def build_agent_evidence_sufficiency_items(
    agent_evidence_sufficiency: Any,
) -> list[tuple[str, Any]]:
    if not isinstance(
        agent_evidence_sufficiency,
        dict,
    ):
        return []

    return [
        (
            "Availability status",
            agent_evidence_sufficiency.get(
                "sufficiency_status"
            ),
        ),
        (
            "Requested evidence",
            agent_evidence_sufficiency.get(
                "requested_evidence",
                [],
            ),
        ),
        (
            "Available evidence",
            agent_evidence_sufficiency.get(
                "available_evidence",
                [],
            ),
        ),
        (
            "Empty evidence",
            agent_evidence_sufficiency.get(
                "empty_evidence",
                [],
            ),
        ),
        (
            "Unavailable evidence",
            agent_evidence_sufficiency.get(
                "unavailable_evidence",
                [],
            ),
        ),
        (
            "Evidence details",
            agent_evidence_sufficiency.get(
                "evidence_details",
                [],
            ),
        ),
    ]


def build_copilot_backend_result(
    data: Dict[str, Any],
) -> Dict[str, Any]:
    answer = data.get(
        "answer"
    )

    return {
        "ok": True,
        "answer": (
            str(answer)
            if answer
            else "Backend khĂ´ng tráº£ vá» answer."
        ),
        "source": "FastAPI Copilot",
        "catalog_id": data.get(
            "catalog_id"
        ),
        "latest_version_id": data.get(
            "latest_version_id"
        ),
        "overall_state": data.get(
            "overall_state"
        ),
        "grounded": data.get(
            "grounded",
            True,
        ),
        "provider": data.get(
            "provider"
        ),
        "model": data.get(
            "model"
        ),
        "used_llm": bool(
            data.get(
                "used_llm",
                False,
            )
        ),
        "fallback_reason": data.get(
            "fallback_reason"
        ),
        "error_type": data.get(
            "error_type"
        ),
        "source_finding_codes": list(
            data.get(
                "source_finding_codes",
                [],
            )
            or []
        ),
        "source_action_codes": list(
            data.get(
                "source_action_codes",
                [],
            )
            or []
        ),
        "tool_execution_trace": list(
            data.get(
                "tool_execution_trace",
                [],
            )
            or []
        ),
        "agent_run_summary": data.get(
            "agent_run_summary"
        ),
        "agent_evidence_coverage": data.get(
            "agent_evidence_coverage"
        ),
        "agent_evidence_sufficiency": data.get(
            "agent_evidence_sufficiency"
        ),
    }


def build_copilot_chat_message(
    answer: str,
    backend_result: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "role": "assistant",
        "content": answer,
        "copilot_meta": {
            "ok": backend_result.get(
                "ok",
                False,
            ),
            "source": backend_result.get(
                "source"
            ),
            "catalog_id": backend_result.get(
                "catalog_id"
            ),
            "latest_version_id": (
                backend_result.get(
                    "latest_version_id"
                )
            ),
            "overall_state": backend_result.get(
                "overall_state"
            ),
            "grounded": backend_result.get(
                "grounded"
            ),
            "provider": backend_result.get(
                "provider"
            ),
            "model": backend_result.get(
                "model"
            ),
            "used_llm": backend_result.get(
                "used_llm"
            ),
            "fallback_reason": backend_result.get(
                "fallback_reason"
            ),
            "error_type": backend_result.get(
                "error_type"
            ),
            "source_finding_codes": (
                backend_result.get(
                    "source_finding_codes",
                    [],
                )
            ),
            "source_action_codes": (
                backend_result.get(
                    "source_action_codes",
                    [],
                )
            ),
            "tool_execution_trace": (
                backend_result.get(
                    "tool_execution_trace",
                    [],
                )
                or []
            ),
            "agent_run_summary": (
                backend_result.get(
                    "agent_run_summary"
                )
            ),
            "agent_evidence_coverage": (
                backend_result.get(
                    "agent_evidence_coverage"
                )
            ),
            "agent_evidence_sufficiency": (
                backend_result.get(
                    "agent_evidence_sufficiency"
                )
            ),
        },
    }
