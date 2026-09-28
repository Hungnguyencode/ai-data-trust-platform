import pytest

from src.assistant.claim_response import (
    build_claim_response_plan,
)


def test_build_claim_response_plan_preserves_mixed_claim_identity():
    plan = build_claim_response_plan(
        question=(
            "Compare volume over time "
            "and tell me the latest volume."
        ),
        claim_scoped_controlled_tool_results=[
            {
                "claim_type": (
                    "HISTORICAL_COMPARISON"
                ),
                "answerability_status": (
                    "NOT_ANSWERABLE"
                ),
                "permitted_evidence": [],
                "restricted_evidence": [
                    "volume_history",
                ],
                "controlled_tool_results": [],
            },
            {
                "claim_type": "CURRENT_STATE",
                "answerability_status": (
                    "ANSWERABLE"
                ),
                "permitted_evidence": [
                    "volume_history",
                ],
                "restricted_evidence": [],
                "controlled_tool_results": [
                    {
                        "name": "get_volume_history",
                        "read_only": True,
                        "ok": True,
                        "result": [
                            {
                                "marker": (
                                    "latest-volume-row"
                                ),
                            },
                        ],
                    },
                ],
            },
        ],
    )

    assert plan == [
        {
            "claim_index": 0,
            "claim_text": (
                "Compare volume over time"
            ),
            "claim_type": (
                "HISTORICAL_COMPARISON"
            ),
            "answerability_status": (
                "NOT_ANSWERABLE"
            ),
            "response_mode": (
                "DETERMINISTIC_LIMITATION"
            ),
            "controlled_tool_results": [],
        },
        {
            "claim_index": 1,
            "claim_text": (
                "tell me the latest volume."
            ),
            "claim_type": "CURRENT_STATE",
            "answerability_status": (
                "ANSWERABLE"
            ),
            "response_mode": "LLM",
            "controlled_tool_results": [
                {
                    "name": "get_volume_history",
                    "read_only": True,
                    "ok": True,
                    "result": [
                        {
                            "marker": (
                                "latest-volume-row"
                            ),
                        },
                    ],
                },
            ],
        },
    ]


def test_build_claim_response_plan_rejects_non_mapping_claim_scope():
    with pytest.raises(
        ValueError,
        match="claim scope must be a mapping",
    ):
        build_claim_response_plan(
            question="Tell me the latest volume.",
            claim_scoped_controlled_tool_results=[
                None,
            ],
        )


def test_build_claim_response_plan_rejects_claim_scope_count_mismatch():
    with pytest.raises(
        ValueError,
        match=(
            "claim segment count must match "
            "claim scope count"
        ),
    ):
        build_claim_response_plan(
            question=(
                "Compare volume over time "
                "and tell me the latest volume."
            ),
            claim_scoped_controlled_tool_results=[
                {
                    "claim_type": (
                        "HISTORICAL_COMPARISON"
                    ),
                    "answerability_status": (
                        "NOT_ANSWERABLE"
                    ),
                    "controlled_tool_results": [],
                },
            ],
        )