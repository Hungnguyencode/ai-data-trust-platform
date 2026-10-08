from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schemas.drift_schema import (
    CategoricalDistributionRequest,
    CategoricalDistributionResponse,
    DriftAnalysisRequest,
    DriftAnalysisResponse,
)
from src.drift.data_drift import (
    build_categorical_distribution_df,
    run_drift_detection,
)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=DriftAnalysisResponse,
)
def analyze_drift(
    payload: DriftAnalysisRequest,
) -> DriftAnalysisResponse:
    if not payload.baseline_records:
        raise HTTPException(
            status_code=400,
            detail=(
                "baseline_records must not be empty"
            ),
        )
    if not payload.current_records:
        raise HTTPException(
            status_code=400,
            detail=(
                "current_records must not be empty"
            ),
        )
    baseline_df = pd.DataFrame(
        payload.baseline_records
    )
    current_df = pd.DataFrame(
        payload.current_records
    )

    drift_report = run_drift_detection(
        baseline_df=baseline_df,
        current_df=current_df,
    )

    schema_report = drift_report[
        "schema_report"
    ]

    serialized_schema_report = {
        "summary": schema_report["summary"],
        "added_columns": (
            schema_report["added_columns"]
        ),
        "removed_columns": (
            schema_report["removed_columns"]
        ),
        "common_columns": (
            schema_report["common_columns"]
        ),
        "dtype_changes": (
            schema_report["dtype_changes"]
        ),
        "change_records": (
            schema_report["changes_df"]
            .to_dict(
                orient="records",
            )
        ),
    }

    return DriftAnalysisResponse(
        summary=drift_report["summary"],
        schema_report=serialized_schema_report,
        numeric_drift_records=(
            drift_report["numeric_drift_df"]
            .to_dict(
                orient="records",
            )
        ),
        categorical_drift_records=(
            drift_report[
                "categorical_drift_df"
            ]
            .to_dict(
                orient="records",
            )
        ),
        all_drift_records=(
            drift_report["all_drift_df"]
            .to_dict(
                orient="records",
            )
        ),
    )


@router.post(
    "/categorical-distribution",
    response_model=CategoricalDistributionResponse,
)
def get_categorical_distribution(
    payload: CategoricalDistributionRequest,
) -> CategoricalDistributionResponse:
    if not payload.baseline_records:
        raise HTTPException(
            status_code=400,
            detail=(
                "baseline_records must not be empty"
            ),
        )

    if not payload.current_records:
        raise HTTPException(
            status_code=400,
            detail=(
                "current_records must not be empty"
            ),
        )

    baseline_df = pd.DataFrame(
        payload.baseline_records
    )
    current_df = pd.DataFrame(
        payload.current_records
    )

    if (
        payload.column_name
        not in baseline_df.columns
        or payload.column_name
        not in current_df.columns
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "column_name must exist in both datasets"
            ),
        )

    distribution_df = (
        build_categorical_distribution_df(
            baseline_df=baseline_df,
            current_df=current_df,
            column_name=payload.column_name,
        )
    )

    return CategoricalDistributionResponse(
        distribution_records=(
            distribution_df.to_dict(
                orient="records",
            )
        ),
    )