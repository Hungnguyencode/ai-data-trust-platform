from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from api.schemas.operational_event_schema import (
    OperationalEventResponse,
)


class FreshnessPolicyUpdateRequest(BaseModel):
    max_age_minutes: int = Field(
        ...,
        gt=0,
    )
    is_enabled: bool = True


class FreshnessPolicyResponse(BaseModel):
    freshness_policy_id: int
    catalog_id: int
    max_age_minutes: int
    is_enabled: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FreshnessCheckResponse(BaseModel):
    freshness_check_id: int
    catalog_id: int
    ingestion_event_id: int | None = None
    version_id: int | None = None
    max_age_minutes: int
    age_minutes: int | None = None
    freshness_status: str
    latest_ingested_at: datetime | None = None
    checked_at: datetime


class FreshnessHistoryResponse(BaseModel):
    catalog_id: int
    limit: int
    count: int
    items: list[FreshnessCheckResponse]


class FreshnessCheckRunResponse(BaseModel):
    policy: FreshnessPolicyResponse
    check: FreshnessCheckResponse
    operational_event: (
        OperationalEventResponse | None
    ) = None