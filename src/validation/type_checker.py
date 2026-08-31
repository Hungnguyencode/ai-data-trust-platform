from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

NUMERIC_KEYWORDS = [
    "age",
    "amount",
    "price",
    "quantity",
    "qty",
    "income",
    "salary",
    "total",
    "spent",
    "score",
    "revenue",
    "cost",
    "profit",
    "balance",
]

DATETIME_KEYWORDS = [
    "date",
    "time",
    "timestamp",
    "created_at",
    "updated_at",
    "invoice_date",
    "transaction_time",
]


def _column_name_contains(column_name: str, keywords: List[str]) -> bool:
    lower_name = column_name.lower()
    return any(keyword in lower_name for keyword in keywords)


def _severity_from_rate(rate: float) -> str:
    if rate >= 20:
        return "High"
    if rate >= 5:
        return "Medium"
    return "Low"


def check_type_issues(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Kiểm tra lỗi kiểu dữ liệu dựa trên tên cột và khả năng ép kiểu.

    Ví dụ:
    - age, price, quantity, amount nên là numeric
    - date, time, timestamp nên là datetime
    """
    issues: List[Dict[str, Any]] = []
    details: List[Dict[str, Any]] = []


    for col in df.columns:
        series = df[col]
        non_null_series = series.dropna()

        if non_null_series.empty:
            continue

        # Kiểm tra cột nên là numeric
        if _column_name_contains(col, NUMERIC_KEYWORDS):
            converted = pd.to_numeric(non_null_series, errors="coerce")
            invalid_mask = converted.isna()
            invalid_count = int(invalid_mask.sum())
            checked_count = len(non_null_series)
            invalid_rate = round(invalid_count / max(checked_count, 1) * 100, 2)

            details.append(
                {
                    "column_name": col,
                    "expected_type": "numeric",
                    "checked_values": checked_count,
                    "invalid_count": invalid_count,
                    "invalid_rate (%)": invalid_rate,
                }
            )

            if invalid_count > 0:
                severity = _severity_from_rate(invalid_rate)

                issues.append(
                    {
                        "issue_type": "Invalid Numeric Type",
                        "column_name": col,
                        "severity": severity,
                        "issue_count": invalid_count,
                        "issue_rate (%)": invalid_rate,
                        "description": (
                            f"Cột '{col}' được kỳ vọng là numeric nhưng có "
                            f"{invalid_count} giá trị không thể chuyển thành số."
                        ),
                        "recommendation": (
                            "Kiểm tra các giá trị sai kiểu. Có thể sửa định dạng, "
                            "chuyển đổi kiểu dữ liệu hoặc đưa các giá trị lỗi thành missing value."
                        ),
                    }
                )

        # Kiểm tra cột nên là datetime
        if _column_name_contains(col, DATETIME_KEYWORDS):
            converted = pd.to_datetime(non_null_series, errors="coerce")
            invalid_mask = converted.isna()
            invalid_count = int(invalid_mask.sum())
            checked_count = len(non_null_series)
            invalid_rate = round(invalid_count / max(checked_count, 1) * 100, 2)

            details.append(
                {
                    "column_name": col,
                    "expected_type": "datetime",
                    "checked_values": checked_count,
                    "invalid_count": invalid_count,
                    "invalid_rate (%)": invalid_rate,
                }
            )

            if invalid_count > 0:
                severity = _severity_from_rate(invalid_rate)

                issues.append(
                    {
                        "issue_type": "Invalid Datetime Type",
                        "column_name": col,
                        "severity": severity,
                        "issue_count": invalid_count,
                        "issue_rate (%)": invalid_rate,
                        "description": (
                            f"Cột '{col}' được kỳ vọng là datetime nhưng có "
                            f"{invalid_count} giá trị không thể chuyển thành ngày tháng."
                        ),
                        "recommendation": (
                            "Chuẩn hóa định dạng ngày tháng, ví dụ YYYY-MM-DD hoặc "
                            "YYYY-MM-DD HH:MM:SS, trước khi đưa vào pipeline."
                        ),
                    }
                )

    details_df = pd.DataFrame(details)

    return {
        "issues": issues,
        "details_df": details_df,
    }