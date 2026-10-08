import pandas as pd
import pytest
import requests

from app.services import scan_api


def test_save_full_scan_posts_json_safe_records(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "dataset_id": 3,
                "scan_id": 10,
                "score_id": 7,
                "saved_issues": 2,
            }

    def fake_post(url, *, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        scan_api.requests,
        "post",
        fake_post,
    )

    df = pd.DataFrame(
        {
            "age": [25, None],
        }
    )

    result = scan_api.save_full_scan(
        df,
        file_name="customers.csv",
        file_type="CSV",
    )

    assert captured["url"] == scan_api.FULL_SCAN_URL
    assert captured["json"] == {
        "file_name": "customers.csv",
        "file_type": "CSV",
        "records": [
            {"age": 25.0},
            {"age": None},
        ],
    }
    assert captured["timeout"] == 15

    assert result == {
        "dataset_id": 3,
        "scan_id": 10,
        "score_id": 7,
        "saved_issues": 2,
    }


def test_save_full_scan_wraps_request_error(
    monkeypatch,
):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError(
            "API unavailable"
        )

    monkeypatch.setattr(
        scan_api.requests,
        "post",
        fake_post,
    )

    with pytest.raises(
        scan_api.ScanApiError,
        match="Unable to save full scan",
    ):
        scan_api.save_full_scan(
            pd.DataFrame(
                {
                    "age": [25, 30],
                }
            ),
            file_name="customers.csv",
            file_type="CSV",
        )


def test_load_scan_history_reconstructs_frame(
    monkeypatch,
):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "limit": 50,
                "count": 1,
                "items": [
                    {
                        "scan_id": 10,
                        "dataset_id": 3,
                        "file_name": "customers.csv",
                        "file_type": "CSV",
                        "total_rows": 100,
                        "total_columns": 8,
                        "missing_cells": 4,
                        "duplicate_rows": 2,
                        "total_issues": 3,
                        "high_issues": 1,
                        "medium_issues": 1,
                        "low_issues": 1,
                        "affected_columns": 2,
                        "overall_score": 91.5,
                        "risk_level": "Low",
                        "ai_readiness": "Ready",
                        "created_at": "2026-09-10T10:30:00",
                    }
                ],
            }

    captured = {}

    def fake_get(url, *, params, timeout):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        scan_api.requests,
        "get",
        fake_get,
    )

    result = scan_api.load_scan_history(
        limit=50
    )

    assert captured["url"] == scan_api.SCAN_HISTORY_URL
    assert captured["params"] == {"limit": 50}
    assert captured["timeout"] == 15

    assert isinstance(result, pd.DataFrame)
    assert result.loc[0, "scan_id"] == 10
    assert result.loc[0, "overall_score"] == 91.5


def test_load_scan_detail_reconstructs_issue_frame(
    monkeypatch,
):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "scan": {
                    "scan_id": 10,
                    "dataset_id": 3,
                    "file_name": "customers.csv",
                    "file_type": "CSV",
                    "total_rows": 100,
                    "total_columns": 8,
                    "missing_cells": 4,
                    "duplicate_rows": 2,
                    "total_issues": 1,
                    "high_issues": 1,
                    "medium_issues": 0,
                    "low_issues": 0,
                    "affected_columns": 1,
                    "overall_score": 91.5,
                    "risk_level": "Low",
                    "ai_readiness": "Ready",
                    "created_at": "2026-09-10T10:30:00",
                },
                "quality_issue_count": 1,
                "quality_issues": [
                    {
                        "issue_id": 21,
                        "scan_id": 10,
                        "issue_type": "missing_value",
                        "column_name": "email",
                        "severity": "High",
                        "issue_count": 4,
                        "issue_rate": 4.0,
                        "description": "Missing values detected.",
                        "recommendation": "Review source data.",
                        "created_at": "2026-09-10T10:30:01",
                    }
                ],
            }

    captured = {}

    def fake_get(url, *, timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        scan_api.requests,
        "get",
        fake_get,
    )

    result = scan_api.load_scan_detail(
        10
    )

    assert (
        captured["url"]
        == f"{scan_api.SCANS_URL}/10"
    )
    assert captured["timeout"] == 15

    assert result["scan"]["scan_id"] == 10
    assert result["quality_issue_count"] == 1

    issues_df = result["issues_df"]

    assert isinstance(
        issues_df,
        pd.DataFrame,
    )
    assert issues_df.loc[0, "issue_type"] == "missing_value"
    assert issues_df.loc[0, "severity"] == "High"


def test_load_scan_history_wraps_request_error(
    monkeypatch,
):
    def fake_get(*args, **kwargs):
        raise requests.ConnectionError(
            "API unavailable"
        )

    monkeypatch.setattr(
        scan_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        scan_api.ScanApiError,
        match="Unable to load scan history",
    ):
        scan_api.load_scan_history(
            limit=50
        )


def test_load_scan_detail_wraps_request_error(
    monkeypatch,
):
    def fake_get(*args, **kwargs):
        raise requests.ConnectionError(
            "API unavailable"
        )

    monkeypatch.setattr(
        scan_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        scan_api.ScanApiError,
        match="Unable to load scan detail",
    ):
        scan_api.load_scan_detail(
            10
        )