from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schemas.anomaly_schema import (
    AnomalyAnalysisRequest,
    AnomalyAnalysisResponse,
)
from src.anomaly.anomaly_engine import (
    run_anomaly_detection,
)

router = APIRouter()


def _frame_records(
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    if frame.empty:
        return []

    normalized = (
        frame.astype(object)
        .where(
            pd.notna(frame),
            None,
        )
    )

    return normalized.to_dict(
        orient="records"
    )


def _serialize_detector_result(
    result: dict[str, Any],
) -> dict[str, Any]:
    serialized = dict(result)

    summary_df = serialized.pop(
        "summary_df",
        None,
    )

    outlier_rows_df = serialized.pop(
        "outlier_rows_df",
        None,
    )

    scores_df = serialized.pop(
        "scores_df",
        None,
    )

    outlier_indexes = serialized.get(
        "outlier_row_indexes",
        set(),
    )

    serialized[
        "outlier_row_indexes"
    ] = list(
        sorted(outlier_indexes)
    )

    if isinstance(
        summary_df,
        pd.DataFrame,
    ):
        serialized[
            "summary_records"
        ] = _frame_records(summary_df)

    if isinstance(
        outlier_rows_df,
        pd.DataFrame,
    ):
        serialized[
            "outlier_records"
        ] = _frame_records(
            outlier_rows_df
        )

    if isinstance(
        scores_df,
        pd.DataFrame,
    ):
        serialized[
            "score_records"
        ] = _frame_records(scores_df)
    else:
        serialized[
            "score_records"
        ] = []

    return serialized


@router.post(
    "/analyze",
    response_model=AnomalyAnalysisResponse,
)
def analyze_anomalies(
    payload: AnomalyAnalysisRequest,
) -> AnomalyAnalysisResponse:
    if not payload.records:
        raise HTTPException(
            status_code=400,
            detail="records must not be empty",
        )

    dataframe = pd.DataFrame(
        payload.records
    )

    result = run_anomaly_detection(
        dataframe,
        zscore_threshold=(
            payload.zscore_threshold
        ),
        isolation_contamination=(
            payload.isolation_contamination
        ),
    )

    return AnomalyAnalysisResponse(
        summary=result["summary"],
        summary_records=_frame_records(
            result["summary_df"]
        ),
        combined_outlier_records=(
            _frame_records(
                result[
                    "combined_outlier_rows_df"
                ]
            )
        ),
        iqr_result=(
            _serialize_detector_result(
                result["iqr_result"]
            )
        ),
        zscore_result=(
            _serialize_detector_result(
                result["zscore_result"]
            )
        ),
        isolation_forest_result=(
            _serialize_detector_result(
                result[
                    "isolation_forest_result"
                ]
            )
        ),
    )