from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd


def detect_zscore_outliers(
    df: pd.DataFrame,
    threshold: float = 3.0,
) -> Dict[str, Any]:
    """
    Phát hiện outlier bằng Z-score.

    Outlier nếu:
        abs((x - mean) / std) > threshold
    """
    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty:
        return {
            "method": "Z-score",
            "summary_df": pd.DataFrame(),
            "outlier_rows_df": pd.DataFrame(),
            "outlier_row_indexes": set(),
            "total_outlier_rows": 0,
            "outlier_rate (%)": 0.0,
        }

    details: List[Dict[str, Any]] = []
    outlier_row_indexes: set[int] = set()

    for col in numeric_df.columns:
        series = numeric_df[col]
        non_null = series.dropna()

        if len(non_null) < 4:
            continue

        mean = float(non_null.mean())
        std = float(non_null.std(ddof=0))

        if std == 0 or np.isnan(std):
            details.append(
                {
                    "column_name": col,
                    "mean": round(mean, 4),
                    "std": round(std, 4),
                    "threshold": threshold,
                    "outlier_count": 0,
                    "outlier_rate (%)": 0.0,
                }
            )
            continue

        z_scores = (series - mean) / std
        mask = z_scores.abs() > threshold

        outlier_count = int(mask.sum())
        outlier_rate = round(outlier_count / max(len(df), 1) * 100, 2)

        if outlier_count > 0:
            outlier_row_indexes.update(numeric_df[mask].index.tolist())

        details.append(
            {
                "column_name": col,
                "mean": round(mean, 4),
                "std": round(std, 4),
                "threshold": threshold,
                "outlier_count": outlier_count,
                "outlier_rate (%)": outlier_rate,
            }
        )

    outlier_rows_df = df.loc[sorted(outlier_row_indexes)].copy() if outlier_row_indexes else pd.DataFrame()

    total_outlier_rows = len(outlier_row_indexes)
    total_outlier_rate = round(total_outlier_rows / max(len(df), 1) * 100, 2)

    return {
        "method": "Z-score",
        "summary_df": pd.DataFrame(details),
        "outlier_rows_df": outlier_rows_df,
        "outlier_row_indexes": outlier_row_indexes,
        "total_outlier_rows": total_outlier_rows,
        "outlier_rate (%)": total_outlier_rate,
    }