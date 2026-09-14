from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Path, Query

from api.schemas.pipeline_run_schema import (
    PipelineRunHistoryResponse,
    PipelineRunResponse,
)
from database.repositories.pipeline_run_repository import (
    get_pipeline_run as load_pipeline_run,
)
from database.repositories.pipeline_run_repository import (
    get_pipeline_run_history as load_pipeline_run_history,
)

router = APIRouter()


def _frame_records(
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Convert repository DataFrames into API-safe records.

    pandas NaN / NaT values must become Python None before
    Pydantic serializes the response.
    """
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


@router.get(
    "",
    response_model=PipelineRunHistoryResponse,
)
def get_pipeline_runs(
    limit: int = Query(
        default=50,
        ge=1,
        le=1000,
    ),
):
    """
    Return persisted Airflow pipeline run history.
    """
    try:
        history_frame = (
            load_pipeline_run_history(
                limit=limit
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "pipeline run history."
            ),
        ) from exc

    records = _frame_records(
        history_frame
    )

    return PipelineRunHistoryResponse(
        limit=limit,
        count=len(records),
        items=records,
    )


@router.get(
    "/{pipeline_run_id}",
    response_model=PipelineRunResponse,
)
def get_pipeline_run_detail(
    pipeline_run_id: int = Path(
        ...,
        gt=0,
    ),
):
    """
    Return one persisted Airflow pipeline run.
    """
    try:
        pipeline_run = load_pipeline_run(
            pipeline_run_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "pipeline run."
            ),
        ) from exc

    if pipeline_run is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Pipeline run "
                f"{pipeline_run_id} "
                "was not found."
            ),
        )

    return PipelineRunResponse(
        **pipeline_run
    )