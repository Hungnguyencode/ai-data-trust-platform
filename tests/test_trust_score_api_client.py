import pandas as pd
import pytest
import requests

from app.services import trust_score_api


def test_load_trust_score_posts_dataset_and_reconstructs_breakdown(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "file_name": "customers.csv",
                "total_rows": 2,
                "total_columns": 1,
                "overall_score": 91.5,
                "risk_level": "Low",
                "ai_readiness": "Ready",
                "conclusion": "Dataset is trustworthy.",
                "components": [
                    {
                        "score_name": "completeness_score",
                        "score": 100.0,
                        "weight": 0.25,
                        "weighted_score": 25.0,
                        "raw_value": 100.0,
                        "detail": "No missing values.",
                        "interpretation": "Higher is better.",
                    }
                ],
                "anomaly_summary": {
                    "total_rows": 2,
                    "total_anomaly_rows": 0,
                    "anomaly_rate (%)": 0.0,
                    "anomaly_score": 100.0,
                    "risk_level": "Low",
                },
                "anomaly_summary_records": [],
                "anomaly_outlier_records": [],
            }

    def fake_post(url, *, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        trust_score_api.requests,
        "post",
        fake_post,
    )

    df = pd.DataFrame(
        {
            "age": [25, None],
        }
    )

    result = trust_score_api.load_trust_score(
        df,
        file_name="customers.csv",
        file_type="CSV",
    )

    assert captured["url"] == trust_score_api.TRUST_SCORE_URL
    assert captured["json"] == {
        "file_name": "customers.csv",
        "file_type": "CSV",
        "records": [
            {"age": 25.0},
            {"age": None},
        ],
    }
    assert captured["timeout"] == 15

    assert result["overall_score"] == 91.5
    assert result["conclusion"] == "Dataset is trustworthy."

    breakdown_df = result["breakdown_df"]

    assert breakdown_df.loc[0, "score_name"] == "completeness_score"
    assert breakdown_df.loc[0, "raw_value (%)"] == 100.0
    assert breakdown_df.loc[0, "interpretation"] == "Higher is better."
    assert (
        result["score_items"]["completeness_score"]["score"]
        == 100.0
    )


def test_load_trust_score_reconstructs_anomaly_report(
    monkeypatch,
):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "file_name": "customers.csv",
                "total_rows": 2,
                "total_columns": 1,
                "overall_score": 80.0,
                "risk_level": "Medium",
                "ai_readiness": "Review",
                "conclusion": "Review anomalies.",
                "components": [],
                "anomaly_summary": {
                    "total_rows": 2,
                    "total_anomaly_rows": 1,
                    "anomaly_rate (%)": 50.0,
                    "anomaly_score": 50.0,
                    "risk_level": "High",
                },
                "anomaly_summary_records": [
                    {
                        "method": "IQR",
                        "total_outlier_rows": 1,
                        "outlier_rate (%)": 50.0,
                    }
                ],
                "anomaly_outlier_records": [
                    {
                        "age": 99,
                    }
                ],
            }

    monkeypatch.setattr(
        trust_score_api.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(),
    )

    result = trust_score_api.load_trust_score(
        pd.DataFrame(
            {
                "age": [25, 99],
            }
        ),
        file_name="customers.csv",
        file_type="CSV",
    )

    anomaly_report = result["anomaly_report"]

    assert anomaly_report["summary"] == {
        "total_rows": 2,
        "total_anomaly_rows": 1,
        "anomaly_rate (%)": 50.0,
        "anomaly_score": 50.0,
        "risk_level": "High",
    }

    assert (
        anomaly_report["summary_df"]
        .to_dict(orient="records")
        == [
            {
                "method": "IQR",
                "total_outlier_rows": 1,
                "outlier_rate (%)": 50.0,
            }
        ]
    )

    assert (
        anomaly_report["combined_outlier_rows_df"]
        .to_dict(orient="records")
        == [
            {
                "age": 99,
            }
        ]
    )

    assert (
        result["outlier_details_df"]
        .to_dict(orient="records")
        == anomaly_report["summary_df"].to_dict(
            orient="records"
        )
    )


def test_load_trust_score_wraps_request_error(
    monkeypatch,
):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError(
            "API unavailable"
        )

    monkeypatch.setattr(
        trust_score_api.requests,
        "post",
        fake_post,
    )

    with pytest.raises(
        trust_score_api.TrustScoreApiError,
        match="Unable to load Trust Score",
    ):
        trust_score_api.load_trust_score(
            pd.DataFrame(
                {
                    "age": [25, 30],
                }
            ),
            file_name="customers.csv",
            file_type="CSV",
        )