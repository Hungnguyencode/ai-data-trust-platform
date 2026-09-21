import json
from datetime import datetime

import pandas as pd
import pytest

from src.assistant import controlled_tools
from src.assistant.controlled_tools import (
    execute_controlled_tool,
)


def test_get_version_lineage_tool_is_read_only(
    monkeypatch,
):
    expected_lineage = {
        "summary": {
            "catalog_id": 1,
            "version_id": 6,
            "lifecycle_state": "ACTIVE",
        },
        "timeline": [
            {
                "event_type": "INGESTION",
            },
        ],
    }

    def fake_get_version_lineage(
        version_id,
    ):
        assert version_id == 6
        return expected_lineage

    monkeypatch.setattr(
        (
            "src.assistant.controlled_tools."
            "get_version_lineage"
        ),
        fake_get_version_lineage,
    )

    result = execute_controlled_tool(
        "get_version_lineage",
        {
            "version_id": 6,
        },
    )

    assert result == {
        "name": "get_version_lineage",
        "read_only": True,
        "ok": True,
        "result": expected_lineage,
    }



def test_controlled_tool_rejects_unknown_tool():
    with pytest.raises(
        ValueError,
        match="Unsupported controlled tool",
    ):
        execute_controlled_tool(
            "promote_version",
            {
                "version_id": 6,
            },
        )


@pytest.mark.parametrize(
    "version_id",
    [
        0,
        -1,
        True,
        "6",
    ],
)
def test_get_version_lineage_rejects_invalid_version_id(
    version_id,
):
    with pytest.raises(
        ValueError,
        match="version_id must be a positive integer",
    ):
        execute_controlled_tool(
            "get_version_lineage",
            {
                "version_id": version_id,
            },
        )


def test_controlled_tool_rejects_non_mapping_arguments():
    with pytest.raises(
        ValueError,
        match="tool arguments must be a mapping",
    ):
        execute_controlled_tool(
            "get_version_lineage",
            ["version_id", 6],
        )


def test_get_version_lineage_rejects_unexpected_arguments(
    monkeypatch,
):
    monkeypatch.setattr(
        (
            "src.assistant.controlled_tools."
            "get_version_lineage"
        ),
        lambda version_id: {
            "summary": {
                "version_id": version_id,
            },
        },
    )

    with pytest.raises(
        ValueError,
        match="Unsupported tool argument",
    ):
        execute_controlled_tool(
            "get_version_lineage",
            {
                "version_id": 6,
                "catalog_id": 1,
            },
        )


def test_controlled_tool_registry_exposes_read_only_schema():
    definitions = (
        controlled_tools
        .get_controlled_tool_definitions()
    )

    assert definitions == [
        {
            "name": "get_version_lineage",
            "description": (
                "Read persisted end-to-end lineage "
                "for one dataset version."
            ),
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "version_id": {
                        "type": "integer",
                        "minimum": 1,
                    },
                },
                "required": [
                    "version_id",
                ],
                "additionalProperties": False,
            },
        },
        {
            "name": "get_freshness_history",
            "description": (
                "Read persisted freshness history "
                "for one dataset catalog."
            ),
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "catalog_id": {
                        "type": "integer",
                        "minimum": 1,
                    },
                },
                "required": [
                    "catalog_id",
                ],
                "additionalProperties": False,
            },
        },
        {
            "name": "get_volume_history",
            "description": (
                "Read persisted volume history "
                "for one dataset catalog."
            ),
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "catalog_id": {
                        "type": "integer",
                        "minimum": 1,
                    },
                },
                "required": [
                    "catalog_id",
                ],
                "additionalProperties": False,
            },
        },
        {
            "name": "get_pipeline_run_history",
            "description": (
                "Read persisted pipeline run history "
                "for one dataset catalog."
            ),
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "catalog_id": {
                        "type": "integer",
                        "minimum": 1,
                    },
                },
                "required": [
                    "catalog_id",
                ],
                "additionalProperties": False,
            },
        },
    ]


def test_get_version_lineage_returns_bounded_json_safe_result(
    monkeypatch,
):
    lineage = {
        "summary": {
            "catalog_id": 1,
            "version_id": 6,
            "created_at": datetime(
                2026,
                9,
                20,
                11,
                30,
                0,
            ),
            "nullable_metric": float("nan"),
        },
        "version": {
            "version_id": 6,
        },
        "ingestions": [
            {"index": index}
            for index in range(25)
        ],
        "contract_validations": [
            {"index": index}
            for index in range(25)
        ],
        "validations": [
            {"index": index}
            for index in range(25)
        ],
        "governance_decisions": [
            {"index": index}
            for index in range(25)
        ],
        "lifecycle_events": [
            {"index": index}
            for index in range(25)
        ],
        "timeline": [
            {"index": index}
            for index in range(25)
        ],
    }

    monkeypatch.setattr(
        (
            "src.assistant.controlled_tools."
            "get_version_lineage"
        ),
        lambda version_id: lineage,
    )

    result = execute_controlled_tool(
        "get_version_lineage",
        {
            "version_id": 6,
        },
    )

    tool_result = result["result"]

    assert tool_result["summary"]["created_at"] == (
        "2026-09-20T11:30:00"
    )

    assert (
        tool_result["summary"]["nullable_metric"]
        is None
    )

    bounded_fields = (
        "ingestions",
        "contract_validations",
        "validations",
        "governance_decisions",
        "lifecycle_events",
        "timeline",
    )

    for field_name in bounded_fields:
        assert len(
            tool_result[field_name]
        ) == 20

        assert tool_result[
            field_name
        ][0]["index"] == 5

        assert tool_result[
            field_name
        ][-1]["index"] == 24

    json.dumps(
        result,
        ensure_ascii=False,
        allow_nan=False,
    )


def test_controlled_tool_request_protocol_allows_only_read_only_tool():
    parsed = (
        controlled_tools
        .parse_controlled_tool_request(
            (
                '{"name":"get_version_lineage",'
                '"arguments":{"version_id":6}}'
            )
        )
    )

    assert parsed == {
        "name": "get_version_lineage",
        "arguments": {
            "version_id": 6,
        },
    }

    with pytest.raises(
        ValueError,
        match="Unsupported controlled tool",
    ):
        controlled_tools.parse_controlled_tool_request(
            (
                '{"name":"promote_version",'
                '"arguments":{"version_id":6}}'
            )
        )


def test_tool_request_cannot_override_trusted_version():
    bound_request = (
        controlled_tools
        .bind_controlled_tool_request(
            (
                '{"name":"get_version_lineage",'
                '"arguments":{"version_id":6}}'
            ),
            trusted_version_id=6,
        )
    )

    assert bound_request == {
        "name": "get_version_lineage",
        "arguments": {
            "version_id": 6,
        },
    }

    with pytest.raises(
        ValueError,
        match="trusted version",
    ):
        controlled_tools.bind_controlled_tool_request(
            (
                '{"name":"get_version_lineage",'
                '"arguments":{"version_id":999}}'
            ),
            trusted_version_id=6,
        )


def test_controlled_tool_selection_is_backend_owned():
    lineage_request = (
        controlled_tools
        .select_controlled_tool_request(
            "Cho mình xem lineage của dataset này.",
            trusted_version_id=6,
        )
    )

    assert lineage_request == {
        "name": "get_version_lineage",
        "arguments": {
            "version_id": 6,
        },
    }

    unrelated_request = (
        controlled_tools
        .select_controlled_tool_request(
            "Trust Score hiện tại là bao nhiêu?",
            trusted_version_id=6,
        )
    )

    assert unrelated_request is None

    write_request = (
        controlled_tools
        .select_controlled_tool_request(
            "Promote version này lên ACTIVE giúp mình.",
            trusted_version_id=6,
        )
    )

    assert write_request is None

def test_get_freshness_history_tool_returns_json_safe_read_only_evidence(
    monkeypatch,
):
    freshness_frame = pd.DataFrame(
        [
            {
                "freshness_check_id": 12,
                "catalog_id": 4,
                "version_id": 9,
                "age_minutes": float("nan"),
                "freshness_status": "FRESH",
                "checked_at": datetime(
                    2026,
                    9,
                    21,
                    1,
                    30,
                    0,
                ),
            },
            {
                "freshness_check_id": 11,
                "catalog_id": 4,
                "version_id": 8,
                "age_minutes": 42,
                "freshness_status": "STALE",
                "checked_at": datetime(
                    2026,
                    9,
                    20,
                    23,
                    0,
                    0,
                ),
            },
        ]
    )

    captured: dict = {}

    def fake_get_freshness_history(
        catalog_id,
        limit=50,
    ):
        captured["catalog_id"] = catalog_id
        captured["limit"] = limit

        return freshness_frame

    monkeypatch.setattr(
        controlled_tools,
        "get_freshness_history",
        fake_get_freshness_history,
        raising=False,
    )

    result = execute_controlled_tool(
        "get_freshness_history",
        {
            "catalog_id": 4,
        },
    )

    assert captured == {
        "catalog_id": 4,
        "limit": 20,
    }

    assert result["name"] == (
        "get_freshness_history"
    )

    assert result["read_only"] is True
    assert result["ok"] is True

    assert result["result"] == [
        {
            "freshness_check_id": 12,
            "catalog_id": 4,
            "version_id": 9,
            "age_minutes": None,
            "freshness_status": "FRESH",
            "checked_at": (
                "2026-09-21T01:30:00"
            ),
        },
        {
            "freshness_check_id": 11,
            "catalog_id": 4,
            "version_id": 8,
            "age_minutes": 42,
            "freshness_status": "STALE",
            "checked_at": (
                "2026-09-20T23:00:00"
            ),
        },
    ]

    json.dumps(
        result,
        ensure_ascii=False,
        allow_nan=False,
    )

def test_freshness_tool_definition_is_read_only_and_catalog_scoped():
    definitions = (
        controlled_tools
        .get_controlled_tool_definitions()
    )

    freshness_definition = next(
        item
        for item in definitions
        if item["name"]
        == "get_freshness_history"
    )

    assert freshness_definition == {
        "name": "get_freshness_history",
        "description": (
            "Read persisted freshness history "
            "for one dataset catalog."
        ),
        "read_only": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "catalog_id": {
                    "type": "integer",
                    "minimum": 1,
                },
            },
            "required": [
                "catalog_id",
            ],
            "additionalProperties": False,
        },
    }


def test_freshness_tool_request_protocol_accepts_catalog_scope():
    parsed = (
        controlled_tools
        .parse_controlled_tool_request(
            (
                '{"name":"get_freshness_history",'
                '"arguments":{"catalog_id":4}}'
            )
        )
    )

    assert parsed == {
        "name": "get_freshness_history",
        "arguments": {
            "catalog_id": 4,
        },
    }


def test_volume_tool_request_protocol_accepts_catalog_scope():
    parsed = (
        controlled_tools
        .parse_controlled_tool_request(
            (
                '{"name":"get_volume_history",'
                '"arguments":{"catalog_id":4}}'
            )
        )
    )

    assert parsed == {
        "name": "get_volume_history",
        "arguments": {
            "catalog_id": 4,
        },
    }


def test_volume_tool_request_protocol_rejects_user_limit():
    with pytest.raises(
        ValueError,
        match="Unsupported tool argument: limit",
    ):
        controlled_tools.parse_controlled_tool_request(
            (
                '{"name":"get_volume_history",'
                '"arguments":{'
                '"catalog_id":4,'
                '"limit":999'
                "}}"
            )
        )


def test_freshness_request_cannot_override_trusted_catalog():
    bound_request = (
        controlled_tools
        .bind_controlled_tool_request(
            (
                '{"name":"get_freshness_history",'
                '"arguments":{"catalog_id":4}}'
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
        )
    )

    assert bound_request == {
        "name": "get_freshness_history",
        "arguments": {
            "catalog_id": 4,
        },
    }

    with pytest.raises(
        ValueError,
        match="trusted catalog",
    ):
        (
            controlled_tools
            .bind_controlled_tool_request(
                (
                    '{"name":"get_freshness_history",'
                    '"arguments":{"catalog_id":999}}'
                ),
                trusted_version_id=6,
                trusted_catalog_id=4,
            )
        )


def test_volume_request_cannot_override_trusted_catalog():
    bound_request = (
        controlled_tools
        .bind_controlled_tool_request(
            (
                '{"name":"get_volume_history",'
                '"arguments":{"catalog_id":4}}'
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
        )
    )

    assert bound_request == {
        "name": "get_volume_history",
        "arguments": {
            "catalog_id": 4,
        },
    }

    with pytest.raises(
        ValueError,
        match="trusted catalog",
    ):
        controlled_tools.bind_controlled_tool_request(
            (
                '{"name":"get_volume_history",'
                '"arguments":{"catalog_id":999}}'
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
        )


def test_controlled_tool_selection_uses_trusted_catalog_for_freshness():
    freshness_request = (
        controlled_tools
        .select_controlled_tool_request(
            (
                "Show freshness history "
                "for catalog 999."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
        )
    )

    assert freshness_request == {
        "name": "get_freshness_history",
        "arguments": {
            "catalog_id": 4,
        },
    }


def test_controlled_tool_selection_uses_trusted_catalog_for_volume():
    volume_request = (
        controlled_tools
        .select_controlled_tool_request(
            (
                "Show volume history "
                "for catalog 999."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
        )
    )

    assert volume_request == {
        "name": "get_volume_history",
        "arguments": {
            "catalog_id": 4,
        },
    }


def test_get_volume_history_tool_returns_json_safe_read_only_evidence(
    monkeypatch,
):
    volume_frame = pd.DataFrame(
        [
            {
                "volume_check_id": 22,
                "volume_policy_id": 3,
                "catalog_id": 4,
                "ingestion_event_id": 15,
                "version_id": 9,
                "baseline_ingestion_event_id": 14,
                "baseline_version_id": 8,
                "baseline_row_count": 1000,
                "current_row_count": 700,
                "drop_threshold_pct": 20.0,
                "spike_threshold_pct": 30.0,
                "row_change_pct": -30.0,
                "volume_status": "DROP",
                "checked_at": datetime(
                    2026,
                    9,
                    21,
                    2,
                    30,
                    0,
                ),
            },
            {
                "volume_check_id": 21,
                "volume_policy_id": 3,
                "catalog_id": 4,
                "ingestion_event_id": 14,
                "version_id": 8,
                "baseline_ingestion_event_id": None,
                "baseline_version_id": None,
                "baseline_row_count": None,
                "current_row_count": 1000,
                "drop_threshold_pct": 20.0,
                "spike_threshold_pct": 30.0,
                "row_change_pct": float("nan"),
                "volume_status": "BASELINE",
                "checked_at": datetime(
                    2026,
                    9,
                    20,
                    23,
                    30,
                    0,
                ),
            },
        ]
    )

    captured: dict = {}

    def fake_get_volume_history(
        catalog_id,
        limit=50,
    ):
        captured["catalog_id"] = catalog_id
        captured["limit"] = limit

        return volume_frame

    monkeypatch.setattr(
        controlled_tools,
        "get_volume_history",
        fake_get_volume_history,
        raising=False,
    )

    result = execute_controlled_tool(
        "get_volume_history",
        {
            "catalog_id": 4,
        },
    )

    assert captured == {
        "catalog_id": 4,
        "limit": 20,
    }

    assert result["name"] == (
        "get_volume_history"
    )

    assert result["read_only"] is True
    assert result["ok"] is True

    assert result["result"] == [
        {
            "volume_check_id": 22,
            "volume_policy_id": 3,
            "catalog_id": 4,
            "ingestion_event_id": 15,
            "version_id": 9,
            "baseline_ingestion_event_id": 14,
            "baseline_version_id": 8,
            "baseline_row_count": 1000,
            "current_row_count": 700,
            "drop_threshold_pct": 20.0,
            "spike_threshold_pct": 30.0,
            "row_change_pct": -30.0,
            "volume_status": "DROP",
            "checked_at": (
                "2026-09-21T02:30:00"
            ),
        },
        {
            "volume_check_id": 21,
            "volume_policy_id": 3,
            "catalog_id": 4,
            "ingestion_event_id": 14,
            "version_id": 8,
            "baseline_ingestion_event_id": None,
            "baseline_version_id": None,
            "baseline_row_count": None,
            "current_row_count": 1000,
            "drop_threshold_pct": 20.0,
            "spike_threshold_pct": 30.0,
            "row_change_pct": None,
            "volume_status": "BASELINE",
            "checked_at": (
                "2026-09-20T23:30:00"
            ),
        },
    ]

    json.dumps(
        result,
        ensure_ascii=False,
        allow_nan=False,
    )


def test_volume_tool_definition_is_read_only_and_catalog_scoped():
    definitions = (
        controlled_tools
        .get_controlled_tool_definitions()
    )

    volume_definition = next(
        (
            item
            for item in definitions
            if item["name"]
            == "get_volume_history"
        ),
        None,
    )

    assert volume_definition == {
        "name": "get_volume_history",
        "description": (
            "Read persisted volume history "
            "for one dataset catalog."
        ),
        "read_only": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "catalog_id": {
                    "type": "integer",
                    "minimum": 1,
                },
            },
            "required": [
                "catalog_id",
            ],
            "additionalProperties": False,
        },
    }


def test_pipeline_run_history_tool_definition_is_read_only_and_catalog_scoped():
    definitions = (
        controlled_tools
        .get_controlled_tool_definitions()
    )

    pipeline_definition = next(
        (
            item
            for item in definitions
            if item["name"]
            == "get_pipeline_run_history"
        ),
        None,
    )

    assert pipeline_definition == {
        "name": "get_pipeline_run_history",
        "description": (
            "Read persisted pipeline run history "
            "for one dataset catalog."
        ),
        "read_only": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "catalog_id": {
                    "type": "integer",
                    "minimum": 1,
                },
            },
            "required": [
                "catalog_id",
            ],
            "additionalProperties": False,
        },
    }


def test_pipeline_run_history_tool_request_protocol_accepts_catalog_scope():
    parsed = (
        controlled_tools
        .parse_controlled_tool_request(
            (
                '{"name":"get_pipeline_run_history",'
                '"arguments":{"catalog_id":4}}'
            )
        )
    )

    assert parsed == {
        "name": "get_pipeline_run_history",
        "arguments": {
            "catalog_id": 4,
        },
    }


def test_pipeline_run_history_tool_request_protocol_rejects_user_limit():
    with pytest.raises(
        ValueError,
        match="Unsupported tool argument: limit",
    ):
        controlled_tools.parse_controlled_tool_request(
            (
                '{"name":"get_pipeline_run_history",'
                '"arguments":{'
                '"catalog_id":4,'
                '"limit":999'
                "}}"
            )
        )


def test_controlled_tool_selection_uses_trusted_catalog_for_pipeline_history():
    pipeline_request = (
        controlled_tools
        .select_controlled_tool_request(
            (
                "Show pipeline run history "
                "for catalog 999."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
        )
    )

    assert pipeline_request == {
        "name": "get_pipeline_run_history",
        "arguments": {
            "catalog_id": 4,
        },
    }


def test_get_pipeline_run_history_tool_returns_json_safe_read_only_evidence(
    monkeypatch,
):
    pipeline_frame = pd.DataFrame(
        [
            {
                "pipeline_run_id": 31,
                "catalog_id": 4,
                "version_id": 9,
                "run_status": "FAILED",
                "attempt_count": 2,
                "trust_score": float("nan"),
                "started_at": datetime(
                    2026,
                    9,
                    21,
                    3,
                    0,
                    0,
                ),
                "finished_at": datetime(
                    2026,
                    9,
                    21,
                    3,
                    1,
                    30,
                ),
                "error_type": "RuntimeError",
                "error_message": "Validation failed.",
            },
            {
                "pipeline_run_id": 30,
                "catalog_id": 4,
                "version_id": 8,
                "run_status": "SUCCESS",
                "attempt_count": 1,
                "trust_score": 97.0,
                "started_at": datetime(
                    2026,
                    9,
                    20,
                    3,
                    0,
                    0,
                ),
                "finished_at": datetime(
                    2026,
                    9,
                    20,
                    3,
                    1,
                    0,
                ),
                "error_type": None,
                "error_message": None,
            },
        ]
    )

    captured = {}

    def fake_get_pipeline_run_history_by_catalog(
        catalog_id,
        *,
        limit,
    ):
        captured["catalog_id"] = catalog_id
        captured["limit"] = limit

        return pipeline_frame

    monkeypatch.setattr(
        controlled_tools,
        "get_pipeline_run_history_by_catalog",
        fake_get_pipeline_run_history_by_catalog,
        raising=False,
    )

    result = execute_controlled_tool(
        "get_pipeline_run_history",
        {
            "catalog_id": 4,
        },
    )

    assert captured == {
        "catalog_id": 4,
        "limit": 20,
    }

    assert result["name"] == (
        "get_pipeline_run_history"
    )

    assert result["read_only"] is True
    assert result["ok"] is True

    assert result["result"] == [
        {
            "pipeline_run_id": 31,
            "catalog_id": 4,
            "version_id": 9,
            "run_status": "FAILED",
            "attempt_count": 2,
            "trust_score": None,
            "started_at": (
                "2026-09-21T03:00:00"
            ),
            "finished_at": (
                "2026-09-21T03:01:30"
            ),
            "error_type": "RuntimeError",
            "error_message": "Validation failed.",
        },
        {
            "pipeline_run_id": 30,
            "catalog_id": 4,
            "version_id": 8,
            "run_status": "SUCCESS",
            "attempt_count": 1,
            "trust_score": 97.0,
            "started_at": (
                "2026-09-20T03:00:00"
            ),
            "finished_at": (
                "2026-09-20T03:01:00"
            ),
            "error_type": None,
            "error_message": None,
        },
    ]
