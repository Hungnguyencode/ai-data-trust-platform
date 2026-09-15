from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from database.repositories.operational_event_repository import (
    create_operational_event,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def emit_operational_event(
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
) -> dict[str, Any] | None:
    """
    Persist one operational event without allowing
    observability failure to break the main workflow.

    The repository remains responsible for validation,
    idempotency and SQL Server persistence.
    """

    try:
        return create_operational_event(
            event_key=event_key,
            event_type=event_type,
            severity=severity,
            event_source=event_source,
            event_stage=event_stage,
            catalog_id=catalog_id,
            version_id=version_id,
            pipeline_run_id=pipeline_run_id,
            reference_id=reference_id,
            message=message,
            detail=detail,
            occurred_at=occurred_at,
        )

    except Exception:
        logger.exception(
            "Unable to persist operational event: %s",
            event_key,
        )

        return None


def emit_pipeline_failed_event(
    *,
    pipeline_run_id: int,
    event_stage: str,
    error: BaseException,
) -> dict[str, Any] | None:
    return emit_operational_event(
        event_key=(
            f"pipeline-run:{pipeline_run_id}:failed"
        ),
        event_type="PIPELINE_FAILED",
        severity="CRITICAL",
        event_source="AIRFLOW",
        event_stage=event_stage,
        pipeline_run_id=pipeline_run_id,
        message="Airflow pipeline run failed.",
        detail={
            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )