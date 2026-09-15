from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import text

from database.db import get_engine

EVENT_SEVERITIES = {
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
}


def _normalize_text(
    value: Any,
    *,
    field_name: str,
    max_length: int,
) -> str:
    normalized = str(
        value
    ).strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be empty."
        )

    if len(normalized) > max_length:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{max_length} characters."
        )

    return normalized


def _normalize_optional_text(
    value: Any,
    *,
    field_name: str,
    max_length: int,
) -> str | None:
    if value is None:
        return None

    normalized = str(
        value
    ).strip()

    if not normalized:
        return None

    if len(normalized) > max_length:
        raise ValueError(
            f"{field_name} must not exceed "
            f"{max_length} characters."
        )

    return normalized


def _normalize_optional_id(
    value: Any,
    *,
    field_name: str,
) -> int | None:
    if value is None:
        return None

    normalized = int(
        value
    )

    if normalized <= 0:
        raise ValueError(
            f"{field_name} must be greater than 0."
        )

    return normalized


def _normalize_severity(
    severity: str,
) -> str:
    normalized = str(
        severity
    ).strip().upper()

    if normalized not in EVENT_SEVERITIES:
        raise ValueError(
            "Unsupported operational event "
            f"severity: {severity}"
        )

    return normalized


def _serialize_detail(
    detail: Mapping[str, Any] | None,
) -> str | None:
    if detail is None:
        return None

    return json.dumps(
        dict(detail),
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )


def create_operational_event(
    *,
    event_key: str,
    event_type: str,
    severity: str,
    event_source: str,
    message: str,
    event_stage: str | None = None,
    catalog_id: int | None = None,
    version_id: int | None = None,
    pipeline_run_id: int | None = None,
    reference_id: int | None = None,
    detail: Mapping[str, Any] | None = None,
    occurred_at: datetime | None = None,
) -> dict[str, Any]:
    normalized_key = _normalize_text(
        event_key,
        field_name="event_key",
        max_length=255,
    )

    normalized_type = _normalize_text(
        event_type,
        field_name="event_type",
        max_length=80,
    ).upper()

    normalized_source = _normalize_text(
        event_source,
        field_name="event_source",
        max_length=50,
    ).upper()

    normalized_stage = _normalize_optional_text(
        event_stage,
        field_name="event_stage",
        max_length=80,
    )

    if normalized_stage is not None:
        normalized_stage = (
            normalized_stage.upper()
        )

    normalized_message = _normalize_text(
        message,
        field_name="message",
        max_length=1000,
    )

    normalized_severity = (
        _normalize_severity(
            severity
        )
    )

    existing_query = text(
        """
        SELECT TOP 1
            operational_event_id,
            event_key,
            event_type,
            severity,
            event_source,
            event_stage,
            catalog_id,
            version_id,
            pipeline_run_id,
            reference_id,
            message,
            detail_json,
            occurred_at,
            created_at
        FROM dbo.operational_events
            WITH (
                UPDLOCK,
                HOLDLOCK
            )
        WHERE event_key = :event_key;
        """
    )

    insert_query = text(
        """
        INSERT INTO dbo.operational_events (
            event_key,
            event_type,
            severity,
            event_source,
            event_stage,
            catalog_id,
            version_id,
            pipeline_run_id,
            reference_id,
            message,
            detail_json,
            occurred_at
        )
        OUTPUT
            INSERTED.operational_event_id
        VALUES (
            :event_key,
            :event_type,
            :severity,
            :event_source,
            :event_stage,
            :catalog_id,
            :version_id,
            :pipeline_run_id,
            :reference_id,
            :message,
            :detail_json,
            COALESCE(
                :occurred_at,
                SYSUTCDATETIME()
            )
        );
        """
    )

    params = {
        "event_key": normalized_key,
        "event_type": normalized_type,
        "severity": normalized_severity,
        "event_source": normalized_source,
        "event_stage": normalized_stage,
        "catalog_id": _normalize_optional_id(
            catalog_id,
            field_name="catalog_id",
        ),
        "version_id": _normalize_optional_id(
            version_id,
            field_name="version_id",
        ),
        "pipeline_run_id": _normalize_optional_id(
            pipeline_run_id,
            field_name="pipeline_run_id",
        ),
        "reference_id": _normalize_optional_id(
            reference_id,
            field_name="reference_id",
        ),
        "message": normalized_message,
        "detail_json": _serialize_detail(
            detail
        ),
        "occurred_at": occurred_at,
    }

    engine = get_engine()

    with engine.begin() as connection:
        existing = connection.execute(
            existing_query,
            {
                "event_key": normalized_key,
            },
        ).mappings().first()

        if existing is not None:
            return dict(
                existing
            )

        operational_event_id = (
            connection.execute(
                insert_query,
                params,
            ).scalar_one()
        )

    created_event = (
        get_operational_event(
            int(
                operational_event_id
            )
        )
    )

    if created_event is None:
        raise RuntimeError(
            "Operational event was created "
            "but could not be loaded."
        )

    return created_event


def get_operational_event(
    operational_event_id: int,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT
            operational_event_id,
            event_key,
            event_type,
            severity,
            event_source,
            event_stage,
            catalog_id,
            version_id,
            pipeline_run_id,
            reference_id,
            message,
            detail_json,
            occurred_at,
            created_at
        FROM dbo.operational_events
        WHERE operational_event_id =
            :operational_event_id;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "operational_event_id": int(
                    operational_event_id
                ),
            },
        ).mappings().first()

    if row is None:
        return None

    return dict(
        row
    )


def get_operational_event_history(
    limit: int = 50,
) -> pd.DataFrame:
    safe_limit = max(
        1,
        min(
            int(limit),
            1000,
        ),
    )

    query = text(
        f"""
        SELECT TOP {safe_limit}
            operational_event_id,
            event_key,
            event_type,
            severity,
            event_source,
            event_stage,
            catalog_id,
            version_id,
            pipeline_run_id,
            reference_id,
            message,
            detail_json,
            occurred_at,
            created_at
        FROM dbo.operational_events
        ORDER BY
            occurred_at DESC,
            operational_event_id DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
        )