from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DriftAnalysisRequest(BaseModel):
    baseline_records: list[dict[str, Any]]
    current_records: list[dict[str, Any]]


class DriftAnalysisResponse(BaseModel):
    summary: dict[str, Any]
    schema_report: dict[str, Any]
    numeric_drift_records: list[dict[str, Any]]
    categorical_drift_records: list[dict[str, Any]]
    all_drift_records: list[dict[str, Any]]


class CategoricalDistributionRequest(BaseModel):
    baseline_records: list[dict[str, Any]]
    current_records: list[dict[str, Any]]
    column_name: str


class CategoricalDistributionResponse(BaseModel):
    distribution_records: list[dict[str, Any]]