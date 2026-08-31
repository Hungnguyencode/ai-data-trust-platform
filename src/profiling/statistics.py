from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def get_basic_info(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Trả về thông tin tổng quan của dataset.
    """
    total_rows = len(df)
    total_columns = len(df.columns)
    total_cells = total_rows * total_columns

    missing_cells = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "total_cells": total_cells,
        "missing_cells": missing_cells,
        "missing_rate": round(missing_cells / max(total_cells, 1) * 100, 2),
        "duplicate_rows": duplicate_rows,
        "duplicate_rate": round(duplicate_rows / max(total_rows, 1) * 100, 2),
    }


def get_missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Thống kê missing value theo từng cột.
    """
    summary = pd.DataFrame(
        {
            "column_name": df.columns,
            "missing_count": df.isna().sum().values,
            "missing_rate (%)": (df.isna().mean().values * 100).round(2),
        }
    )

    summary = summary.sort_values(
        by="missing_rate (%)",
        ascending=False,
    ).reset_index(drop=True)

    return summary


def get_duplicate_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Thống kê dòng trùng lặp.
    """
    duplicate_count = int(df.duplicated().sum())
    duplicate_rate = round(duplicate_count / max(len(df), 1) * 100, 2)

    return {
        "duplicate_rows": duplicate_count,
        "duplicate_rate": duplicate_rate,
    }


def get_numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Thống kê mô tả cho các cột số.
    """
    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty:
        return pd.DataFrame()

    summary = numeric_df.describe().T.reset_index()
    summary = summary.rename(columns={"index": "column_name"})

    return summary


def get_categorical_summary(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """
    Thống kê đơn giản cho các cột phân loại/text.
    """
    categorical_df = df.select_dtypes(include=["object", "category", "bool"])

    rows = []

    for col in categorical_df.columns:
        series = categorical_df[col]
        value_counts = series.value_counts(dropna=True).head(top_n)

        top_values = [
            f"{idx}: {count}"
            for idx, count in value_counts.items()
        ]

        rows.append(
            {
                "column_name": col,
                "non_null_count": int(series.notna().sum()),
                "null_count": int(series.isna().sum()),
                "unique_count": int(series.nunique(dropna=True)),
                "top_values": "; ".join(top_values),
            }
        )

    return pd.DataFrame(rows)