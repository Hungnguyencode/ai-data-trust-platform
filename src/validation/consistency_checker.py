from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


NON_NEGATIVE_KEYWORDS = [
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

AGE_KEYWORDS = ["age", "tuoi"]

BINARY_LABEL_KEYWORDS = [
    "churn",
    "label",
    "target",
    "fraud",
    "is_fraud",
    "default",
]

COMMON_BINARY_VALUES = {
    "0",
    "1",
    0,
    1,
    "yes",
    "no",
    "true",
    "false",
    "y",
    "n",
    "Yes",
    "No",
    "True",
    "False",
    "Y",
    "N",
}


def _contains_keyword(column_name: str, keywords: List[str]) -> bool:
    lower_name = column_name.lower()
    return any(keyword in lower_name for keyword in keywords)


def _severity_from_rate(rate: float) -> str:
    if rate >= 20:
        return "High"
    if rate >= 5:
        return "Medium"
    return "Low"


def check_range_issues(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Kiểm tra lỗi miền giá trị cơ bản.

    Bao gồm:
    - Cột numeric không nên âm: age, price, quantity, amount, income...
    - Age không nên lớn hơn 120
    """
    issues: List[Dict[str, Any]] = []
    details: List[Dict[str, Any]] = []
    total_rows = len(df)

    for col in df.columns:
        if not _contains_keyword(col, NON_NEGATIVE_KEYWORDS):
            continue

        numeric_series = pd.to_numeric(df[col], errors="coerce")

        # Bỏ qua cột không ép được numeric
        if numeric_series.notna().sum() == 0:
            continue

        negative_mask = numeric_series < 0
        negative_count = int(negative_mask.sum())
        negative_rate = round(negative_count / max(total_rows, 1) * 100, 2)

        details.append(
            {
                "column_name": col,
                "rule": "value >= 0",
                "invalid_count": negative_count,
                "invalid_rate (%)": negative_rate,
            }
        )

        if negative_count > 0:
            severity = _severity_from_rate(negative_rate)

            issues.append(
                {
                    "issue_type": "Invalid Range",
                    "column_name": col,
                    "severity": severity,
                    "issue_count": negative_count,
                    "issue_rate (%)": negative_rate,
                    "description": (
                        f"Cột '{col}' có {negative_count} giá trị âm, "
                        "không phù hợp với miền giá trị kỳ vọng."
                    ),
                    "recommendation": (
                        "Kiểm tra lại nguồn dữ liệu. Có thể sửa giá trị, loại bỏ dòng lỗi "
                        "hoặc chuyển giá trị bất hợp lệ thành missing value."
                    ),
                }
            )

        # Rule riêng cho tuổi
        if _contains_keyword(col, AGE_KEYWORDS):
            age_invalid_mask = numeric_series > 120
            age_invalid_count = int(age_invalid_mask.sum())
            age_invalid_rate = round(age_invalid_count / max(total_rows, 1) * 100, 2)

            details.append(
                {
                    "column_name": col,
                    "rule": "age <= 120",
                    "invalid_count": age_invalid_count,
                    "invalid_rate (%)": age_invalid_rate,
                }
            )

            if age_invalid_count > 0:
                severity = _severity_from_rate(age_invalid_rate)

                issues.append(
                    {
                        "issue_type": "Invalid Age Range",
                        "column_name": col,
                        "severity": severity,
                        "issue_count": age_invalid_count,
                        "issue_rate (%)": age_invalid_rate,
                        "description": (
                            f"Cột '{col}' có {age_invalid_count} giá trị tuổi lớn hơn 120."
                        ),
                        "recommendation": (
                            "Kiểm tra lại dữ liệu tuổi. Những giá trị này có thể là lỗi nhập liệu."
                        ),
                    }
                )

    return {
        "issues": issues,
        "details_df": pd.DataFrame(details),
    }


def check_categorical_value_issues(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Kiểm tra lỗi categorical đơn giản.

    Hiện tại kiểm tra:
    - Các cột label/churn/fraud/target nên là nhị phân.
    - Các cột object có khoảng trắng dư ở đầu/cuối.
    """
    issues: List[Dict[str, Any]] = []
    details: List[Dict[str, Any]] = []
    total_rows = len(df)

    for col in df.columns:
        series = df[col]

        # Check binary label columns
        if _contains_keyword(col, BINARY_LABEL_KEYWORDS):
            non_null_values = series.dropna()
            invalid_mask = ~non_null_values.isin(COMMON_BINARY_VALUES)
            invalid_count = int(invalid_mask.sum())
            invalid_rate = round(invalid_count / max(len(non_null_values), 1) * 100, 2)

            details.append(
                {
                    "column_name": col,
                    "rule": "binary label values",
                    "invalid_count": invalid_count,
                    "invalid_rate (%)": invalid_rate,
                }
            )

            if invalid_count > 0:
                severity = _severity_from_rate(invalid_rate)

                issues.append(
                    {
                        "issue_type": "Invalid Categorical Value",
                        "column_name": col,
                        "severity": severity,
                        "issue_count": invalid_count,
                        "issue_rate (%)": invalid_rate,
                        "description": (
                            f"Cột '{col}' được kỳ vọng là nhãn nhị phân nhưng có "
                            f"{invalid_count} giá trị nằm ngoài tập giá trị hợp lệ."
                        ),
                        "recommendation": (
                            "Chuẩn hóa nhãn về dạng 0/1, Yes/No hoặc True/False. "
                            "Kiểm tra các giá trị bất thường trong cột nhãn."
                        ),
                    }
                )

        # Check leading/trailing spaces in text columns
        if pd.api.types.is_object_dtype(series):
            non_null_series = series.dropna().astype(str)
            space_mask = non_null_series != non_null_series.str.strip()
            space_count = int(space_mask.sum())
            space_rate = round(space_count / max(len(non_null_series), 1) * 100, 2)

            details.append(
                {
                    "column_name": col,
                    "rule": "no leading/trailing spaces",
                    "invalid_count": space_count,
                    "invalid_rate (%)": space_rate,
                }
            )

            if space_count > 0:
                severity = _severity_from_rate(space_rate)

                issues.append(
                    {
                        "issue_type": "Text Format Inconsistency",
                        "column_name": col,
                        "severity": severity,
                        "issue_count": space_count,
                        "issue_rate (%)": space_rate,
                        "description": (
                            f"Cột '{col}' có {space_count} giá trị chứa khoảng trắng dư "
                            "ở đầu hoặc cuối chuỗi."
                        ),
                        "recommendation": (
                            "Chuẩn hóa chuỗi bằng cách trim khoảng trắng trước khi phân tích."
                        ),
                    }
                )

    return {
        "issues": issues,
        "details_df": pd.DataFrame(details),
    }