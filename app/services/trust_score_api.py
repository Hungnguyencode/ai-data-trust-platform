from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)
TRUST_SCORE_URL = f"{API_BASE_URL}/api/scores/calculate"


class TrustScoreApiError(RuntimeError):
    """Raised when the Trust Score API cannot be used."""


def load_trust_score(
    df: pd.DataFrame,
    *,
    file_name: str = "uploaded_dataset.csv",
    file_type: str = "CSV",
) -> dict[str, Any]:
    records = (
        df.astype(object)
        .where(pd.notnull(df), None)
        .to_dict(orient="records")
    )

    try:
        response = requests.post(
            TRUST_SCORE_URL,
            json={
                "file_name": file_name,
                "file_type": file_type,
                "records": records,
            },
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise TrustScoreApiError(
            "Unable to load Trust Score."
        ) from exc

    payload = response.json()

    breakdown_records = []

    for component in payload["components"]:
        row = dict(component)
        row["raw_value (%)"] = row.pop(
            "raw_value"
        )
        breakdown_records.append(row)

    score_items = {
        component["score_name"]: dict(component)
        for component in payload["components"]
    }

    result = dict(payload)

    result["breakdown_df"] = pd.DataFrame(
        breakdown_records
    )

    result["score_items"] = score_items

    anomaly_summary_df = pd.DataFrame(
        payload["anomaly_summary_records"]
    )

    anomaly_outlier_rows_df = pd.DataFrame(
        payload["anomaly_outlier_records"]
    )

    result["anomaly_report"] = {
        "summary": dict(
            payload["anomaly_summary"]
        ),
        "summary_df": anomaly_summary_df,
        "combined_outlier_rows_df": (
            anomaly_outlier_rows_df
        ),
    }

    result["outlier_details_df"] = anomaly_summary_df

    return result