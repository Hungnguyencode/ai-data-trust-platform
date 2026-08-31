from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def _severity_from_missing_rate(rate: float) -> str:
    if rate >= 20:
        return "High"
    if rate >= 5:
        return "Medium"
    return "Low"


def check_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Kiểm tra missing value theo từng cột.

    Trả về:
    - issues: danh sách lỗi missing
    - summary_df: bảng thống kê missing theo cột
    """

    issues: List[Dict[str, Any]] = []

    summary_df = pd.DataFrame(
        {
            "column_name": df.columns,
            "missing_count": df.isna().sum().values,
            "missing_rate (%)": (df.isna().mean().values * 100).round(2),
        }
    ).sort_values(
        by="missing_rate (%)",
        ascending=False,
    ).reset_index(drop=True)

    for _, row in summary_df.iterrows():
        missing_count = int(row["missing_count"])
        missing_rate = float(row["missing_rate (%)"])

        if missing_count <= 0:
            continue

        severity = _severity_from_missing_rate(missing_rate)

        issues.append(
            {
                "issue_type": "Missing Value",
                "column_name": row["column_name"],
                "severity": severity,
                "issue_count": missing_count,
                "issue_rate (%)": missing_rate,
                "description": (
                    f"Cột '{row['column_name']}' có {missing_count} giá trị thiếu, "
                    f"chiếm {missing_rate}% tổng số dòng."
                ),
                "recommendation": (
                    "Kiểm tra nguyên nhân thiếu dữ liệu. Có thể loại bỏ dòng, "
                    "điền giá trị thay thế bằng mean/median/mode hoặc đánh dấu Unknown "
                    "tùy theo ý nghĩa nghiệp vụ của cột."
                ),
            }
        )

    return {
        "issues": issues,
        "summary_df": summary_df,
    }
