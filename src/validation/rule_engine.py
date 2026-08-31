from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from src.validation.consistency_checker import (
    check_categorical_value_issues,
    check_range_issues,
)
from src.validation.duplicate_checker import check_duplicate_rows
from src.validation.missing_checker import check_missing_values
from src.validation.type_checker import check_type_issues

Issue = Dict[str, Any]


def build_issue(
    issue_type: str,
    column_name: str,
    severity: str,
    issue_count: int,
    total_rows: int,
    description: str,
    recommendation: str,
) -> Issue:
    """
    Chuẩn hóa format của một lỗi dữ liệu.
    """
    issue_rate = round(issue_count / max(total_rows, 1) * 100, 2)

    return {
        "issue_type": issue_type,
        "column_name": column_name,
        "severity": severity,
        "issue_count": int(issue_count),
        "issue_rate (%)": issue_rate,
        "description": description,
        "recommendation": recommendation,
    }


def severity_from_rate(rate: float) -> str:
    """
    Phân loại mức độ nghiêm trọng theo tỷ lệ lỗi.
    """
    if rate >= 20:
        return "High"
    if rate >= 5:
        return "Medium"
    if rate > 0:
        return "Low"
    return "None"


def summarize_issues(issues: List[Issue], total_columns: int) -> Dict[str, Any]:
    """
    Tạo thống kê tổng quan cho toàn bộ lỗi dữ liệu.
    """
    if not issues:
        return {
            "total_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "affected_columns": 0,
            "total_columns": total_columns,
        }

    issues_df = pd.DataFrame(issues)

    affected_columns = issues_df[
        issues_df["column_name"] != "__row__"
    ]["column_name"].nunique()

    return {
        "total_issues": len(issues),
        "high_issues": int((issues_df["severity"] == "High").sum()),
        "medium_issues": int((issues_df["severity"] == "Medium").sum()),
        "low_issues": int((issues_df["severity"] == "Low").sum()),
        "affected_columns": int(affected_columns),
        "total_columns": total_columns,
    }


def run_quality_checks(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Chạy toàn bộ bộ kiểm tra chất lượng dữ liệu cho Version 0.2.

    Bao gồm:
    - Missing value checker
    - Duplicate checker
    - Type checker
    - Range checker
    - Categorical value checker
    """
    issues: List[Issue] = []

    missing_result = check_missing_values(df)
    duplicate_result = check_duplicate_rows(df)
    type_result = check_type_issues(df)
    range_result = check_range_issues(df)
    categorical_result = check_categorical_value_issues(df)

    issues.extend(missing_result["issues"])
    issues.extend(duplicate_result["issues"])
    issues.extend(type_result["issues"])
    issues.extend(range_result["issues"])
    issues.extend(categorical_result["issues"])

    issues_df = pd.DataFrame(issues)

    if not issues_df.empty:
        severity_order = {"High": 0, "Medium": 1, "Low": 2}
        issues_df["severity_order"] = issues_df["severity"].map(severity_order)
        issues_df = issues_df.sort_values(
            by=["severity_order", "issue_rate (%)", "issue_count"],
            ascending=[True, False, False],
        ).drop(columns=["severity_order"])
        issues_df = issues_df.reset_index(drop=True)

    summary = summarize_issues(issues, total_columns=len(df.columns))

    return {
        "summary": summary,
        "issues": issues,
        "issues_df": issues_df,
        "missing_summary": missing_result["summary_df"],
        "duplicate_rows_df": duplicate_result["duplicate_rows_df"],
        "type_issues_df": type_result["details_df"],
        "range_issues_df": range_result["details_df"],
        "categorical_issues_df": categorical_result["details_df"],
    }