from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class QualityReportEvidence(BaseModel):
    summary: dict[str, Any]
    issue_records: list[dict[str, Any]]


class TrustScoreEvidence(BaseModel):
    overall_score: float
    risk_level: str
    ai_readiness: str
    conclusion: str
    breakdown_records: list[dict[str, Any]]


class PrivacyReportEvidence(BaseModel):
    summary: dict[str, Any]
    finding_records: list[dict[str, Any]]


class DriftReportEvidence(BaseModel):
    summary: dict[str, Any]
    baseline_file_name: str
    current_file_name: str
    numeric_drift_records: list[dict[str, Any]]
    categorical_drift_records: list[dict[str, Any]]
    schema_change_records: list[dict[str, Any]]


class ProfileEvidence(BaseModel):
    basic_info: dict[str, Any]


class HtmlReportRequest(BaseModel):
    file_name: str
    file_type: str
    total_rows: int
    total_columns: int
    quality: QualityReportEvidence | None = None
    trust_score: TrustScoreEvidence | None = None
    privacy: PrivacyReportEvidence | None = None
    drift: DriftReportEvidence | None = None
    profile: ProfileEvidence | None = None


class HtmlReportResponse(BaseModel):
    report_file_name: str
    html_content: str


class HtmlReportSaveRequest(BaseModel):
    html_content: str
    report_file_name: str


class HtmlReportSaveResponse(BaseModel):
    report_file_name: str
    saved_path: str