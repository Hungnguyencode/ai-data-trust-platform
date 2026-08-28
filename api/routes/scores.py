import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schemas.score_schema import (
    ScoreComponent,
    ScoreRequest,
    ScoreResponse,
)
from src.scoring.score_engine import calculate_data_trust_score
from src.validation.rule_engine import run_quality_checks


router = APIRouter()


@router.post("/calculate", response_model=ScoreResponse)
def calculate_score(payload: ScoreRequest):
    """
    Calculate Data Trust Score through the single core scoring engine.

    FastAPI must not maintain a separate scoring implementation.
    The same dataset should produce the same result across API,
    Streamlit, tests, and future pipeline jobs.
    """

    if not payload.records:
        raise HTTPException(
            status_code=400,
            detail="records must not be empty",
        )

    df = pd.DataFrame(payload.records)

    # Use the same quality engine as the Streamlit/core workflow.
    quality_report = run_quality_checks(df)

    # Single source of truth for Trust Score.
    trust_score_report = calculate_data_trust_score(
        df=df,
        quality_report=quality_report,
    )

    breakdown_df = trust_score_report["breakdown_df"]

    components = [
        ScoreComponent(
            score_name=str(row["score_name"]),
            score=float(row["score"]),
            weight=float(row["weight"]),
            weighted_score=float(row["weighted_score"]),
            raw_value=float(row["raw_value (%)"]),
            detail=str(row["detail"]),
        )
        for _, row in breakdown_df.iterrows()
    ]

    return ScoreResponse(
        file_name=payload.file_name,
        total_rows=int(df.shape[0]),
        total_columns=int(df.shape[1]),
        overall_score=float(trust_score_report["overall_score"]),
        risk_level=str(trust_score_report["risk_level"]),
        ai_readiness=str(trust_score_report["ai_readiness"]),
        components=components,
    )