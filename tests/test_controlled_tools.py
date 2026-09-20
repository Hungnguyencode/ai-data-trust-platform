import json
from datetime import datetime

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
