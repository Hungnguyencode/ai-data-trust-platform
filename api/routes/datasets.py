import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schemas.dataset_schema import (
    DatasetOverviewResponse,
    DatasetPreviewResponse,
    DatasetRecordsRequest,
)

router = APIRouter()


@router.post("/overview", response_model=DatasetOverviewResponse)
def get_dataset_overview(payload: DatasetRecordsRequest):
    if not payload.records:
        raise HTTPException(status_code=400, detail="records must not be empty")

    df = pd.DataFrame(payload.records)

    return DatasetOverviewResponse(
        file_name=payload.file_name,
        file_type=payload.file_type,
        total_rows=int(df.shape[0]),
        total_columns=int(df.shape[1]),
        total_cells=int(df.shape[0] * df.shape[1]),
        missing_cells=int(df.isna().sum().sum()),
        duplicate_rows=int(df.duplicated().sum()),
        columns=list(df.columns),
    )


@router.post("/preview", response_model=DatasetPreviewResponse)
def get_dataset_preview(payload: DatasetRecordsRequest):
    if not payload.records:
        raise HTTPException(status_code=400, detail="records must not be empty")

    df = pd.DataFrame(payload.records)

    return DatasetPreviewResponse(
        file_name=payload.file_name,
        preview_rows=df.head(10).where(pd.notnull(df), None).to_dict(orient="records"),
        total_rows=int(df.shape[0]),
    )