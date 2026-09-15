from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class OperationalEventResponse(BaseModel):
    operational_event_id: int
    event_key: str

    event_type: str
    severity: str

    event_source: str
    event_stage: str | None = None

    catalog_id: int | None = None
    version_id: int | None = None
    pipeline_run_id: int | None = None
    reference_id: int | None = None

    message: str
    detail_json: str | None = None

    occurred_at: datetime
    created_at: datetime


class OperationalEventHistoryResponse(BaseModel):
    limit: int
    count: int
    items: list[OperationalEventResponse]