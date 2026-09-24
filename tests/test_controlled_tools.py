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
        {
            "name": "get_operational_event_history",
            "description": (
                "Read persisted operational event history "
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


def test_operational_event_history_tool_definition_is_read_only_and_catalog_scoped():
    definitions = (
        controlled_tools
        .get_controlled_tool_definitions()
    )

    event_definition = next(
        (
            item
            for item in definitions
            if item["name"]
            == "get_operational_event_history"
        ),
        None,
    )

    assert event_definition == {
        "name": "get_operational_event_history",
        "description": (
            "Read persisted operational event history "
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


def test_operational_event_history_tool_request_protocol_accepts_catalog_scope():
    parsed = (
        controlled_tools
        .parse_controlled_tool_request(
            (
                '{"name":"get_operational_event_history",'
                '"arguments":{"catalog_id":4}}'
            )
        )
    )

    assert parsed == {
        "name": "get_operational_event_history",
        "arguments": {
            "catalog_id": 4,
        },
    }


def test_operational_event_history_tool_request_protocol_rejects_user_limit():
    with pytest.raises(
        ValueError,
        match="Unsupported tool argument: limit",
    ):
        controlled_tools.parse_controlled_tool_request(
            (
                '{"name":"get_operational_event_history",'
                '"arguments":{'
                '"catalog_id":4,'
                '"limit":999'
                "}}"
            )
        )


def test_controlled_tool_selection_uses_trusted_catalog_for_operational_events():
    event_request = (
        controlled_tools
        .select_controlled_tool_request(
            (
                "Show operational event history "
                "for catalog 999."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
        )
    )

    assert event_request == {
        "name": "get_operational_event_history",
        "arguments": {
            "catalog_id": 4,
        },
    }


def test_get_operational_event_history_tool_returns_json_safe_read_only_evidence(
    monkeypatch,
):
    event_frame = pd.DataFrame(
        [
            {
                "operational_event_id": 51,
                "event_key": "freshness:4:stale",
                "event_type": "DATASET_STALE",
                "severity": "WARNING",
                "event_source": "FRESHNESS_MONITOR",
                "event_stage": "OBSERVABILITY",
                "catalog_id": 4,
                "version_id": 9,
                "pipeline_run_id": float("nan"),
                "reference_id": 12,
                "message": "Dataset is stale.",
                "detail_json": (
                    '{"age_minutes": 180}'
                ),
                "occurred_at": datetime(
                    2026,
                    9,
                    21,
                    4,
                    0,
                    0,
                ),
                "created_at": datetime(
                    2026,
                    9,
                    21,
                    4,
                    0,
                    5,
                ),
            }
        ]
    )

    captured = {}

    def fake_get_operational_event_history_by_catalog(
        catalog_id,
        *,
        limit,
    ):
        captured["catalog_id"] = catalog_id
        captured["limit"] = limit

        return event_frame

    monkeypatch.setattr(
        controlled_tools,
        "get_operational_event_history_by_catalog",
        fake_get_operational_event_history_by_catalog,
        raising=False,
    )

    result = execute_controlled_tool(
        "get_operational_event_history",
        {
            "catalog_id": 4,
        },
    )

    assert captured == {
        "catalog_id": 4,
        "limit": 20,
    }

    assert result["name"] == (
        "get_operational_event_history"
    )

    assert result["read_only"] is True
    assert result["ok"] is True

    assert result["result"] == [
        {
            "operational_event_id": 51,
            "event_key": "freshness:4:stale",
            "event_type": "DATASET_STALE",
            "severity": "WARNING",
            "event_source": "FRESHNESS_MONITOR",
            "event_stage": "OBSERVABILITY",
            "catalog_id": 4,
            "version_id": 9,
            "pipeline_run_id": None,
            "reference_id": 12,
            "message": "Dataset is stale.",
            "detail_json": (
                '{"age_minutes": 180}'
            ),
            "occurred_at": (
                "2026-09-21T04:00:00"
            ),
            "created_at": (
                "2026-09-21T04:00:05"
            ),
        }
    ]


def test_controlled_tool_planner_builds_multi_tool_read_only_evidence_plan():
    plan = (
        controlled_tools
        .plan_controlled_tool_requests(
            (
                "Compare freshness, volume, "
                "and pipeline history "
                "for catalog 999."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
        )
    )

    assert plan == [
        {
            "name": "get_freshness_history",
            "arguments": {
                "catalog_id": 4,
            },
        },
        {
            "name": "get_volume_history",
            "arguments": {
                "catalog_id": 4,
            },
        },
        {
            "name": "get_pipeline_run_history",
            "arguments": {
                "catalog_id": 4,
            },
        },
    ]


def test_controlled_tool_planner_caps_plan_at_three_tools():
    plan = (
        controlled_tools
        .plan_controlled_tool_requests(
            (
                "Show lineage, freshness, volume, "
                "pipeline history, and operational events."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
        )
    )

    assert len(plan) == 3

    assert plan == [
        {
            "name": "get_version_lineage",
            "arguments": {
                "version_id": 6,
            },
        },
        {
            "name": "get_freshness_history",
            "arguments": {
                "catalog_id": 4,
            },
        },
        {
            "name": "get_volume_history",
            "arguments": {
                "catalog_id": 4,
            },
        },
    ]


def test_controlled_evidence_requirements_keep_all_requested_domains():
    evidence = (
        controlled_tools
        .plan_controlled_evidence_requirements(
            (
                "Show lineage, freshness, volume, "
                "pipeline history, and operational events."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
        )
    )

    assert evidence == [
        "version_lineage",
        "freshness_history",
        "volume_history",
        "pipeline_run_history",
        "operational_event_history",
    ]


def test_controlled_evidence_coverage_marks_failed_requested_evidence_missing():
    coverage = (
        controlled_tools
        .build_controlled_evidence_coverage(
            requested_evidence=[
                "freshness_history",
                "volume_history",
            ],
            attempted_tool_names=[
                "get_freshness_history",
                "get_volume_history",
            ],
            accepted_tool_names=[
                "get_volume_history",
            ],
        )
    )

    assert coverage == {
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


def test_controlled_evidence_coverage_preserves_actual_attempt_and_accept_order():
    coverage = (
        controlled_tools
        .build_controlled_evidence_coverage(
            requested_evidence=[
                "freshness_history",
                "volume_history",
                "pipeline_run_history",
            ],
            attempted_tool_names=[
                "get_pipeline_run_history",
                "get_freshness_history",
                "get_volume_history",
            ],
            accepted_tool_names=[
                "get_pipeline_run_history",
                "get_volume_history",
            ],
        )
    )

    assert coverage == {
        "requested_evidence": [
            "freshness_history",
            "volume_history",
            "pipeline_run_history",
        ],
        "attempted_evidence": [
            "pipeline_run_history",
            "freshness_history",
            "volume_history",
        ],
        "accepted_evidence": [
            "pipeline_run_history",
            "volume_history",
        ],
        "missing_evidence": [
            "freshness_history",
        ],
        "coverage_status": "PARTIAL",
    }


@pytest.mark.parametrize(
    (
        "requested_evidence",
        "attempted_tool_names",
        "accepted_tool_names",
        "expected_status",
        "expected_missing",
    ),
    [
        (
            [
                "freshness_history",
                "volume_history",
            ],
            [
                "get_freshness_history",
                "get_volume_history",
            ],
            [
                "get_freshness_history",
                "get_volume_history",
            ],
            "COMPLETE",
            [],
        ),
        (
            [
                "freshness_history",
                "volume_history",
            ],
            [
                "get_freshness_history",
                "get_volume_history",
            ],
            [],
            "NONE",
            [
                "freshness_history",
                "volume_history",
            ],
        ),
        (
            [],
            [],
            [],
            "NOT_APPLICABLE",
            [],
        ),
    ],
)
def test_controlled_evidence_coverage_reports_deterministic_status(
    requested_evidence,
    attempted_tool_names,
    accepted_tool_names,
    expected_status,
    expected_missing,
):
    coverage = (
        controlled_tools
        .build_controlled_evidence_coverage(
            requested_evidence=(
                requested_evidence
            ),
            attempted_tool_names=(
                attempted_tool_names
            ),
            accepted_tool_names=(
                accepted_tool_names
            ),
        )
    )

    assert (
        coverage["coverage_status"]
        == expected_status
    )

    assert (
        coverage["missing_evidence"]
        == expected_missing
    )


def test_controlled_tool_follow_up_planner_returns_unattempted_requested_tools():
    question = (
        "Show lineage, freshness, volume, "
        "pipeline history, and operational events."
    )

    first_round = (
        controlled_tools
        .plan_controlled_tool_requests(
            question,
            trusted_version_id=6,
            trusted_catalog_id=4,
        )
    )

    attempted_tool_names = {
        request["name"]
        for request in first_round
    }

    follow_up = (
        controlled_tools
        .plan_follow_up_controlled_tool_requests(
            question,
            trusted_version_id=6,
            trusted_catalog_id=4,
            attempted_tool_names=(
                attempted_tool_names
            ),
        )
    )

    assert follow_up == [
        {
            "name": "get_pipeline_run_history",
            "arguments": {
                "catalog_id": 4,
            },
        },
        {
            "name": "get_operational_event_history",
            "arguments": {
                "catalog_id": 4,
            },
        },
    ]


def test_controlled_tool_follow_up_planner_does_not_retry_attempted_failed_tool():
    question = (
        "Show freshness, volume, "
        "pipeline history, and operational events."
    )

    attempted_tool_names = {
        "get_freshness_history",
        "get_volume_history",
    }

    follow_up = (
        controlled_tools
        .plan_follow_up_controlled_tool_requests(
            question,
            trusted_version_id=6,
            trusted_catalog_id=4,
            attempted_tool_names=(
                attempted_tool_names
            ),
        )
    )

    assert follow_up == [
        {
            "name": "get_pipeline_run_history",
            "arguments": {
                "catalog_id": 4,
            },
        },
        {
            "name": "get_operational_event_history",
            "arguments": {
                "catalog_id": 4,
            },
        },
    ]


def test_controlled_tool_planner_rejects_mutating_request():
    plan = (
        controlled_tools
        .plan_controlled_tool_requests(
            (
                "Promote this dataset and show "
                "freshness, pipeline, and alerts."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
        )
    )

    assert plan == []


def test_controlled_tool_plan_executor_hard_caps_execution(
    monkeypatch,
):
    executed: list[str] = []

    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        executed.append(
            name
        )

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [],
        }

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    results = (
        controlled_tools
        .execute_controlled_tool_plan(
            [
                {
                    "name": "get_version_lineage",
                    "arguments": {
                        "version_id": 6,
                    },
                },
                {
                    "name": "get_freshness_history",
                    "arguments": {
                        "catalog_id": 4,
                    },
                },
                {
                    "name": "get_volume_history",
                    "arguments": {
                        "catalog_id": 4,
                    },
                },
                {
                    "name": "get_pipeline_run_history",
                    "arguments": {
                        "catalog_id": 4,
                    },
                },
            ]
        )
    )

    assert executed == [
        "get_version_lineage",
        "get_freshness_history",
        "get_volume_history",
    ]

    assert len(results) == 3


def test_controlled_tool_plan_executor_isolates_tool_failure(
    monkeypatch,
):
    executed: list[str] = []

    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        executed.append(
            name
        )

        if name == "get_volume_history":
            raise RuntimeError(
                "simulated volume read failure"
            )

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [],
        }

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    results = (
        controlled_tools
        .execute_controlled_tool_plan(
            [
                {
                    "name": "get_freshness_history",
                    "arguments": {
                        "catalog_id": 4,
                    },
                },
                {
                    "name": "get_volume_history",
                    "arguments": {
                        "catalog_id": 4,
                    },
                },
                {
                    "name": "get_pipeline_run_history",
                    "arguments": {
                        "catalog_id": 4,
                    },
                },
            ]
        )
    )

    assert executed == [
        "get_freshness_history",
        "get_volume_history",
        "get_pipeline_run_history",
    ]

    assert [
        result["name"]
        for result in results
    ] == [
        "get_freshness_history",
        "get_pipeline_run_history",
    ]


def test_controlled_tool_plan_executor_records_success_trace(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [
                {
                    "catalog_id": (
                        arguments["catalog_id"]
                    ),
                },
            ],
        }

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    execution_trace: list[dict] = []

    results = (
        controlled_tools
        .execute_controlled_tool_plan(
            [
                {
                    "name": "get_freshness_history",
                    "arguments": {
                        "catalog_id": 4,
                    },
                },
            ],
            execution_trace=execution_trace,
        )
    )

    assert len(results) == 1

    assert len(execution_trace) == 1

    trace_step = execution_trace[0]

    assert trace_step["step"] == 1

    assert (
        trace_step["tool_name"]
        == "get_freshness_history"
    )

    assert trace_step["arguments"] == {
        "catalog_id": 4,
    }

    assert trace_step["status"] == "SUCCEEDED"

    assert (
        trace_step["evidence_accepted"]
        is True
    )

    assert trace_step["error_type"] is None

    assert trace_step["duration_ms"] >= 0


def test_controlled_tool_plan_executor_records_failure_trace_and_continues(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        if name == "get_volume_history":
            raise RuntimeError(
                "simulated volume read failure"
            )

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [],
        }

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    execution_trace: list[dict] = []

    results = (
        controlled_tools
        .execute_controlled_tool_plan(
            [
                {
                    "name": "get_freshness_history",
                    "arguments": {
                        "catalog_id": 4,
                    },
                },
                {
                    "name": "get_volume_history",
                    "arguments": {
                        "catalog_id": 4,
                    },
                },
                {
                    "name": "get_pipeline_run_history",
                    "arguments": {
                        "catalog_id": 4,
                    },
                },
            ],
            execution_trace=execution_trace,
        )
    )

    assert [
        result["name"]
        for result in results
    ] == [
        "get_freshness_history",
        "get_pipeline_run_history",
    ]

    assert [
        item["status"]
        for item in execution_trace
    ] == [
        "SUCCEEDED",
        "FAILED",
        "SUCCEEDED",
    ]

    assert (
        execution_trace[1][
            "tool_name"
        ]
        == "get_volume_history"
    )

    assert (
        execution_trace[1][
            "evidence_accepted"
        ]
        is False
    )

    assert (
        execution_trace[1][
            "error_type"
        ]
        == "RuntimeError"
    )


def test_controlled_tool_plan_executor_trace_respects_hard_cap(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [],
        }

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    execution_trace: list[dict] = []

    controlled_tools.execute_controlled_tool_plan(
        [
            {
                "name": "get_version_lineage",
                "arguments": {
                    "version_id": 6,
                },
            },
            {
                "name": "get_freshness_history",
                "arguments": {
                    "catalog_id": 4,
                },
            },
            {
                "name": "get_volume_history",
                "arguments": {
                    "catalog_id": 4,
                },
            },
            {
                "name": "get_pipeline_run_history",
                "arguments": {
                    "catalog_id": 4,
                },
            },
        ],
        execution_trace=execution_trace,
    )

    assert len(execution_trace) == 3

    assert [
        item["step"]
        for item in execution_trace
    ] == [
        1,
        2,
        3,
    ]

    assert [
        item["tool_name"]
        for item in execution_trace
    ] == [
        "get_version_lineage",
        "get_freshness_history",
        "get_volume_history",
    ]


def test_bounded_controlled_tool_rounds_stop_after_two_rounds(
    monkeypatch,
):
    planned_rounds: list[str] = []
    executed_tools: list[str] = []
    agent_run_summary: dict = {}

    def fake_first_round_planner(
        question,
        *,
        trusted_version_id,
        trusted_catalog_id=None,
    ):
        del (
            question,
            trusted_version_id,
            trusted_catalog_id,
        )

        planned_rounds.append(
            "first"
        )

        return [
            {
                "name": "get_freshness_history",
                "arguments": {
                    "catalog_id": 4,
                },
            },
        ]

    def fake_follow_up_planner(
        question,
        *,
        trusted_version_id,
        trusted_catalog_id=None,
        attempted_tool_names,
    ):
        del (
            question,
            trusted_version_id,
            trusted_catalog_id,
            attempted_tool_names,
        )

        planned_rounds.append(
            "follow_up"
        )

        return [
            {
                "name": "get_volume_history",
                "arguments": {
                    "catalog_id": 4,
                },
            },
        ]

    def fake_execute_plan(
        tool_requests,
        *,
        execution_trace=None,
    ):
        del execution_trace

        results = []

        for request in tool_requests:
            executed_tools.append(
                request["name"]
            )

            results.append(
                {
                    "name": request["name"],
                    "read_only": True,
                    "ok": True,
                    "result": [],
                }
            )

        return results

    monkeypatch.setattr(
        controlled_tools,
        "plan_controlled_tool_requests",
        fake_first_round_planner,
    )

    monkeypatch.setattr(
        controlled_tools,
        "plan_follow_up_controlled_tool_requests",
        fake_follow_up_planner,
    )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool_plan",
        fake_execute_plan,
    )

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            "Show evidence.",
            trusted_version_id=6,
            trusted_catalog_id=4,
            agent_run_summary=(
                agent_run_summary
            ),
        )
    )

    assert planned_rounds == [
        "first",
        "follow_up",
    ]

    assert executed_tools == [
        "get_freshness_history",
        "get_volume_history",
    ]

    assert [
        result["name"]
        for result in results
    ] == [
        "get_freshness_history",
        "get_volume_history",
    ]

    assert agent_run_summary == {
        "round_count": 2,
        "stop_reason": "MAX_ROUNDS_REACHED",
        "attempted_tool_count": 2,
        "accepted_evidence_count": 2,
        "failed_tool_count": 0,
    }


def test_bounded_controlled_tool_rounds_reports_one_round_summary(
    monkeypatch,
):
    def fake_first_round_planner(
        question,
        *,
        trusted_version_id,
        trusted_catalog_id=None,
    ):
        del (
            question,
            trusted_version_id,
            trusted_catalog_id,
        )

        return [
            {
                "name": "get_freshness_history",
                "arguments": {
                    "catalog_id": 4,
                },
            },
        ]

    def fake_follow_up_planner(
        question,
        *,
        trusted_version_id,
        trusted_catalog_id=None,
        attempted_tool_names,
    ):
        del (
            question,
            trusted_version_id,
            trusted_catalog_id,
        )

        assert attempted_tool_names == {
            "get_freshness_history",
        }

        return []

    def fake_execute_plan(
        tool_requests,
        *,
        execution_trace=None,
    ):
        del execution_trace

        return [
            {
                "name": request["name"],
                "read_only": True,
                "ok": True,
                "result": [],
            }
            for request in tool_requests
        ]

    monkeypatch.setattr(
        controlled_tools,
        "plan_controlled_tool_requests",
        fake_first_round_planner,
    )

    monkeypatch.setattr(
        controlled_tools,
        "plan_follow_up_controlled_tool_requests",
        fake_follow_up_planner,
    )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool_plan",
        fake_execute_plan,
    )

    agent_run_summary: dict = {}

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            "Show freshness evidence.",
            trusted_version_id=6,
            trusted_catalog_id=4,
            agent_run_summary=(
                agent_run_summary
            ),
        )
    )

    assert [
        result["name"]
        for result in results
    ] == [
        "get_freshness_history",
    ]

    assert agent_run_summary == {
        "round_count": 1,
        "stop_reason": (
            "NO_UNATTEMPTED_REQUESTED_TOOLS"
        ),
        "attempted_tool_count": 1,
        "accepted_evidence_count": 1,
        "failed_tool_count": 0,
    }


def test_bounded_controlled_tool_rounds_reports_zero_tool_summary(
    monkeypatch,
):
    def fake_first_round_planner(
        question,
        *,
        trusted_version_id,
        trusted_catalog_id=None,
    ):
        del (
            question,
            trusted_version_id,
            trusted_catalog_id,
        )

        return []

    def fail_execute_plan(
        tool_requests,
        *,
        execution_trace=None,
    ):
        del tool_requests
        del execution_trace

        raise AssertionError(
            "zero-tool run must not execute tools"
        )

    monkeypatch.setattr(
        controlled_tools,
        "plan_controlled_tool_requests",
        fake_first_round_planner,
    )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool_plan",
        fail_execute_plan,
    )

    agent_run_summary: dict = {}

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            "Explain the current state.",
            trusted_version_id=6,
            trusted_catalog_id=4,
            agent_run_summary=(
                agent_run_summary
            ),
        )
    )

    assert results == []

    assert agent_run_summary == {
        "round_count": 0,
        "stop_reason": "NO_TOOL_REQUESTS",
        "attempted_tool_count": 0,
        "accepted_evidence_count": 0,
        "failed_tool_count": 0,
    }


def test_bounded_controlled_tool_rounds_keep_trace_steps_continuous(
    monkeypatch,
):
    def fake_first_round_planner(
        question,
        *,
        trusted_version_id,
        trusted_catalog_id=None,
    ):
        del (
            question,
            trusted_version_id,
            trusted_catalog_id,
        )

        return [
            {
                "name": "get_freshness_history",
                "arguments": {
                    "catalog_id": 4,
                },
            },
        ]

    def fake_follow_up_planner(
        question,
        *,
        trusted_version_id,
        trusted_catalog_id=None,
        attempted_tool_names,
    ):
        del (
            question,
            trusted_version_id,
            trusted_catalog_id,
            attempted_tool_names,
        )

        return [
            {
                "name": "get_volume_history",
                "arguments": {
                    "catalog_id": 4,
                },
            },
        ]

    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [],
        }

    monkeypatch.setattr(
        controlled_tools,
        "plan_controlled_tool_requests",
        fake_first_round_planner,
    )

    monkeypatch.setattr(
        controlled_tools,
        "plan_follow_up_controlled_tool_requests",
        fake_follow_up_planner,
    )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    execution_trace: list[dict] = []

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            "Show evidence.",
            trusted_version_id=6,
            trusted_catalog_id=4,
            execution_trace=execution_trace,
        )
    )

    assert [
        result["name"]
        for result in results
    ] == [
        "get_freshness_history",
        "get_volume_history",
    ]

    assert [
        item["step"]
        for item in execution_trace
    ] == [
        1,
        2,
    ]

    assert [
        item["tool_name"]
        for item in execution_trace
    ] == [
        "get_freshness_history",
        "get_volume_history",
    ]


def test_bounded_controlled_tool_rounds_do_not_retry_failed_attempt(
    monkeypatch,
):
    executed_tools: list[str] = []

    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        executed_tools.append(
            name
        )

        if name == "get_freshness_history":
            raise RuntimeError(
                "simulated freshness read failure"
            )

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [],
        }

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    execution_trace: list[dict] = []
    agent_run_summary: dict = {}

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            (
                "Show freshness, volume, "
                "pipeline history, "
                "and operational events."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
            execution_trace=execution_trace,
            agent_run_summary=(
                agent_run_summary
            ),
        )
    )

    assert executed_tools == [
        "get_freshness_history",
        "get_volume_history",
        "get_pipeline_run_history",
        "get_operational_event_history",
    ]

    assert (
        executed_tools.count(
            "get_freshness_history"
        )
        == 1
    )

    assert [
        result["name"]
        for result in results
    ] == [
        "get_volume_history",
        "get_pipeline_run_history",
        "get_operational_event_history",
    ]

    assert [
        item["step"]
        for item in execution_trace
    ] == [
        1,
        2,
        3,
        4,
    ]

    assert [
        item["status"]
        for item in execution_trace
    ] == [
        "FAILED",
        "SUCCEEDED",
        "SUCCEEDED",
        "SUCCEEDED",
    ]

    assert agent_run_summary == {
        "round_count": 2,
        "stop_reason": "MAX_ROUNDS_REACHED",
        "attempted_tool_count": 4,
        "accepted_evidence_count": 3,
        "failed_tool_count": 1,
    }


def test_bounded_controlled_tool_rounds_reports_partial_evidence_coverage(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        if name == "get_freshness_history":
            raise RuntimeError(
                "simulated freshness read failure"
            )

        return {
            "name": name,
            "read_only": True,
            "ok": True,
            "result": [],
        }

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    agent_evidence_coverage: dict = {}

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            (
                "Show freshness and "
                "volume history."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
            agent_evidence_coverage=(
                agent_evidence_coverage
            ),
        )
    )

    assert [
        result["name"]
        for result in results
    ] == [
        "get_volume_history",
    ]

    assert agent_evidence_coverage == {
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


def test_bounded_controlled_tool_rounds_reports_partial_evidence_sufficiency(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        if name == "get_freshness_history":
            return {
                "name": name,
                "read_only": True,
                "ok": True,
                "result": [
                    {
                        "freshness_status": "FRESH",
                    },
                ],
            }

        if name == "get_volume_history":
            return {
                "name": name,
                "read_only": True,
                "ok": True,
                "result": [],
            }

        raise AssertionError(
            f"Unexpected tool: {name}"
        )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    agent_evidence_sufficiency: dict = {}

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            (
                "Show freshness and "
                "volume history."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
            agent_evidence_sufficiency=(
                agent_evidence_sufficiency
            ),
        )
    )

    assert [
        result["name"]
        for result in results
    ] == [
        "get_freshness_history",
        "get_volume_history",
    ]

    assert agent_evidence_sufficiency == {
        "requested_evidence": [
            "freshness_history",
            "volume_history",
        ],
        "available_evidence": [
            "freshness_history",
        ],
        "empty_evidence": [
            "volume_history",
        ],
        "unavailable_evidence": [],
        "evidence_details": [
            {
                "evidence_type": (
                    "freshness_history"
                ),
                "availability_status": (
                    "AVAILABLE"
                ),
                "item_count": 1,
            },
            {
                "evidence_type": (
                    "volume_history"
                ),
                "availability_status": (
                    "EMPTY"
                ),
                "item_count": 0,
            },
        ],
        "sufficiency_status": "PARTIAL",
    }


def test_bounded_controlled_tool_rounds_marks_failed_evidence_unavailable(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        if name == "get_freshness_history":
            raise RuntimeError(
                "simulated freshness read failure"
            )

        if name == "get_volume_history":
            return {
                "name": name,
                "read_only": True,
                "ok": True,
                "result": [
                    {
                        "volume_status": "NORMAL",
                    },
                ],
            }

        raise AssertionError(
            f"Unexpected tool: {name}"
        )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    agent_evidence_sufficiency: dict = {}

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            (
                "Show freshness and "
                "volume history."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
            agent_evidence_sufficiency=(
                agent_evidence_sufficiency
            ),
        )
    )

    assert [
        result["name"]
        for result in results
    ] == [
        "get_volume_history",
    ]

    assert agent_evidence_sufficiency == {
        "requested_evidence": [
            "freshness_history",
            "volume_history",
        ],
        "available_evidence": [
            "volume_history",
        ],
        "empty_evidence": [],
        "unavailable_evidence": [
            "freshness_history",
        ],
        "evidence_details": [
            {
                "evidence_type": (
                    "freshness_history"
                ),
                "availability_status": (
                    "UNAVAILABLE"
                ),
                "item_count": None,
            },
            {
                "evidence_type": (
                    "volume_history"
                ),
                "availability_status": (
                    "AVAILABLE"
                ),
                "item_count": 1,
            },
        ],
        "sufficiency_status": "PARTIAL",
    }


def test_bounded_controlled_tool_rounds_can_use_initial_plan_without_replanning(
    monkeypatch,
):
    executed_tools: list[str] = []

    initial_tool_requests = [
        {
            "name": "get_freshness_history",
            "arguments": {
                "catalog_id": 4,
            },
        },
        {
            "name": "get_volume_history",
            "arguments": {
                "catalog_id": 4,
            },
        },
    ]

    def fail_first_round_planner(
        question,
        *,
        trusted_version_id,
        trusted_catalog_id=None,
    ):
        del (
            question,
            trusted_version_id,
            trusted_catalog_id,
        )

        raise AssertionError(
            "initial plan must avoid replanning round 1"
        )

    def fake_follow_up_planner(
        question,
        *,
        trusted_version_id,
        trusted_catalog_id=None,
        attempted_tool_names,
    ):
        del (
            question,
            trusted_version_id,
            trusted_catalog_id,
        )

        assert attempted_tool_names == {
            "get_freshness_history",
            "get_volume_history",
        }

        return []

    def fake_execute_plan(
        tool_requests,
        *,
        execution_trace=None,
    ):
        del execution_trace

        executed_tools.extend(
            request["name"]
            for request in tool_requests
        )

        return [
            {
                "name": request["name"],
                "read_only": True,
                "ok": True,
                "result": [],
            }
            for request in tool_requests
        ]

    monkeypatch.setattr(
        controlled_tools,
        "plan_controlled_tool_requests",
        fail_first_round_planner,
    )

    monkeypatch.setattr(
        controlled_tools,
        "plan_follow_up_controlled_tool_requests",
        fake_follow_up_planner,
    )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool_plan",
        fake_execute_plan,
    )

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            "Show evidence.",
            trusted_version_id=6,
            trusted_catalog_id=4,
            initial_tool_requests=(
                initial_tool_requests
            ),
        )
    )

    assert executed_tools == [
        "get_freshness_history",
        "get_volume_history",
    ]

    assert [
        result["name"]
        for result in results
    ] == [
        "get_freshness_history",
        "get_volume_history",
    ]


def test_controlled_evidence_sufficiency_marks_empty_successful_results_insufficient():
    sufficiency = (
        controlled_tools
        .build_controlled_evidence_sufficiency(
            requested_evidence=[
                "freshness_history",
                "volume_history",
                "pipeline_run_history",
            ],
            controlled_tool_results=[
                {
                    "name": "get_freshness_history",
                    "read_only": True,
                    "ok": True,
                    "result": [],
                },
                {
                    "name": "get_volume_history",
                    "read_only": True,
                    "ok": True,
                    "result": [],
                },
                {
                    "name": "get_pipeline_run_history",
                    "read_only": True,
                    "ok": True,
                    "result": [],
                },
            ],
        )
    )

    assert sufficiency == {
        "requested_evidence": [
            "freshness_history",
            "volume_history",
            "pipeline_run_history",
        ],
        "available_evidence": [],
        "empty_evidence": [
            "freshness_history",
            "volume_history",
            "pipeline_run_history",
        ],
        "unavailable_evidence": [],
        "evidence_details": [
            {
                "evidence_type": "freshness_history",
                "availability_status": "EMPTY",
                "item_count": 0,
            },
            {
                "evidence_type": "volume_history",
                "availability_status": "EMPTY",
                "item_count": 0,
            },
            {
                "evidence_type": "pipeline_run_history",
                "availability_status": "EMPTY",
                "item_count": 0,
            },
        ],
        "sufficiency_status": "INSUFFICIENT",
    }


def test_controlled_evidence_sufficiency_distinguishes_available_empty_and_unavailable():
    sufficiency = (
        controlled_tools
        .build_controlled_evidence_sufficiency(
            requested_evidence=[
                "freshness_history",
                "volume_history",
                "pipeline_run_history",
            ],
            controlled_tool_results=[
                {
                    "name": "get_freshness_history",
                    "read_only": True,
                    "ok": True,
                    "result": [
                        {
                            "freshness_status": "FRESH",
                        },
                    ],
                },
                {
                    "name": "get_volume_history",
                    "read_only": True,
                    "ok": True,
                    "result": [],
                },
            ],
        )
    )

    assert sufficiency == {
        "requested_evidence": [
            "freshness_history",
            "volume_history",
            "pipeline_run_history",
        ],
        "available_evidence": [
            "freshness_history",
        ],
        "empty_evidence": [
            "volume_history",
        ],
        "unavailable_evidence": [
            "pipeline_run_history",
        ],
        "evidence_details": [
            {
                "evidence_type": "freshness_history",
                "availability_status": "AVAILABLE",
                "item_count": 1,
            },
            {
                "evidence_type": "volume_history",
                "availability_status": "EMPTY",
                "item_count": 0,
            },
            {
                "evidence_type": "pipeline_run_history",
                "availability_status": "UNAVAILABLE",
                "item_count": None,
            },
        ],
        "sufficiency_status": "PARTIAL",
    }


@pytest.mark.parametrize(
    (
        "requested_evidence",
        "controlled_tool_results",
        "expected_status",
    ),
    [
        (
            [
                "freshness_history",
                "volume_history",
            ],
            [
                {
                    "name": "get_freshness_history",
                    "read_only": True,
                    "ok": True,
                    "result": [
                        {
                            "freshness_status": "FRESH",
                        },
                    ],
                },
                {
                    "name": "get_volume_history",
                    "read_only": True,
                    "ok": True,
                    "result": [
                        {
                            "volume_status": "NORMAL",
                        },
                    ],
                },
            ],
            "SUFFICIENT",
        ),
        (
            [],
            [],
            "NOT_APPLICABLE",
        ),
    ],
)
def test_controlled_evidence_sufficiency_reports_boundary_statuses(
    requested_evidence,
    controlled_tool_results,
    expected_status,
):
    sufficiency = (
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

    assert (
        sufficiency["sufficiency_status"]
        == expected_status
    )


def test_controlled_evidence_answerability_requires_two_items_for_historical_comparison():
    answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=(
                "Compare freshness history "
                "over time."
            ),
            evidence_sufficiency={
                "requested_evidence": [
                    "freshness_history",
                ],
                "available_evidence": [
                    "freshness_history",
                ],
                "empty_evidence": [],
                "unavailable_evidence": [],
                "evidence_details": [
                    {
                        "evidence_type": (
                            "freshness_history"
                        ),
                        "availability_status": (
                            "AVAILABLE"
                        ),
                        "item_count": 1,
                    },
                ],
                "sufficiency_status": (
                    "SUFFICIENT"
                ),
            },
        )
    )

    assert answerability == {
        "assessment_scope": (
            "HISTORICAL_COMPARISON"
        ),
        "assessed_evidence": [
            "freshness_history",
        ],
        "answerable_evidence": [],
        "insufficient_evidence": [
            "freshness_history",
        ],
        "unavailable_evidence": [],
        "evidence_requirements": [
            {
                "evidence_type": (
                    "freshness_history"
                ),
                "minimum_item_count": 2,
                "observed_item_count": 1,
                "requirement_status": (
                    "INSUFFICIENT_ITEMS"
                ),
            },
        ],
        "answerability_status": (
            "NOT_ANSWERABLE"
        ),
    }


def test_controlled_evidence_answerability_accepts_two_items_for_historical_comparison():
    answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=(
                "Compare freshness history "
                "over time."
            ),
            evidence_sufficiency={
                "requested_evidence": [
                    "freshness_history",
                ],
                "available_evidence": [
                    "freshness_history",
                ],
                "empty_evidence": [],
                "unavailable_evidence": [],
                "evidence_details": [
                    {
                        "evidence_type": (
                            "freshness_history"
                        ),
                        "availability_status": (
                            "AVAILABLE"
                        ),
                        "item_count": 2,
                    },
                ],
                "sufficiency_status": (
                    "SUFFICIENT"
                ),
            },
        )
    )

    assert answerability == {
        "assessment_scope": (
            "HISTORICAL_COMPARISON"
        ),
        "assessed_evidence": [
            "freshness_history",
        ],
        "answerable_evidence": [
            "freshness_history",
        ],
        "insufficient_evidence": [],
        "unavailable_evidence": [],
        "evidence_requirements": [
            {
                "evidence_type": (
                    "freshness_history"
                ),
                "minimum_item_count": 2,
                "observed_item_count": 2,
                "requirement_status": (
                    "SATISFIED"
                ),
            },
        ],
        "answerability_status": (
            "ANSWERABLE"
        ),
    }


def test_controlled_evidence_answerability_reports_partial_for_mixed_history_counts():
    answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=(
                "Compare freshness and volume "
                "history over time."
            ),
            evidence_sufficiency={
                "requested_evidence": [
                    "freshness_history",
                    "volume_history",
                ],
                "available_evidence": [
                    "freshness_history",
                    "volume_history",
                ],
                "empty_evidence": [],
                "unavailable_evidence": [],
                "evidence_details": [
                    {
                        "evidence_type": (
                            "freshness_history"
                        ),
                        "availability_status": (
                            "AVAILABLE"
                        ),
                        "item_count": 2,
                    },
                    {
                        "evidence_type": (
                            "volume_history"
                        ),
                        "availability_status": (
                            "AVAILABLE"
                        ),
                        "item_count": 1,
                    },
                ],
                "sufficiency_status": (
                    "SUFFICIENT"
                ),
            },
        )
    )

    assert answerability == {
        "assessment_scope": (
            "HISTORICAL_COMPARISON"
        ),
        "assessed_evidence": [
            "freshness_history",
            "volume_history",
        ],
        "answerable_evidence": [
            "freshness_history",
        ],
        "insufficient_evidence": [
            "volume_history",
        ],
        "unavailable_evidence": [],
        "evidence_requirements": [
            {
                "evidence_type": (
                    "freshness_history"
                ),
                "minimum_item_count": 2,
                "observed_item_count": 2,
                "requirement_status": (
                    "SATISFIED"
                ),
            },
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
        "answerability_status": (
            "PARTIAL"
        ),
    }


def test_controlled_evidence_answerability_is_not_applicable_without_historical_comparison():
    answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=(
                "Show the latest freshness status."
            ),
            evidence_sufficiency={
                "requested_evidence": [
                    "freshness_history",
                ],
                "available_evidence": [
                    "freshness_history",
                ],
                "empty_evidence": [],
                "unavailable_evidence": [],
                "evidence_details": [
                    {
                        "evidence_type": (
                            "freshness_history"
                        ),
                        "availability_status": (
                            "AVAILABLE"
                        ),
                        "item_count": 1,
                    },
                ],
                "sufficiency_status": (
                    "SUFFICIENT"
                ),
            },
        )
    )

    assert answerability == {
        "assessment_scope": (
            "NOT_APPLICABLE"
        ),
        "assessed_evidence": [],
        "answerable_evidence": [],
        "insufficient_evidence": [],
        "unavailable_evidence": [],
        "evidence_requirements": [],
        "answerability_status": (
            "NOT_APPLICABLE"
        ),
    }


def test_controlled_evidence_answerability_marks_unavailable_history_not_answerable():
    answerability = (
        controlled_tools
        .build_controlled_evidence_answerability(
            question=(
                "Compare pipeline history "
                "over time."
            ),
            evidence_sufficiency={
                "requested_evidence": [
                    "pipeline_run_history",
                ],
                "available_evidence": [],
                "empty_evidence": [],
                "unavailable_evidence": [
                    "pipeline_run_history",
                ],
                "evidence_details": [
                    {
                        "evidence_type": (
                            "pipeline_run_history"
                        ),
                        "availability_status": (
                            "UNAVAILABLE"
                        ),
                        "item_count": None,
                    },
                ],
                "sufficiency_status": (
                    "INSUFFICIENT"
                ),
            },
        )
    )

    assert answerability == {
        "assessment_scope": (
            "HISTORICAL_COMPARISON"
        ),
        "assessed_evidence": [
            "pipeline_run_history",
        ],
        "answerable_evidence": [],
        "insufficient_evidence": [],
        "unavailable_evidence": [
            "pipeline_run_history",
        ],
        "evidence_requirements": [
            {
                "evidence_type": (
                    "pipeline_run_history"
                ),
                "minimum_item_count": 2,
                "observed_item_count": None,
                "requirement_status": (
                    "UNAVAILABLE"
                ),
            },
        ],
        "answerability_status": (
            "NOT_ANSWERABLE"
        ),
    }


def test_bounded_controlled_tool_rounds_reports_partial_evidence_answerability(
    monkeypatch,
):
    def fake_execute_tool(
        name,
        arguments,
    ):
        del arguments

        if name == "get_freshness_history":
            return {
                "name": name,
                "read_only": True,
                "ok": True,
                "result": [
                    {
                        "freshness_status": "FRESH",
                    },
                    {
                        "freshness_status": "FRESH",
                    },
                ],
            }

        if name == "get_volume_history":
            return {
                "name": name,
                "read_only": True,
                "ok": True,
                "result": [
                    {
                        "volume_status": "NORMAL",
                    },
                ],
            }

        raise AssertionError(
            f"Unexpected tool: {name}"
        )

    monkeypatch.setattr(
        controlled_tools,
        "execute_controlled_tool",
        fake_execute_tool,
    )

    agent_evidence_answerability: dict = {}

    results = (
        controlled_tools
        .execute_bounded_controlled_tool_rounds(
            (
                "Compare freshness and volume "
                "history over time."
            ),
            trusted_version_id=6,
            trusted_catalog_id=4,
            agent_evidence_answerability=(
                agent_evidence_answerability
            ),
        )
    )

    assert [
        result["name"]
        for result in results
    ] == [
        "get_freshness_history",
        "get_volume_history",
    ]

    assert agent_evidence_answerability == {
        "assessment_scope": (
            "HISTORICAL_COMPARISON"
        ),
        "assessed_evidence": [
            "freshness_history",
            "volume_history",
        ],
        "answerable_evidence": [
            "freshness_history",
        ],
        "insufficient_evidence": [
            "volume_history",
        ],
        "unavailable_evidence": [],
        "evidence_requirements": [
            {
                "evidence_type": (
                    "freshness_history"
                ),
                "minimum_item_count": 2,
                "observed_item_count": 2,
                "requirement_status": (
                    "SATISFIED"
                ),
            },
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
        "answerability_status": (
            "PARTIAL"
        ),
    }