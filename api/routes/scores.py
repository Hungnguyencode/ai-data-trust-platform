from typing import List

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schemas.score_schema import ScoreComponent, ScoreRequest, ScoreResponse

router = APIRouter()


def _risk_level(score: float) -> str:
    if score >= 80:
        return "Low"
    if score >= 60:
        return "Medium"
    if score >= 40:
        return "High"
    return "Critical"


def _ai_readiness(score: float) -> str:
    if score >= 80:
        return "Ready for Analytics and ML"
    if score >= 60:
        return "Needs Cleaning"
    return "Not Ready"


def _safe_rate(part: float, total: float) -> float:
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


@router.post("/calculate", response_model=ScoreResponse)
def calculate_score(payload: ScoreRequest):
    if not payload.records:
        raise HTTPException(status_code=400, detail="records must not be empty")

    df = pd.DataFrame(payload.records)

    total_rows = int(df.shape[0])
    total_columns = int(df.shape[1])
    total_cells = total_rows * total_columns

    missing_cells = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    missing_rate = _safe_rate(missing_cells, total_cells)
    duplicate_rate = _safe_rate(duplicate_rows, total_rows)

    completeness_score = round(max(0, 100 - missing_rate), 2)
    uniqueness_score = round(max(0, 100 - duplicate_rate), 2)

    validity_penalty = 0
    for col in df.columns:
        numeric_series = pd.to_numeric(df[col], errors="coerce")
        original_non_null = df[col].notna().sum()
        numeric_non_null = numeric_series.notna().sum()

        if original_non_null > 0 and numeric_non_null > 0:
            invalid_numeric_count = max(0, int(original_non_null - numeric_non_null))
            validity_penalty += invalid_numeric_count

    validity_rate = _safe_rate(validity_penalty, total_cells)
    validity_score = round(max(0, 100 - validity_rate * 5), 2)

    consistency_score = round(max(0, 100 - missing_rate * 0.5 - duplicate_rate * 0.5), 2)

    anomaly_score = 100.0

    components: List[ScoreComponent] = [
        ScoreComponent(
            score_name="Completeness",
            score=completeness_score,
            weight=0.25,
            weighted_score=round(completeness_score * 0.25, 2),
            raw_value=missing_rate,
            detail=f"Missing cells: {missing_cells}/{total_cells}.",
        ),
        ScoreComponent(
            score_name="Validity",
            score=validity_score,
            weight=0.25,
            weighted_score=round(validity_score * 0.25, 2),
            raw_value=validity_rate,
            detail=f"Estimated invalid numeric values: {validity_penalty}.",
        ),
        ScoreComponent(
            score_name="Uniqueness",
            score=uniqueness_score,
            weight=0.20,
            weighted_score=round(uniqueness_score * 0.20, 2),
            raw_value=duplicate_rate,
            detail=f"Duplicate rows: {duplicate_rows}/{total_rows}.",
        ),
        ScoreComponent(
            score_name="Consistency",
            score=consistency_score,
            weight=0.15,
            weighted_score=round(consistency_score * 0.15, 2),
            raw_value=round((missing_rate + duplicate_rate) / 2, 2),
            detail="Basic consistency estimated from missing and duplicate rates.",
        ),
        ScoreComponent(
            score_name="Anomaly Safety",
            score=anomaly_score,
            weight=0.15,
            weighted_score=round(anomaly_score * 0.15, 2),
            raw_value=0.0,
            detail="API minimal mode does not run advanced anomaly detection.",
        ),
    ]

    overall_score = round(sum(item.weighted_score for item in components), 2)

    return ScoreResponse(
        file_name=payload.file_name,
        total_rows=total_rows,
        total_columns=total_columns,
        overall_score=overall_score,
        risk_level=_risk_level(overall_score),
        ai_readiness=_ai_readiness(overall_score),
        components=components,
    )