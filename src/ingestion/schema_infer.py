from __future__ import annotations

import warnings
from typing import Dict, List

import pandas as pd


def infer_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Tự động phân loại cột trong dataset.

    Trả về:
    - numeric_columns
    - categorical_columns
    - datetime_columns
    - boolean_columns
    - text_columns
    """
    numeric_columns: List[str] = []
    categorical_columns: List[str] = []
    datetime_columns: List[str] = []
    boolean_columns: List[str] = []
    text_columns: List[str] = []

    for col in df.columns:
        series = df[col]

        if pd.api.types.is_bool_dtype(series):
            boolean_columns.append(col)

        elif pd.api.types.is_numeric_dtype(series):
            numeric_columns.append(col)

        elif pd.api.types.is_datetime64_any_dtype(series):
            datetime_columns.append(col)

        else:
            # Thử nhận diện datetime nếu cột object có thể parse ngày tháng
            if series.dropna().empty:
                categorical_columns.append(col)
                continue

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                parsed = pd.to_datetime(series.dropna().head(100), errors="coerce")

            datetime_ratio = parsed.notna().mean() if len(parsed) > 0 else 0

            if datetime_ratio >= 0.8:
                datetime_columns.append(col)
            else:
                unique_ratio = series.nunique(dropna=True) / max(len(series), 1)

                if unique_ratio <= 0.5:
                    categorical_columns.append(col)
                else:
                    text_columns.append(col)

    return {
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "datetime_columns": datetime_columns,
        "boolean_columns": boolean_columns,
        "text_columns": text_columns,
    }


def get_schema_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo bảng tổng quan schema của dataset.
    """
    rows = []

    for col in df.columns:
        series = df[col]
        rows.append(
            {
                "column_name": col,
                "dtype": str(series.dtype),
                "non_null_count": int(series.notna().sum()),
                "null_count": int(series.isna().sum()),
                "null_rate (%)": round(series.isna().mean() * 100, 2),
                "unique_count": int(series.nunique(dropna=True)),
                "unique_rate (%)": round(
                    series.nunique(dropna=True) / max(len(series), 1) * 100,
                    2,
                ),
            }
        )

    return pd.DataFrame(rows)