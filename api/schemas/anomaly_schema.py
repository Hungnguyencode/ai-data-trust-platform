from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AnomalyAnalysisRequest(BaseModel):
    records: list[dict[str, Any]]
    zscore_threshold: float = 3.0
    isolation_contamination: float = 0.1


class AnomalyAnalysisResponse(BaseModel):
    summary: dict[str, Any]
    summary_records: list[dict[str, Any]]
    combined_outlier_records: list[dict[str, Any]]

    iqr_result: dict[str, Any]
    zscore_result: dict[str, Any]
    isolation_forest_result: dict[str, Any]