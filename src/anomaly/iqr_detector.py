from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def detect_iqr_outliers(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Phát hiện outlier bằng phương pháp IQR cho từng cột numeric.

    Outlier nếu:
        value < Q1 - 1.5 * IQR
        value > Q3 + 1.5 * IQR
    """
    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty:
        return {
            "method": "IQR",
            "summary_df": pd.DataFrame(),
            "outlier_rows_df": pd.DataFrame(),
            "outlier_row_indexes": set(),
            "total_outlier_rows": 0,
            "outlier_rate (%)": 0.0,
        }

    details: List[Dict[str, Any]] = []
    outlier_row_indexes: set[int] = set()

    for col in numeric_df.columns:
        series = numeric_df[col].dropna()

        if len(series) < 4:
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1

        if iqr == 0:
            details.append(
                {
                    "column_name": col,
                    "q1": round(q1, 4),
                    "q3": round(q3, 4),
                    "iqr": round(iqr, 4),
                    "lower_bound": None,
                    "upper_bound": None,
                    "outlier_count": 0,
                    "outlier_rate (%)": 0.0,
                }
            )
            continue

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        mask = (numeric_df[col] < lower_bound) | (numeric_df[col] > upper_bound)
        outlier_count = int(mask.sum())
        outlier_rate = round(outlier_count / max(len(df), 1) * 100, 2)

        if outlier_count > 0:
            outlier_row_indexes.update(numeric_df[mask].index.tolist())

        details.append(
            {
                "column_name": col,
                "q1": round(q1, 4),
                "q3": round(q3, 4),
                "iqr": round(iqr, 4),
                "lower_bound": round(float(lower_bound), 4),
                "upper_bound": round(float(upper_bound), 4),
                "outlier_count": outlier_count,
                "outlier_rate (%)": outlier_rate,
            }
        )

    outlier_rows_df = df.loc[sorted(outlier_row_indexes)].copy() if outlier_row_indexes else pd.DataFrame()

    total_outlier_rows = len(outlier_row_indexes)
    total_outlier_rate = round(total_outlier_rows / max(len(df), 1) * 100, 2)

    return {
        "method": "IQR",
        "summary_df": pd.DataFrame(details),
        "outlier_rows_df": outlier_rows_df,
        "outlier_row_indexes": outlier_row_indexes,
        "total_outlier_rows": total_outlier_rows,
        "outlier_rate (%)": total_outlier_rate,
    }