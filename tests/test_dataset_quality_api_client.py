from __future__ import annotations

from typing import Any

import pandas as pd
import pytest
import requests

import app.services.dataset_quality_api as dataset_quality_api


class FakeResponse:
    def __init__(
        self,
        payload: Any,
    ) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> Any:
        return self.payload


def test_load_dataset_quality_posts_json_safe_records_and_reconstructs_issue_frame(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_post(
        url: str,
        *,
        json: dict[str, Any],
        timeout: int,
    ) -> FakeResponse:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "summary": {
                    "total_issues": 1,
                },
                "issues": [
                    {
                        "issue_type": "missing_values",
                    },
                ],
                "issue_records": [
                    {
                        "issue_type": "missing_values",
                        "column_name": "age",
                    },
                ],
                "missing_records": [],
                "duplicate_row_records": [],
                "type_issue_records": [],
                "range_issue_records": [],
                "categorical_issue_records": [],
            }
        )

    monkeypatch.setattr(
        dataset_quality_api.requests,
        "post",
        fake_post,
    )

    df = pd.DataFrame(
        {
            "age": [
                25,
                None,
            ],
        }
    )

    result = dataset_quality_api.load_dataset_quality(
        df,
        file_name="quality.csv",
        file_type="CSV",
    )

    assert captured["url"] == (
        f"{dataset_quality_api.DATASET_QUALITY_URL}"
    )
    assert captured["timeout"] == 15

    assert captured["json"] == {
        "file_name": "quality.csv",
        "file_type": "CSV",
        "records": [
            {
                "age": 25.0,
            },
            {
                "age": None,
            },
        ],
    }

    assert result["summary"] == {
        "total_issues": 1,
    }
    assert result["issues"] == [
        {
            "issue_type": "missing_values",
        },
    ]

    assert isinstance(
        result["issues_df"],
        pd.DataFrame,
    )
    assert result["issues_df"].to_dict(
        orient="records",
    ) == [
        {
            "issue_type": "missing_values",
            "column_name": "age",
        },
    ]


def test_load_dataset_quality_reconstructs_detail_frames(
    monkeypatch: pytest.MonkeyPatch,
):
    payload = {
        "summary": {
            "total_issues": 1,
        },
        "issues": [],
        "issue_records": [],
        "missing_records": [
            {
                "column_name": "age",
                "missing_count": 1,
            },
        ],
        "duplicate_row_records": [
            {
                "age": 25,
            },
        ],
        "type_issue_records": [
            {
                "column_name": "age",
            },
        ],
        "range_issue_records": [
            {
                "column_name": "age",
            },
        ],
        "categorical_issue_records": [
            {
                "column_name": "status",
            },
        ],
    }

    monkeypatch.setattr(
        dataset_quality_api.requests,
        "post",
        lambda url, json, timeout: FakeResponse(
            payload
        ),
    )

    result = dataset_quality_api.load_dataset_quality(
        pd.DataFrame(
            {
                "age": [25],
            }
        )
    )

    assert result["missing_summary"].to_dict(
        orient="records",
    ) == payload["missing_records"]

    assert result["duplicate_rows_df"].to_dict(
        orient="records",
    ) == payload["duplicate_row_records"]

    assert result["type_issues_df"].to_dict(
        orient="records",
    ) == payload["type_issue_records"]

    assert result["range_issues_df"].to_dict(
        orient="records",
    ) == payload["range_issue_records"]

    assert result["categorical_issues_df"].to_dict(
        orient="records",
    ) == payload["categorical_issue_records"]


def test_load_dataset_quality_wraps_request_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_post(
        url: str,
        *,
        json: dict[str, Any],
        timeout: int,
    ):
        del url
        del json
        del timeout

        raise requests.ConnectionError(
            "connection failed"
        )

    monkeypatch.setattr(
        dataset_quality_api.requests,
        "post",
        fail_post,
    )

    with pytest.raises(
        dataset_quality_api.DatasetQualityApiError,
        match="Unable to load Dataset Quality",
    ):
        dataset_quality_api.load_dataset_quality(
            pd.DataFrame(
                {
                    "age": [25],
                }
            )
        )