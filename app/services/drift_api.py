from __future__ import annotations

import os

import pandas as pd
import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://localhost:8000",
)

DRIFT_ANALYZE_URL = (
    f"{API_BASE_URL}/api/drift/analyze"
)

CATEGORICAL_DISTRIBUTION_URL = (
    f"{API_BASE_URL}"
    "/api/drift/categorical-distribution"
)


class DriftApiError(RuntimeError):
    pass


def analyze_drift(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
) -> dict:
    try:
        response = requests.post(
            DRIFT_ANALYZE_URL,
            json={
                "baseline_records": (
                    baseline_df.to_dict(
                        orient="records",
                    )
                ),
                "current_records": (
                    current_df.to_dict(
                        orient="records",
                    )
                ),
            },
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DriftApiError(
            "Unable to analyze drift."
        ) from exc

    payload = response.json()

    schema_payload = payload["schema_report"]

    schema_report = {
        "summary": schema_payload["summary"],
        "added_columns": (
            schema_payload["added_columns"]
        ),
        "removed_columns": (
            schema_payload["removed_columns"]
        ),
        "common_columns": (
            schema_payload["common_columns"]
        ),
        "dtype_changes": (
            schema_payload["dtype_changes"]
        ),
        "changes_df": pd.DataFrame(
            schema_payload["change_records"]
        ),
    }

    return {
        "summary": payload["summary"],
        "schema_report": schema_report,
        "numeric_drift_df": pd.DataFrame(
            payload["numeric_drift_records"]
        ),
        "categorical_drift_df": pd.DataFrame(
            payload[
                "categorical_drift_records"
            ]
        ),
        "all_drift_df": pd.DataFrame(
            payload["all_drift_records"]
        ),
    }


def get_categorical_distribution(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    column_name: str,
) -> pd.DataFrame:
    try:
        response = requests.post(
            CATEGORICAL_DISTRIBUTION_URL,
            json={
                "baseline_records": (
                    baseline_df.to_dict(
                        orient="records",
                    )
                ),
                "current_records": (
                    current_df.to_dict(
                        orient="records",
                    )
                ),
                "column_name": column_name,
            },
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DriftApiError(
            "Unable to load categorical drift distribution."
        ) from exc

    payload = response.json()

    return pd.DataFrame(
        payload["distribution_records"]
    )