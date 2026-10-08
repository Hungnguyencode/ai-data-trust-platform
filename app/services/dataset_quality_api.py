from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

DATASET_QUALITY_URL = (
    f"{API_BASE_URL}/api/datasets/quality"
)

class DatasetQualityApiError(RuntimeError):
    """Raised when the Dataset Quality API cannot be used."""


def load_dataset_quality(
    df: pd.DataFrame,
    *,
    file_name: str = "uploaded_dataset.csv",
    file_type: str = "CSV",
) -> dict[str, Any]:
    records = (
        df.astype(object)
        .where(
            pd.notnull(df),
            None,
        )
        .to_dict(
            orient="records",
        )
    )

    try:
        response = requests.post(
            DATASET_QUALITY_URL,
            json={
                "file_name": file_name,
                "file_type": file_type,
                "records": records,
            },
            timeout=15,
        )
        response.raise_for_status()

    except requests.RequestException as exc:
        raise DatasetQualityApiError(
            "Unable to load Dataset Quality."
        ) from exc

    payload = response.json()

    result = dict(payload)

    result["issues_df"] = pd.DataFrame(
        payload["issue_records"]
    )
    result["missing_summary"] = pd.DataFrame(
        payload["missing_records"]
    )
    result["duplicate_rows_df"] = pd.DataFrame(
        payload["duplicate_row_records"]
    )
    result["type_issues_df"] = pd.DataFrame(
        payload["type_issue_records"]
    )
    result["range_issues_df"] = pd.DataFrame(
        payload["range_issue_records"]
    )
    result["categorical_issues_df"] = pd.DataFrame(
        payload["categorical_issue_records"]
    )

    return result