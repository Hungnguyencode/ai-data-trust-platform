from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ScanSummaryResponse(BaseModel):
    scan_id: int
    dataset_id: int

    file_name: str
    file_type: str

    total_rows: int
    total_columns: int
    missing_cells: int
    duplicate_rows: int

    total_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    affected_columns: int

    overall_score: float | None = None
    risk_level: str | None = None
    ai_readiness: str | None = None

    created_at: datetime


class QualityIssueResponse(BaseModel):
    issue_id: int
    scan_id: int

    issue_type: str
    column_name: str
    severity: str

    issue_count: int
    issue_rate: float

    description: str | None = None
    recommendation: str | None = None

    created_at: datetime


class ScanHistoryResponse(BaseModel):
    limit: int
    count: int
    items: list[ScanSummaryResponse]


class ScanDetailResponse(BaseModel):
    scan: ScanSummaryResponse
    quality_issue_count: int
    quality_issues: list[QualityIssueResponse]