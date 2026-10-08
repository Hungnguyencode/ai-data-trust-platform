from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

SCANS_URL = f"{API_BASE_URL}/api/scans"
FULL_SCAN_URL = f"{SCANS_URL}/full"
SCAN_HISTORY_URL = f"{SCANS_URL}/history"


class ScanApiError(RuntimeError):
    """Raised when the Scan API cannot be used."""


def save_full_scan(
    df: pd.DataFrame,
    *,
    file_name: str,
    file_type: str,
) -> dict[str, Any]:
    records = (
        df.astype(object)
        .where(pd.notnull(df), None)
        .to_dict(orient="records")
    )

    try:
        response = requests.post(
            FULL_SCAN_URL,
            json={
                "file_name": file_name,
                "file_type": file_type,
                "records": records,
            },
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScanApiError(
            "Unable to save full scan."
        ) from exc

    return response.json()


def load_scan_history(
    *,
    limit: int = 50,
) -> pd.DataFrame:
    try:
        response = requests.get(
            SCAN_HISTORY_URL,
            params={
                "limit": limit,
            },
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScanApiError(
            "Unable to load scan history."
        ) from exc

    payload = response.json()

    return pd.DataFrame(
        payload["items"]
    )


def load_scan_detail(
    scan_id: int,
) -> dict[str, Any]:
    try:
        response = requests.get(
            f"{SCANS_URL}/{scan_id}",
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScanApiError(
            "Unable to load scan detail."
        ) from exc

    payload = response.json()

    result = dict(payload)
    result["issues_df"] = pd.DataFrame(
        payload["quality_issues"]
    )

    return result