from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

HTML_REPORT_URL = (
    f"{API_BASE_URL}/api/reports/html"
)

SAVE_HTML_REPORT_URL = (
    f"{API_BASE_URL}/api/reports/html/save"
)


class ReportApiError(RuntimeError):
    pass


def generate_html_report(
    df: pd.DataFrame,
    *,
    file_name: str,
    file_type: str,
    profile: dict[str, Any] | None = None,
    quality_report: dict[str, Any] | None = None,
    trust_score_report: dict[str, Any] | None = None,
    privacy_report: dict[str, Any] | None = None,
    drift_report: dict[str, Any] | None = None,
) -> dict:
    payload: dict[str, Any] = {
        "file_name": file_name,
        "file_type": file_type,
        "total_rows": int(df.shape[0]),
        "total_columns": int(df.shape[1]),
    }

    if profile is not None:
        payload["profile"] = {
            "basic_info": dict(
                profile.get(
                    "basic_info",
                    {},
                )
            ),
        }

    if quality_report is not None:
        issues_df = quality_report.get(
            "issues_df",
            pd.DataFrame(),
        )

        payload["quality"] = {
            "summary": dict(
                quality_report.get(
                    "summary",
                    {},
                )
            ),
            "issue_records": (
                issues_df.to_dict(
                    orient="records"
                )
            ),
        }

    if trust_score_report is not None:
        breakdown_df = trust_score_report.get(
            "breakdown_df",
            pd.DataFrame(),
        )

        payload["trust_score"] = {
            "overall_score": (
                trust_score_report.get(
                    "overall_score"
                )
            ),
            "risk_level": (
                trust_score_report.get(
                    "risk_level"
                )
            ),
            "ai_readiness": (
                trust_score_report.get(
                    "ai_readiness"
                )
            ),
            "conclusion": (
                trust_score_report.get(
                    "conclusion"
                )
            ),
            "breakdown_records": (
                breakdown_df.to_dict(
                    orient="records"
                )
            ),
        }

    if privacy_report is not None:
        findings_df = privacy_report.get(
            "findings_df",
            pd.DataFrame(),
        )

        payload["privacy"] = {
            "summary": dict(
                privacy_report.get(
                    "summary",
                    {},
                )
            ),
            "finding_records": (
                findings_df.to_dict(
                    orient="records"
                )
            ),
        }

    if drift_report is not None:
        numeric_drift_df = drift_report.get(
            "numeric_drift_df",
            pd.DataFrame(),
        )

        categorical_drift_df = drift_report.get(
            "categorical_drift_df",
            pd.DataFrame(),
        )

        schema_report = drift_report.get(
            "schema_report",
            {},
        )

        schema_changes_df = schema_report.get(
            "changes_df",
            pd.DataFrame(),
        )

        payload["drift"] = {
            "summary": dict(
                drift_report.get(
                    "summary",
                    {},
                )
            ),
            "baseline_file_name": (
                drift_report.get(
                    "baseline_file_name",
                    "baseline dataset",
                )
            ),
            "current_file_name": (
                drift_report.get(
                    "current_file_name",
                    "current dataset",
                )
            ),
            "numeric_drift_records": (
                numeric_drift_df.to_dict(
                    orient="records"
                )
            ),
            "categorical_drift_records": (
                categorical_drift_df.to_dict(
                    orient="records"
                )
            ),
            "schema_change_records": (
                schema_changes_df.to_dict(
                    orient="records"
                )
            ),
        }

    try:
        response = requests.post(
            HTML_REPORT_URL,
            json=payload,
            timeout=15,
        )

        response.raise_for_status()
    except requests.RequestException as exc:
        raise ReportApiError(
            "Unable to generate HTML report."
        ) from exc

    return response.json()


def save_html_report(
    *,
    html_content: str,
    report_file_name: str,
) -> dict:
    try:
        response = requests.post(
            SAVE_HTML_REPORT_URL,
            json={
                "html_content": html_content,
                "report_file_name": (
                    report_file_name
                ),
            },
            timeout=15,
        )

        response.raise_for_status()
    except requests.RequestException as exc:
        raise ReportApiError(
            "Unable to save HTML report."
        ) from exc

    return response.json()