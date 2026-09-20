from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from database.repositories.lineage_repository import (
    get_version_lineage,
)
from src.assistant.platform_context import (
    _json_safe,
)


def _require_positive_int(
    value: Any,
    *,
    field_name: str,
) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ValueError(
            f"{field_name} must be a positive integer."
        )

    return value


LINEAGE_COLLECTION_LIMIT = 20

LINEAGE_COLLECTION_FIELDS = (
    "ingestions",
    "contract_validations",
    "validations",
    "governance_decisions",
    "lifecycle_events",
    "timeline",
)


def _prepare_version_lineage_result(
    lineage: Mapping[str, Any],
) -> dict[str, Any]:
    bounded_lineage = dict(
        lineage
    )

    for field_name in LINEAGE_COLLECTION_FIELDS:
        records = bounded_lineage.get(
            field_name
        )

        if isinstance(
            records,
            list,
        ):
            bounded_lineage[
                field_name
            ] = records[
                -LINEAGE_COLLECTION_LIMIT:
            ]

    json_safe_lineage = _json_safe(
        bounded_lineage
    )

    if not isinstance(
        json_safe_lineage,
        dict,
    ):
        raise ValueError(
            "Version lineage result must be a mapping."
        )

    return json_safe_lineage


def get_controlled_tool_definitions() -> list[
    dict[str, Any]
]:
    return [
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


def parse_controlled_tool_request(
    raw_request: str,
) -> dict[str, Any]:
    if (
        not isinstance(raw_request, str)
        or not raw_request.strip()
    ):
        raise ValueError(
            "Controlled tool request must be "
            "a non-empty JSON string."
        )

    try:
        payload = json.loads(
            raw_request
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Controlled tool request must be valid JSON."
        ) from exc

    if not isinstance(
        payload,
        Mapping,
    ):
        raise ValueError(
            "Controlled tool request must be a JSON object."
        )

    allowed_fields = {
        "name",
        "arguments",
    }

    unexpected_fields = (
        set(payload)
        - allowed_fields
    )

    if unexpected_fields:
        field_name = sorted(
            str(field)
            for field in unexpected_fields
        )[0]

        raise ValueError(
            "Unsupported tool request field: "
            f"{field_name}."
        )

    normalized_name = str(
        payload.get("name") or ""
    ).strip()

    if normalized_name != "get_version_lineage":
        raise ValueError(
            "Unsupported controlled tool: "
            f"{normalized_name or '<empty>'}."
        )

    arguments = payload.get(
        "arguments"
    )

    if not isinstance(
        arguments,
        Mapping,
    ):
        raise ValueError(
            "tool arguments must be a mapping."
        )

    allowed_arguments = {
        "version_id",
    }

    unexpected_arguments = (
        set(arguments)
        - allowed_arguments
    )

    if unexpected_arguments:
        unsupported_argument = sorted(
            str(argument)
            for argument in unexpected_arguments
        )[0]

        raise ValueError(
            "Unsupported tool argument: "
            f"{unsupported_argument}."
        )

    version_id = _require_positive_int(
        arguments.get("version_id"),
        field_name="version_id",
    )

    return {
        "name": "get_version_lineage",
        "arguments": {
            "version_id": version_id,
        },
    }


def select_controlled_tool_request(
    question: str,
    *,
    trusted_version_id: int,
) -> dict[str, Any] | None:
    trusted_version = _require_positive_int(
        trusted_version_id,
        field_name="trusted_version_id",
    )

    if not isinstance(
        question,
        str,
    ):
        raise ValueError(
            "question must be a string."
        )

    normalized_question = (
        question
        .strip()
        .lower()
    )

    if not normalized_question:
        return None

    mutating_terms = (
        "promote",
        "activate",
        "update",
        "delete",
        "remove",
        "cập nhật",
        "xóa",
        "kích hoạt",
        "thay đổi",
    )

    if any(
        term in normalized_question
        for term in mutating_terms
    ):
        return None

    lineage_terms = (
        "lineage",
        "provenance",
        "truy vết",
    )

    if any(
        term in normalized_question
        for term in lineage_terms
    ):
        return {
            "name": "get_version_lineage",
            "arguments": {
                "version_id": trusted_version,
            },
        }

    return None


def bind_controlled_tool_request(
    raw_request: str,
    *,
    trusted_version_id: int,
) -> dict[str, Any]:
    trusted_version = _require_positive_int(
        trusted_version_id,
        field_name="trusted_version_id",
    )

    parsed_request = (
        parse_controlled_tool_request(
            raw_request
        )
    )

    requested_version_id = (
        parsed_request[
            "arguments"
        ][
            "version_id"
        ]
    )

    if (
        requested_version_id
        != trusted_version
    ):
        raise ValueError(
            "Controlled tool request does not "
            "match the trusted version."
        )

    return {
        "name": parsed_request[
            "name"
        ],
        "arguments": {
            "version_id": trusted_version,
        },
    }


def execute_controlled_tool(
    name: str,
    arguments: Mapping[str, Any],
) -> dict[str, Any]:
    normalized_name = str(
        name or ""
    ).strip()

    if normalized_name != "get_version_lineage":
        raise ValueError(
            "Unsupported controlled tool: "
            f"{normalized_name or '<empty>'}."
        )

    if not isinstance(
        arguments,
        Mapping,
    ):
        raise ValueError(
            "tool arguments must be a mapping."
        )

    allowed_arguments = {
        "version_id",
    }

    unexpected_arguments = (
        set(arguments)
        - allowed_arguments
    )

    if unexpected_arguments:
        unsupported_argument = sorted(
            str(argument)
            for argument
            in unexpected_arguments
        )[0]

        raise ValueError(
            "Unsupported tool argument: "
            f"{unsupported_argument}."
        )

    version_id = _require_positive_int(
        arguments.get("version_id"),
        field_name="version_id",
    )

    lineage = get_version_lineage(
        version_id
    )

    lineage_result = (
        _prepare_version_lineage_result(
            lineage
        )
    )

    return {
        "name": "get_version_lineage",
        "read_only": True,
        "ok": True,
        "result": lineage_result,
    }
