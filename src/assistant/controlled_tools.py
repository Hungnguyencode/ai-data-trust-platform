from __future__ import annotations

import json
import time
from collections.abc import Mapping
from typing import Any

from database.repositories.freshness_repository import (
    get_freshness_history,
)
from database.repositories.lineage_repository import (
    get_version_lineage,
)
from database.repositories.operational_event_repository import (
    get_operational_event_history_by_catalog,
)
from database.repositories.pipeline_run_repository import (
    get_pipeline_run_history_by_catalog,
)
from database.repositories.volume_repository import (
    get_volume_history,
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
OPERATIONAL_EVENT_HISTORY_LIMIT = 20
PIPELINE_RUN_HISTORY_LIMIT = 20
VOLUME_HISTORY_LIMIT = 20
CONTROLLED_TOOL_PLAN_LIMIT = 3
CONTROLLED_TOOL_MAX_ROUNDS = 2

CONTROLLED_TOOL_EVIDENCE_TYPES = {
    "get_version_lineage": (
        "version_lineage"
    ),
    "get_freshness_history": (
        "freshness_history"
    ),
    "get_volume_history": (
        "volume_history"
    ),
    "get_pipeline_run_history": (
        "pipeline_run_history"
    ),
    "get_operational_event_history": (
        "operational_event_history"
    ),
}

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
        "get_volume_history",
        "get_pipeline_run_history",
        "get_operational_event_history",
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

    volume_terms = (
        "volume",
        "row count",
        "rowcount",
        "spike",
        "drop",
        "số dòng",
    )

    if any(
        term in normalized_question
        for term in volume_terms
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
            "name": "get_volume_history",
            "arguments": {
                "catalog_id": trusted_catalog,
            },
        }

    pipeline_terms = (
        "pipeline",
        "airflow",
    )

    if any(
        term in normalized_question
        for term in pipeline_terms
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
            "name": "get_pipeline_run_history",
            "arguments": {
                "catalog_id": trusted_catalog,
            },
        }

    operational_event_terms = (
        "operational event",
        "operational events",
        "operational alert",
        "operational alerts",
        "alert",
        "incident",
        "sự kiện vận hành",
        "cảnh báo vận hành",
        "cảnh báo",
        "sự cố vận hành",
        "sự cố",
    )

    if any(
        term in normalized_question
        for term in operational_event_terms
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
            "name": "get_operational_event_history",
            "arguments": {
                "catalog_id": trusted_catalog,
            },
        }

    return None


def _build_controlled_tool_candidates(
    question: str,
    *,
    trusted_version_id: int,
    trusted_catalog_id: int | None = None,
) -> list[dict[str, Any]]:
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
        return []

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
        return []

    plan: list[
        dict[str, Any]
    ] = []

    lineage_terms = (
        "lineage",
        "provenance",
        "truy vết",
    )

    if any(
        term in normalized_question
        for term in lineage_terms
    ):
        plan.append(
            {
                "name": "get_version_lineage",
                "arguments": {
                    "version_id": trusted_version,
                },
            }
        )

    freshness_terms = (
        "freshness",
        "stale",
        "độ tươi",
    )

    if any(
        term in normalized_question
        for term in freshness_terms
    ):
        if trusted_catalog_id is not None:
            trusted_catalog = (
                _require_positive_int(
                    trusted_catalog_id,
                    field_name="trusted_catalog_id",
                )
            )

            plan.append(
                {
                    "name": "get_freshness_history",
                    "arguments": {
                        "catalog_id": trusted_catalog,
                    },
                }
            )

    volume_terms = (
        "volume",
        "row count",
        "rowcount",
        "spike",
        "drop",
        "số dòng",
    )

    if any(
        term in normalized_question
        for term in volume_terms
    ):
        if trusted_catalog_id is not None:
            trusted_catalog = (
                _require_positive_int(
                    trusted_catalog_id,
                    field_name="trusted_catalog_id",
                )
            )

            plan.append(
                {
                    "name": "get_volume_history",
                    "arguments": {
                        "catalog_id": trusted_catalog,
                    },
                }
            )

    pipeline_terms = (
        "pipeline",
        "airflow",
    )

    if any(
        term in normalized_question
        for term in pipeline_terms
    ):
        if trusted_catalog_id is not None:
            trusted_catalog = (
                _require_positive_int(
                    trusted_catalog_id,
                    field_name="trusted_catalog_id",
                )
            )

            plan.append(
                {
                    "name": "get_pipeline_run_history",
                    "arguments": {
                        "catalog_id": trusted_catalog,
                    },
                }
            )

    operational_event_terms = (
        "operational event",
        "operational events",
        "operational alert",
        "operational alerts",
        "alert",
        "incident",
        "sự kiện vận hành",
        "cảnh báo vận hành",
        "cảnh báo",
        "sự cố vận hành",
        "sự cố",
    )

    if any(
        term in normalized_question
        for term in operational_event_terms
    ):
        if trusted_catalog_id is not None:
            trusted_catalog = (
                _require_positive_int(
                    trusted_catalog_id,
                    field_name="trusted_catalog_id",
                )
            )

            plan.append(
                {
                    "name": "get_operational_event_history",
                    "arguments": {
                        "catalog_id": trusted_catalog,
                    },
                }
            )

    return plan


def plan_controlled_evidence_requirements(
    question: str,
    *,
    trusted_version_id: int,
    trusted_catalog_id: int | None = None,
) -> list[str]:
    candidates = (
        _build_controlled_tool_candidates(
            question,
            trusted_version_id=(
                trusted_version_id
            ),
            trusted_catalog_id=(
                trusted_catalog_id
            ),
        )
    )

    evidence: list[str] = []

    for request in candidates:
        tool_name = str(
            request["name"]
        )

        evidence_type = (
            CONTROLLED_TOOL_EVIDENCE_TYPES.get(
                tool_name
            )
        )

        if evidence_type is not None:
            evidence.append(
                evidence_type
            )

    return evidence


def build_controlled_evidence_coverage(
    *,
    requested_evidence: list[str],
    attempted_tool_names: list[str],
    accepted_tool_names: list[str],
) -> dict[str, Any]:
    requested = list(
        dict.fromkeys(
            requested_evidence
        )
    )

    requested_evidence_set = set(
        requested
    )

    attempted_evidence: list[str] = []
    attempted_evidence_set: set[str] = set()

    for tool_name in attempted_tool_names:
        evidence_type = (
            CONTROLLED_TOOL_EVIDENCE_TYPES.get(
                tool_name
            )
        )

        if (
            evidence_type is None
            or evidence_type
            not in requested_evidence_set
            or evidence_type
            in attempted_evidence_set
        ):
            continue

        attempted_evidence.append(
            evidence_type
        )

        attempted_evidence_set.add(
            evidence_type
        )

    accepted_evidence: list[str] = []
    accepted_evidence_set: set[str] = set()

    for tool_name in accepted_tool_names:
        evidence_type = (
            CONTROLLED_TOOL_EVIDENCE_TYPES.get(
                tool_name
            )
        )

        if (
            evidence_type is None
            or evidence_type
            not in requested_evidence_set
            or evidence_type
            not in attempted_evidence_set
            or evidence_type
            in accepted_evidence_set
        ):
            continue

        accepted_evidence.append(
            evidence_type
        )

        accepted_evidence_set.add(
            evidence_type
        )

    missing_evidence = [
        evidence_type
        for evidence_type in requested
        if evidence_type
        not in accepted_evidence_set
    ]

    if not requested:
        coverage_status = (
            "NOT_APPLICABLE"
        )

    elif not accepted_evidence:
        coverage_status = "NONE"

    elif len(
        accepted_evidence
    ) == len(
        requested
    ):
        coverage_status = "COMPLETE"

    else:
        coverage_status = "PARTIAL"

    return {
        "requested_evidence": requested,
        "attempted_evidence": (
            attempted_evidence
        ),
        "accepted_evidence": (
            accepted_evidence
        ),
        "missing_evidence": (
            missing_evidence
        ),
        "coverage_status": (
            coverage_status
        ),
    }


def build_controlled_evidence_sufficiency(
    *,
    requested_evidence: list[str],
    controlled_tool_results: list[
        Mapping[str, Any]
    ],
) -> dict[str, Any]:
    requested = list(
        dict.fromkeys(
            requested_evidence
        )
    )

    requested_set = set(
        requested
    )

    result_by_evidence: dict[
        str,
        Any,
    ] = {}

    for item in controlled_tool_results:
        if not isinstance(
            item,
            Mapping,
        ):
            continue

        tool_name = str(
            item.get(
                "name",
                "",
            )
            or ""
        )

        evidence_type = (
            CONTROLLED_TOOL_EVIDENCE_TYPES.get(
                tool_name
            )
        )

        if (
            evidence_type is None
            or evidence_type
            not in requested_set
            or evidence_type
            in result_by_evidence
            or item.get("ok") is not True
        ):
            continue

        result_by_evidence[
            evidence_type
        ] = item.get(
            "result"
        )

    available_evidence: list[str] = []
    empty_evidence: list[str] = []
    unavailable_evidence: list[str] = []
    evidence_details: list[
        dict[str, Any]
    ] = []

    for evidence_type in requested:
        if (
            evidence_type
            not in result_by_evidence
        ):
            unavailable_evidence.append(
                evidence_type
            )

            evidence_details.append(
                {
                    "evidence_type": (
                        evidence_type
                    ),
                    "availability_status": (
                        "UNAVAILABLE"
                    ),
                    "item_count": None,
                }
            )

            continue

        result = result_by_evidence[
            evidence_type
        ]

        if isinstance(
            result,
            Mapping,
        ):
            item_count = (
                1
                if result
                else 0
            )

        elif isinstance(
            result,
            (list, tuple),
        ):
            item_count = len(
                result
            )

        elif result is None:
            item_count = 0

        else:
            item_count = 1

        if item_count > 0:
            availability_status = (
                "AVAILABLE"
            )

            available_evidence.append(
                evidence_type
            )

        else:
            availability_status = "EMPTY"

            empty_evidence.append(
                evidence_type
            )

        evidence_details.append(
            {
                "evidence_type": (
                    evidence_type
                ),
                "availability_status": (
                    availability_status
                ),
                "item_count": item_count,
            }
        )

    if not requested:
        sufficiency_status = (
            "NOT_APPLICABLE"
        )

    elif len(
        available_evidence
    ) == len(
        requested
    ):
        sufficiency_status = "SUFFICIENT"

    elif available_evidence:
        sufficiency_status = "PARTIAL"

    else:
        sufficiency_status = (
            "INSUFFICIENT"
        )

    return {
        "requested_evidence": requested,
        "available_evidence": (
            available_evidence
        ),
        "empty_evidence": (
            empty_evidence
        ),
        "unavailable_evidence": (
            unavailable_evidence
        ),
        "evidence_details": (
            evidence_details
        ),
        "sufficiency_status": (
            sufficiency_status
        ),
    }


def plan_controlled_tool_requests(
    question: str,
    *,
    trusted_version_id: int,
    trusted_catalog_id: int | None = None,
) -> list[dict[str, Any]]:
    candidates = (
        _build_controlled_tool_candidates(
            question,
            trusted_version_id=(
                trusted_version_id
            ),
            trusted_catalog_id=(
                trusted_catalog_id
            ),
        )
    )

    return candidates[
        :CONTROLLED_TOOL_PLAN_LIMIT
    ]


def plan_follow_up_controlled_tool_requests(
    question: str,
    *,
    trusted_version_id: int,
    trusted_catalog_id: int | None = None,
    attempted_tool_names: set[str],
) -> list[dict[str, Any]]:
    candidates = (
        _build_controlled_tool_candidates(
            question,
            trusted_version_id=(
                trusted_version_id
            ),
            trusted_catalog_id=(
                trusted_catalog_id
            ),
        )
    )

    remaining = [
        request
        for request in candidates
        if request["name"]
        not in attempted_tool_names
    ]

    return remaining[
        :CONTROLLED_TOOL_PLAN_LIMIT
    ]


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
        "get_volume_history",
        "get_pipeline_run_history",
        "get_operational_event_history",
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

    if normalized_name == "get_volume_history":
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

        volume_history = (
            get_volume_history(
                catalog_id,
                limit=VOLUME_HISTORY_LIMIT,
            )
        )

        volume_result = _json_safe(
            volume_history
        )

        if not isinstance(
            volume_result,
            list,
        ):
            raise ValueError(
                "Volume history result must "
                "be a list."
            )

        return {
            "name": "get_volume_history",
            "read_only": True,
            "ok": True,
            "result": volume_result,
        }

    if normalized_name == "get_pipeline_run_history":
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

        pipeline_history = (
            get_pipeline_run_history_by_catalog(
                catalog_id,
                limit=PIPELINE_RUN_HISTORY_LIMIT,
            )
        )

        pipeline_result = _json_safe(
            pipeline_history
        )

        if not isinstance(
            pipeline_result,
            list,
        ):
            raise ValueError(
                "Pipeline run history result must "
                "be a list."
            )

        return {
            "name": "get_pipeline_run_history",
            "read_only": True,
            "ok": True,
            "result": pipeline_result,
        }

    if normalized_name == "get_operational_event_history":
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

        event_history = (
            get_operational_event_history_by_catalog(
                catalog_id,
                limit=OPERATIONAL_EVENT_HISTORY_LIMIT,
            )
        )

        event_result = _json_safe(
            event_history
        )

        if not isinstance(
            event_result,
            list,
        ):
            raise ValueError(
                "Operational event history result must "
                "be a list."
            )

        return {
            "name": "get_operational_event_history",
            "read_only": True,
            "ok": True,
            "result": event_result,
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


def execute_controlled_tool_plan(
    tool_requests: list[
        Mapping[str, Any]
    ],
    *,
    execution_trace: (
        list[dict[str, Any]] | None
    ) = None,
) -> list[dict[str, Any]]:
    results: list[
        dict[str, Any]
    ] = []

    trace_step_start = (
        len(execution_trace) + 1
        if execution_trace is not None
        else 1
    )

    for step, tool_request in enumerate(
        tool_requests[
            :CONTROLLED_TOOL_PLAN_LIMIT
        ],
        start=trace_step_start,
    ):
        started_at = time.perf_counter()

        tool_result = None
        error_type = None

        try:
            tool_name = tool_request[
                "name"
            ]

            tool_arguments = tool_request[
                "arguments"
            ]

            tool_result = (
                execute_controlled_tool(
                    tool_name,
                    tool_arguments,
                )
            )

        except Exception as exc:
            error_type = type(
                exc
            ).__name__

            tool_result = None

        duration_ms = round(
            (
                time.perf_counter()
                - started_at
            )
            * 1000,
            3,
        )

        evidence_accepted = (
            tool_result is not None
        )

        if tool_result is not None:
            results.append(
                tool_result
            )

        if execution_trace is not None:
            execution_trace.append(
                {
                    "step": step,
                    "tool_name": (
                        str(
                            tool_request.get(
                                "name",
                                "UNKNOWN",
                            )
                        )
                        if isinstance(
                            tool_request,
                            Mapping,
                        )
                        else "UNKNOWN"
                    ),
                    "arguments": (
                        dict(
                            tool_request.get(
                                "arguments",
                                {},
                            )
                        )
                        if (
                            isinstance(
                                tool_request,
                                Mapping,
                            )
                            and isinstance(
                                tool_request.get(
                                    "arguments"
                                ),
                                Mapping,
                            )
                        )
                        else {}
                    ),
                    "status": (
                        "SUCCEEDED"
                        if evidence_accepted
                        else "FAILED"
                    ),
                    "duration_ms": (
                        duration_ms
                    ),
                    "evidence_accepted": (
                        evidence_accepted
                    ),
                    "error_type": (
                        error_type
                    ),
                }
            )

    return results


def execute_bounded_controlled_tool_rounds(
    question: str,
    *,
    trusted_version_id: int,
    trusted_catalog_id: int | None = None,
    execution_trace: (
        list[dict[str, Any]] | None
    ) = None,
    initial_tool_requests: (
        list[dict[str, Any]] | None
    ) = None,
    agent_run_summary: (
        dict[str, Any] | None
    ) = None,
    agent_evidence_coverage: (
        dict[str, Any] | None
    ) = None,
    agent_evidence_sufficiency: (
        dict[str, Any] | None
    ) = None,
) -> list[dict[str, Any]]:
    results: list[
        dict[str, Any]
    ] = []

    attempted_tool_names: set[
        str
    ] = set()

    attempted_tool_names_in_order: list[
        str
    ] = []

    accepted_tool_names: list[
        str
    ] = []

    attempted_tool_count = 0
    round_count = 0

    stop_reason = (
        "MAX_ROUNDS_REACHED"
    )

    requested_evidence: list[str] = []

    if agent_run_summary is not None:
        agent_run_summary.clear()

    if agent_evidence_coverage is not None:
        agent_evidence_coverage.clear()

    if agent_evidence_sufficiency is not None:
        agent_evidence_sufficiency.clear()

    if (
        agent_evidence_coverage is not None
        or agent_evidence_sufficiency is not None
    ):
        requested_evidence = (
            plan_controlled_evidence_requirements(
                question,
                trusted_version_id=(
                    trusted_version_id
                ),
                trusted_catalog_id=(
                    trusted_catalog_id
                ),
            )
        )

    for round_number in range(
        1,
        CONTROLLED_TOOL_MAX_ROUNDS + 1,
    ):
        if round_number == 1:
            if initial_tool_requests is not None:
                tool_requests = (
                    initial_tool_requests[
                        :CONTROLLED_TOOL_PLAN_LIMIT
                    ]
                )

            else:
                tool_requests = (
                    plan_controlled_tool_requests(
                        question,
                        trusted_version_id=(
                            trusted_version_id
                        ),
                        trusted_catalog_id=(
                            trusted_catalog_id
                        ),
                    )
                )

        else:
            tool_requests = (
                plan_follow_up_controlled_tool_requests(
                    question,
                    trusted_version_id=(
                        trusted_version_id
                    ),
                    trusted_catalog_id=(
                        trusted_catalog_id
                    ),
                    attempted_tool_names=(
                        attempted_tool_names
                    ),
                )
            )

        if not tool_requests:
            stop_reason = (
                "NO_TOOL_REQUESTS"
                if round_number == 1
                else (
                    "NO_UNATTEMPTED_REQUESTED_TOOLS"
                )
            )

            break

        tool_requests = tool_requests[
            :CONTROLLED_TOOL_PLAN_LIMIT
        ]

        round_count += 1

        attempted_tool_count += len(
            tool_requests
        )

        attempted_tool_names.update(
            str(
                request["name"]
            )
            for request in tool_requests
        )

        attempted_tool_names_in_order.extend(
            str(
                request["name"]
            )
            for request in tool_requests
        )

        round_results = (
            execute_controlled_tool_plan(
                tool_requests,
                execution_trace=(
                    execution_trace
                ),
            )
        )

        results.extend(
            round_results
        )

        accepted_tool_names.extend(
            str(
                result["name"]
            )
            for result in round_results
        )

    if agent_run_summary is not None:
        accepted_evidence_count = len(
            results
        )

        agent_run_summary.update(
            {
                "round_count": round_count,
                "stop_reason": stop_reason,
                "attempted_tool_count": (
                    attempted_tool_count
                ),
                "accepted_evidence_count": (
                    accepted_evidence_count
                ),
                "failed_tool_count": (
                    attempted_tool_count
                    - accepted_evidence_count
                ),
            }
        )

    if agent_evidence_coverage is not None:
        agent_evidence_coverage.update(
            build_controlled_evidence_coverage(
                requested_evidence=(
                    requested_evidence
                ),
                attempted_tool_names=(
                    attempted_tool_names_in_order
                ),
                accepted_tool_names=(
                    accepted_tool_names
                ),
            )
        )

    if agent_evidence_sufficiency is not None:
        agent_evidence_sufficiency.update(
            build_controlled_evidence_sufficiency(
                requested_evidence=(
                    requested_evidence
                ),
                controlled_tool_results=(
                    results
                ),
            )
        )

    return results
