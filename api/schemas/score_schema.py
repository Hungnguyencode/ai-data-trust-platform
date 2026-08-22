from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    file_name: str = Field(default="uploaded_dataset.csv")
    file_type: str = Field(default="CSV")
    records: List[Dict[str, Any]]


class ScoreComponent(BaseModel):
    score_name: str
    score: float
    weight: float
    weighted_score: float
    raw_value: float
    detail: str


class ScoreResponse(BaseModel):
    file_name: str
    total_rows: int
    total_columns: int
    overall_score: float
    risk_level: str
    ai_readiness: str
    components: List[ScoreComponent]