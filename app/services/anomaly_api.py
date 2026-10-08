from __future__ import annotations

import os

import pandas as pd
import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

ANOMALY_ANALYSIS_URL = (
    f"{API_BASE_URL}/api/anomaly/analyze"
)


class AnomalyApiError(RuntimeError):
    pass


def _deserialize_detector_result(
    payload: dict,
) -> dict:
    result = dict(payload)

    result.pop(
        "summary_records",
        None,
    )
    result.pop(
        "outlier_records",
        None,
    )
    result.pop(
        "score_records",
        None,
    )

    result["summary_df"] = pd.DataFrame(
        payload.get(
            "summary_records",
            [],
        )
    )

    result["outlier_rows_df"] = (
        pd.DataFrame(
            payload.get(
                "outlier_records",
                [],
            )
        )
    )

    result["scores_df"] = pd.DataFrame(
        payload.get(
            "score_records",
            [],
        )
    )

    result["outlier_row_indexes"] = set(
        payload.get(
            "outlier_row_indexes",
            [],
        )
    )

    return result


def run_anomaly_detection(
    dataframe: pd.DataFrame,
    *,
    zscore_threshold: float = 3.0,
    isolation_contamination: float = 0.1,
) -> dict:
    try:
        response = requests.post(
            ANOMALY_ANALYSIS_URL,
            json={
                "records": dataframe.to_dict(
                    orient="records"
                ),
                "zscore_threshold": (
                    zscore_threshold
                ),
                "isolation_contamination": (
                    isolation_contamination
                ),
            },
            timeout=60,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise AnomalyApiError(
            "Unable to run anomaly detection."
        ) from exc

    payload = response.json()

    return {
        "summary": payload["summary"],
        "summary_df": pd.DataFrame(
            payload["summary_records"]
        ),
        "combined_outlier_rows_df": (
            pd.DataFrame(
                payload[
                    "combined_outlier_records"
                ]
            )
        ),
        "iqr_result": (
            _deserialize_detector_result(
                payload["iqr_result"]
            )
        ),
        "zscore_result": (
            _deserialize_detector_result(
                payload["zscore_result"]
            )
        ),
        "isolation_forest_result": (
            _deserialize_detector_result(
                payload[
                    "isolation_forest_result"
                ]
            )
        ),
    }