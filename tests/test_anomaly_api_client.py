import pandas as pd
import requests

from app.services import anomaly_api


def test_run_anomaly_detection_reconstructs_dataframes(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "summary": {
                    "total_rows": 4,
                    "total_anomaly_rows": 1,
                    "anomaly_rate (%)": 25.0,
                    "anomaly_score": 50.0,
                    "risk_level": "High",
                },
                "summary_records": [
                    {
                        "method": "IQR",
                        "total_outlier_rows": 1,
                        "outlier_rate (%)": 25.0,
                    }
                ],
                "combined_outlier_records": [
                    {
                        "value": 100.0,
                    }
                ],
                "iqr_result": {
                    "method": "IQR",
                    "summary_records": [
                        {
                            "column_name": "value",
                            "outlier_count": 1,
                        }
                    ],
                    "outlier_records": [
                        {
                            "value": 100.0,
                        }
                    ],
                    "outlier_row_indexes": [3],
                    "score_records": [],
                    "total_outlier_rows": 1,
                    "outlier_rate (%)": 25.0,
                },
                "zscore_result": {
                    "method": "Z-score",
                    "summary_records": [],
                    "outlier_records": [],
                    "outlier_row_indexes": [],
                    "score_records": [],
                    "total_outlier_rows": 0,
                    "outlier_rate (%)": 0.0,
                },
                "isolation_forest_result": {
                    "method": "Isolation Forest",
                    "summary": {
                        "used": False,
                        "reason": "Dataset too small.",
                        "contamination": 0.1,
                        "total_outlier_rows": 0,
                        "outlier_rate (%)": 0.0,
                    },
                    "outlier_records": [],
                    "outlier_row_indexes": [],
                    "score_records": [],
                },
            }

    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        anomaly_api.requests,
        "post",
        fake_post,
    )

    dataframe = pd.DataFrame(
        {
            "value": [
                1.0,
                2.0,
                3.0,
                100.0,
            ]
        }
    )

    result = anomaly_api.run_anomaly_detection(
        dataframe,
        zscore_threshold=3.0,
        isolation_contamination=0.1,
    )

    assert captured["url"].endswith(
        "/api/anomaly/analyze"
    )

    assert captured["json"] == {
        "records": [
            {"value": 1.0},
            {"value": 2.0},
            {"value": 3.0},
            {"value": 100.0},
        ],
        "zscore_threshold": 3.0,
        "isolation_contamination": 0.1,
    }

    assert isinstance(
        result["summary_df"],
        pd.DataFrame,
    )

    assert isinstance(
        result["combined_outlier_rows_df"],
        pd.DataFrame,
    )

    assert isinstance(
        result["iqr_result"]["summary_df"],
        pd.DataFrame,
    )

    assert isinstance(
        result[
            "isolation_forest_result"
        ]["scores_df"],
        pd.DataFrame,
    )

    assert (
        result["iqr_result"][
            "outlier_row_indexes"
        ]
        == {3}
    )


def test_run_anomaly_detection_wraps_request_error(
    monkeypatch,
):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError(
            "API unavailable"
        )

    monkeypatch.setattr(
        anomaly_api.requests,
        "post",
        fake_post,
    )

    dataframe = pd.DataFrame(
        {
            "value": [1.0, 2.0, 3.0],
        }
    )

    try:
        anomaly_api.run_anomaly_detection(
            dataframe
        )
    except anomaly_api.AnomalyApiError as exc:
        assert str(exc) == (
            "Unable to run anomaly detection."
        )
    else:
        raise AssertionError(
            "Expected AnomalyApiError"
        )