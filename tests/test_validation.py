import pandas as pd

from src.validation.consistency_checker import (
    check_categorical_value_issues,
    check_range_issues,
)
from src.validation.duplicate_checker import check_duplicate_rows
from src.validation.missing_checker import check_missing_values
from src.validation.rule_engine import run_quality_checks
from src.validation.type_checker import check_type_issues


def test_missing_checker_detects_missing_values():
    df = pd.DataFrame(
        {
            "nickname": [
                "A",
                "B",
                "C",
                "D",
                "E",
                "F",
                "G",
                "H",
                None,
                None,
            ]
        }
    )

    result = check_missing_values(df)

    assert len(result["issues"]) == 1

    issue = result["issues"][0]

    assert issue["issue_type"] == "Missing Value"
    assert issue["column_name"] == "nickname"
    assert issue["issue_count"] == 2
    assert issue["issue_rate (%)"] == 20.0
    assert issue["severity"] == "High"

    summary = result["summary_df"].iloc[0]

    assert summary["missing_count"] == 2
    assert summary["missing_rate (%)"] == 20.0


def test_duplicate_checker_detects_full_row_duplicates():
    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 2, 3, 4],
            "name": ["A", "B", "B", "C", "D"],
        }
    )

    result = check_duplicate_rows(df)

    assert result["duplicate_count"] == 1
    assert result["duplicate_rate"] == 20.0

    # keep=False trả về cả hai dòng thuộc nhóm duplicate.
    assert len(result["duplicate_rows_df"]) == 2

    assert len(result["issues"]) == 1

    issue = result["issues"][0]

    assert issue["issue_type"] == "Duplicate Rows"
    assert issue["column_name"] == "__row__"
    assert issue["issue_count"] == 1
    assert issue["severity"] == "High"


def test_type_checker_detects_invalid_numeric_value():
    df = pd.DataFrame(
        {
            "age": [
                "20",
                "30",
                "not-a-number",
                "40",
                None,
            ]
        }
    )

    result = check_type_issues(df)

    assert len(result["issues"]) == 1

    issue = result["issues"][0]

    assert issue["issue_type"] == "Invalid Numeric Type"
    assert issue["column_name"] == "age"
    assert issue["issue_count"] == 1
    assert issue["issue_rate (%)"] == 25.0
    assert issue["severity"] == "High"

    details = result["details_df"]

    age_detail = details[
        details["column_name"] == "age"
    ].iloc[0]

    assert age_detail["expected_type"] == "numeric"
    assert age_detail["checked_values"] == 4
    assert age_detail["invalid_count"] == 1
    assert age_detail["invalid_rate (%)"] == 25.0


def test_range_checker_detects_negative_and_invalid_age():
    df = pd.DataFrame(
        {
            "age": [
                20,
                -1,
                130,
                40,
            ]
        }
    )

    result = check_range_issues(df)

    issues = {
        issue["issue_type"]: issue
        for issue in result["issues"]
    }

    assert "Invalid Range" in issues
    assert "Invalid Age Range" in issues

    negative_issue = issues["Invalid Range"]

    assert negative_issue["column_name"] == "age"
    assert negative_issue["issue_count"] == 1
    assert negative_issue["issue_rate (%)"] == 25.0
    assert negative_issue["severity"] == "High"

    age_issue = issues["Invalid Age Range"]

    assert age_issue["column_name"] == "age"
    assert age_issue["issue_count"] == 1
    assert age_issue["issue_rate (%)"] == 25.0
    assert age_issue["severity"] == "High"

    rules = set(result["details_df"]["rule"])

    assert "value >= 0" in rules
    assert "age <= 120" in rules


def test_categorical_checker_detects_invalid_binary_label():
    df = pd.DataFrame(
        {
            "churn": [
                0,
                1,
                "yes",
                "maybe",
                None,
            ]
        }
    )

    result = check_categorical_value_issues(df)

    categorical_issues = [
        issue
        for issue in result["issues"]
        if issue["issue_type"] == "Invalid Categorical Value"
    ]

    assert len(categorical_issues) == 1

    issue = categorical_issues[0]

    assert issue["column_name"] == "churn"
    assert issue["issue_count"] == 1
    assert issue["issue_rate (%)"] == 25.0
    assert issue["severity"] == "High"


def test_categorical_checker_detects_text_whitespace():
    df = pd.DataFrame(
        {
            "name": [
                "Alice",
                " Bob",
                "Charlie ",
                "Dana",
            ]
        }
    )

    result = check_categorical_value_issues(df)

    text_issues = [
        issue
        for issue in result["issues"]
        if issue["issue_type"] == "Text Format Inconsistency"
    ]

    assert len(text_issues) == 1

    issue = text_issues[0]

    assert issue["column_name"] == "name"
    assert issue["issue_count"] == 2
    assert issue["issue_rate (%)"] == 50.0
    assert issue["severity"] == "High"


def test_quality_engine_returns_expected_contract_and_summary():
    df = pd.DataFrame(
        {
            "nickname": [
                "Alice",
                "Bob",
                "Charlie",
                None,
            ]
        }
    )

    result = run_quality_checks(df)

    assert set(result.keys()) == {
        "summary",
        "issues",
        "issues_df",
        "missing_summary",
        "duplicate_rows_df",
        "type_issues_df",
        "range_issues_df",
        "categorical_issues_df",
    }

    summary = result["summary"]

    assert summary["total_issues"] == 1
    assert summary["high_issues"] == 1
    assert summary["medium_issues"] == 0
    assert summary["low_issues"] == 0
    assert summary["affected_columns"] == 1
    assert summary["total_columns"] == 1

    assert len(result["issues"]) == 1
    assert result["issues_df"].iloc[0]["issue_type"] == "Missing Value"