from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from database.repositories.freshness_repository import (
    get_freshness_history,
)
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


FRESHNESS_HISTORY_LIMIT = 20

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

    if normalized_name not in {
        "get_version_lineage",
        "get_freshness_history",
    }:
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

    argument_name = (
        "version_id"
        if normalized_name
        == "get_version_lineage"
        else "catalog_id"
    )

    allowed_arguments = {
        argument_name,
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

    identifier = _require_positive_int(
        arguments.get(argument_name),
        field_name=argument_name,
    )

    return {
        "name": normalized_name,
        "arguments": {
            argument_name: identifier,
        },
    }


def select_controlled_tool_request(
    question: str,
    *,
    trusted_version_id: int,
    trusted_catalog_id: int | None = None,
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

    freshness_terms = (
        "freshness",
        "stale",
        "độ tươi",
    )

    if any(
        term in normalized_question
        for term in freshness_terms
    ):
        if trusted_catalog_id is None:
            return None

        trusted_catalog = (
            _require_positive_int(
                trusted_catalog_id,
                field_name="trusted_catalog_id",
            )
        )

        return {
            "name": "get_freshness_history",
            "arguments": {
                "catalog_id": trusted_catalog,
            },
        }

    return None


def bind_controlled_tool_request(
    raw_request: str,
    *,
    trusted_version_id: int,
    trusted_catalog_id: int | None = None,
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

    tool_name = parsed_request[
        "name"
    ]

    if tool_name == "get_version_lineage":
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
            "name": tool_name,
            "arguments": {
                "version_id": trusted_version,
            },
        }

    trusted_catalog = _require_positive_int(
        trusted_catalog_id,
        field_name="trusted_catalog_id",
    )

    requested_catalog_id = (
        parsed_request[
            "arguments"
        ][
            "catalog_id"
        ]
    )

    if (
        requested_catalog_id
        != trusted_catalog
    ):
        raise ValueError(
            "Controlled tool request does not "
            "match the trusted catalog."
        )

    return {
        "name": tool_name,
        "arguments": {
            "catalog_id": trusted_catalog,
        },
    }


def execute_controlled_tool(
    name: str,
    arguments: Mapping[str, Any],
) -> dict[str, Any]:
    normalized_name = str(
        name or ""
    ).strip()

    if normalized_name not in {
        "get_version_lineage",
        "get_freshness_history",
    }:
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

    if normalized_name == "get_freshness_history":
        allowed_arguments = {
            "catalog_id",
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

        catalog_id = _require_positive_int(
            arguments.get("catalog_id"),
            field_name="catalog_id",
        )

        freshness_history = (
            get_freshness_history(
                catalog_id,
                limit=FRESHNESS_HISTORY_LIMIT,
            )
        )

        freshness_result = _json_safe(
            freshness_history
        )

        if not isinstance(
            freshness_result,
            list,
        ):
            raise ValueError(
                "Freshness history result must "
                "be a list."
            )

        return {
            "name": "get_freshness_history",
            "read_only": True,
            "ok": True,
            "result": freshness_result,
        }

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
