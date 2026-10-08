from __future__ import annotations

import pandas as pd
import pytest
import requests

from app.services import drift_api


def test_analyze_drift_posts_records_and_reconstructs_report(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "summary": {
                    "baseline_rows": 2,
                    "current_rows": 2,
                    "overall_drift_level": "Low",
                },
                "schema_report": {
                    "summary": {
                        "baseline_columns": 2,
                        "current_columns": 2,
                    },
                    "added_columns": [],
                    "removed_columns": [],
                    "common_columns": [
                        "age",
                        "country",
                    ],
                    "dtype_changes": [],
                    "change_records": [
                        {
                            "change_type": "Added Column",
                            "column_name": "segment",
                        }
                    ],
                },
                "numeric_drift_records": [
                    {
                        "column_name": "age",
                        "psi": 0.12,
                    }
                ],
                "categorical_drift_records": [
                    {
                        "column_name": "country",
                        "drift_level": "Low",
                    }
                ],
                "all_drift_records": [
                    {
                        "column_name": "age",
                        "drift_type": "numeric",
                        "drift_level": "Low",
                    }
                ],
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
        drift_api.requests,
        "post",
        fake_post,
    )

    baseline_df = pd.DataFrame(
        [
            {
                "age": 20,
                "country": "VN",
            },
            {
                "age": 30,
                "country": "US",
            },
        ]
    )

    current_df = pd.DataFrame(
        [
            {
                "age": 21,
                "country": "VN",
            },
            {
                "age": 31,
                "country": "US",
            },
        ]
    )

    result = drift_api.analyze_drift(
        baseline_df=baseline_df,
        current_df=current_df,
    )

    assert captured["url"] == (
        drift_api.DRIFT_ANALYZE_URL
    )

    assert captured["json"] == {
        "baseline_records": [
            {
                "age": 20,
                "country": "VN",
            },
            {
                "age": 30,
                "country": "US",
            },
        ],
        "current_records": [
            {
                "age": 21,
                "country": "VN",
            },
            {
                "age": 31,
                "country": "US",
            },
        ],
    }

    assert captured["timeout"] == 15

    assert result["summary"][
        "overall_drift_level"
    ] == "Low"

    assert (
        result["schema_report"]["changes_df"]
        .to_dict(orient="records")
        == [
            {
                "change_type": "Added Column",
                "column_name": "segment",
            }
        ]
    )

    assert (
        result["numeric_drift_df"]
        .to_dict(orient="records")
        == [
            {
                "column_name": "age",
                "psi": 0.12,
            }
        ]
    )

    assert (
        result["categorical_drift_df"]
        .to_dict(orient="records")
        == [
            {
                "column_name": "country",
                "drift_level": "Low",
            }
        ]
    )

    assert (
        result["all_drift_df"]
        .to_dict(orient="records")
        == [
            {
                "column_name": "age",
                "drift_type": "numeric",
                "drift_level": "Low",
            }
        ]
    )


def test_analyze_drift_wraps_request_error(
    monkeypatch,
):
    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        drift_api.requests,
        "post",
        fake_post,
    )

    baseline_df = pd.DataFrame(
        [
            {
                "country": "VN",
            }
        ]
    )

    current_df = pd.DataFrame(
        [
            {
                "country": "US",
            }
        ]
    )

    with pytest.raises(
        drift_api.DriftApiError,
        match="Unable to analyze drift.",
    ):
        drift_api.analyze_drift(
            baseline_df=baseline_df,
            current_df=current_df,
        )


def test_get_categorical_distribution_posts_records_and_returns_dataframe(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "distribution_records": [
                    {
                        "value": "US",
                        "baseline_pct": 33.33,
                        "current_pct": 66.67,
                    },
                    {
                        "value": "VN",
                        "baseline_pct": 66.67,
                        "current_pct": 33.33,
                    },
                ]
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
        drift_api.requests,
        "post",
        fake_post,
    )

    baseline_df = pd.DataFrame(
        [
            {"country": "VN"},
            {"country": "VN"},
            {"country": "US"},
        ]
    )

    current_df = pd.DataFrame(
        [
            {"country": "VN"},
            {"country": "US"},
            {"country": "US"},
        ]
    )

    result = (
        drift_api.get_categorical_distribution(
            baseline_df=baseline_df,
            current_df=current_df,
            column_name="country",
        )
    )

    assert captured["url"] == (
        drift_api.CATEGORICAL_DISTRIBUTION_URL
    )

    assert captured["json"] == {
        "baseline_records": [
            {"country": "VN"},
            {"country": "VN"},
            {"country": "US"},
        ],
        "current_records": [
            {"country": "VN"},
            {"country": "US"},
            {"country": "US"},
        ],
        "column_name": "country",
    }

    assert captured["timeout"] == 15

    assert result.to_dict(
        orient="records"
    ) == [
        {
            "value": "US",
            "baseline_pct": 33.33,
            "current_pct": 66.67,
        },
        {
            "value": "VN",
            "baseline_pct": 66.67,
            "current_pct": 33.33,
        },
    ]


def test_get_categorical_distribution_wraps_request_error(
    monkeypatch,
):
    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        drift_api.requests,
        "post",
        fake_post,
    )

    baseline_df = pd.DataFrame(
        [
            {"country": "VN"},
        ]
    )

    current_df = pd.DataFrame(
        [
            {"country": "US"},
        ]
    )

    with pytest.raises(
        drift_api.DriftApiError,
        match=(
            "Unable to load categorical "
            "drift distribution."
        ),
    ):
        drift_api.get_categorical_distribution(
            baseline_df=baseline_df,
            current_df=current_df,
            column_name="country",
        )