from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def _severity_from_duplicate_rate(rate: float) -> str:
    if rate >= 10:
        return "High"
    if rate >= 3:
        return "Medium"
    return "Low"


def check_duplicate_rows(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Kiểm tra các dòng trùng lặp toàn bộ giá trị.

    Lưu ý:
    Hai dòng chỉ được xem là duplicate nếu tất cả các cột giống nhau.
    """
    total_rows = len(df)
    duplicate_mask = df.duplicated(keep=False)
    duplicate_rows_df = df[duplicate_mask].copy()

    duplicate_count = int(df.duplicated().sum())
    duplicate_rate = round(duplicate_count / max(total_rows, 1) * 100, 2)

    issues: List[Dict[str, Any]] = []

    if duplicate_count > 0:
        severity = _severity_from_duplicate_rate(duplicate_rate)

        issues.append(
            {
                "issue_type": "Duplicate Rows",
                "column_name": "__row__",
                "severity": severity,
                "issue_count": duplicate_count,
                "issue_rate (%)": duplicate_rate,
                "description": (
                    f"Dataset có {duplicate_count} dòng bị trùng lặp hoàn toàn, "
                    f"chiếm {duplicate_rate}% tổng số dòng."
                ),
                "recommendation": (
                    "Kiểm tra các dòng trùng lặp. Nếu không có ý nghĩa nghiệp vụ đặc biệt, "
                    "nên loại bỏ duplicate rows trước khi phân tích hoặc huấn luyện mô hình."
                ),
            }
        )

    return {
        "issues": issues,
        "duplicate_rows_df": duplicate_rows_df,
        "duplicate_count": duplicate_count,
        "duplicate_rate": duplicate_rate,
    }