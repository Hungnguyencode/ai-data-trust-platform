from __future__ import annotations

import os

import pandas as pd
import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

PRIVACY_SCAN_URL = (
    f"{API_BASE_URL}/api/privacy/scan"
)


class PrivacyApiError(RuntimeError):
    pass


def run_privacy_scan(
    dataframe: pd.DataFrame,
) -> dict:
    try:
        response = requests.post(
            PRIVACY_SCAN_URL,
            json={
                "records": dataframe.to_dict(
                    orient="records"
                ),
            },
            timeout=60,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise PrivacyApiError(
            "Unable to run privacy scan."
        ) from exc

    payload = response.json()

    return {
        "summary": payload["summary"],
        "findings_df": pd.DataFrame(
            payload["findings_records"]
        ),
    }