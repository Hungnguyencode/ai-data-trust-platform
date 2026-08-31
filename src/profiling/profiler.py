from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from src.ingestion.schema_infer import get_schema_summary, infer_column_types
from src.profiling.statistics import (
    get_basic_info,
    get_categorical_summary,
    get_duplicate_summary,
    get_missing_summary,
    get_numeric_summary,
)


def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Chạy toàn bộ bước profiling cho dataset.

    Đây là hàm trung tâm của Version 0.1.
    """
    return {
        "basic_info": get_basic_info(df),
        "column_types": infer_column_types(df),
        "schema_summary": get_schema_summary(df),
        "missing_summary": get_missing_summary(df),
        "duplicate_summary": get_duplicate_summary(df),
        "numeric_summary": get_numeric_summary(df),
        "categorical_summary": get_categorical_summary(df),
    }