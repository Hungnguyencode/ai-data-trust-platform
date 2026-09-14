from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PipelineRunResponse(BaseModel):
    pipeline_run_id: int

    dag_id: str
    airflow_run_id: str
    source_path: str

    run_status: str
    attempt_count: int

    catalog_id: int | None = None
    version_id: int | None = None

    validation_status: str | None = None
    governance_decision: str | None = None
    trust_score: float | None = None
    lifecycle_state: str | None = None

    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None

    error_type: str | None = None
    error_message: str | None = None

    created_at: datetime
    updated_at: datetime


class PipelineRunHistoryResponse(BaseModel):
    limit: int
    count: int
    items: list[PipelineRunResponse]