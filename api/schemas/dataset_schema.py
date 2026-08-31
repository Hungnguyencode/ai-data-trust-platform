from typing import Any, Dict, List

from pydantic import BaseModel, Field


class DatasetRecordsRequest(BaseModel):
    file_name: str = Field(default="uploaded_dataset.csv")
    file_type: str = Field(default="CSV")
    records: List[Dict[str, Any]]


class DatasetOverviewResponse(BaseModel):
    file_name: str
    file_type: str
    total_rows: int
    total_columns: int
    total_cells: int
    missing_cells: int
    duplicate_rows: int
    columns: List[str]


class DatasetPreviewResponse(BaseModel):
    file_name: str
    preview_rows: List[Dict[str, Any]]
    total_rows: int