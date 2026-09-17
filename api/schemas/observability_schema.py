from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DatasetObservabilityResponse(BaseModel):
    catalog_id: int

    freshness_enabled: bool
    freshness_status: str | None = None
    freshness_checked_at: datetime | None = None

    volume_enabled: bool
    volume_status: str | None = None
    volume_checked_at: datetime | None = None

    latest_pipeline_run_id: int | None = None
    latest_pipeline_status: str | None = None
    latest_pipeline_finished_at: datetime | None = None

    recent_operational_event_count: int = 0


class ObservabilitySummaryResponse(BaseModel):
    monitored_dataset_count: int

    freshness_policy_count: int
    freshness_breach_count: int

    volume_policy_count: int
    volume_breach_count: int

    operational_event_count: int
    recent_failed_pipeline_run_count: int


class ObservabilityOverviewResponse(BaseModel):
    summary: ObservabilitySummaryResponse
    datasets: list[DatasetObservabilityResponse]