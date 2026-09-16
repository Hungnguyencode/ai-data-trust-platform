from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from api.schemas.operational_event_schema import (
    OperationalEventResponse,
)


class VolumePolicyUpdateRequest(BaseModel):
    drop_threshold_pct: float = Field(
        ...,
        gt=0,
        le=100,
    )
    spike_threshold_pct: float = Field(
        ...,
        gt=0,
    )
    is_enabled: bool = True


class VolumePolicyResponse(BaseModel):
    volume_policy_id: int
    catalog_id: int
    drop_threshold_pct: float
    spike_threshold_pct: float
    is_enabled: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class VolumeCheckResponse(BaseModel):
    volume_check_id: int
    volume_policy_id: int
    catalog_id: int
    ingestion_event_id: int
    version_id: int
    baseline_ingestion_event_id: int | None = None
    baseline_version_id: int | None = None
    baseline_row_count: int | None = None
    current_row_count: int
    drop_threshold_pct: float
    spike_threshold_pct: float
    row_change_pct: float | None = None
    volume_status: str
    checked_at: datetime


class VolumeHistoryResponse(BaseModel):
    catalog_id: int
    limit: int
    count: int
    items: list[VolumeCheckResponse]


class VolumeCheckRunResponse(BaseModel):
    policy: VolumePolicyResponse
    check: VolumeCheckResponse
    operational_event: (
        OperationalEventResponse | None
    ) = None