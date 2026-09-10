from __future__ import annotations

import pandas as pd
from fastapi.testclient import TestClient

import api.routes.scans as scan_route
from api.main import app

client = TestClient(app)


def build_scan_frame(
    *,
    scan_id: int = 10,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "scan_id": scan_id,
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
                "created_at": pd.Timestamp(
                    "2026-09-10T10:30:00"
                ),
            }
        ]
    )


def build_issue_frame(
    *,
    scan_id: int = 10,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "issue_id": 21,
                "scan_id": scan_id,
                "issue_type": "missing_value",
                "column_name": "email",
                "severity": "High",
                "issue_count": 4,
                "issue_rate": 4.0,
                "description": (
                    "Missing values detected."
                ),
                "recommendation": (
                    "Review source data."
                ),
                "created_at": pd.Timestamp(
                    "2026-09-10T10:30:01"
                ),
            }
        ]
    )


def test_scan_history_returns_persisted_rows(
    monkeypatch,
):
    def fake_history(
        limit: int,
    ):
        assert limit == 50

        return build_scan_frame()

    monkeypatch.setattr(
        scan_route,
        "load_scan_history",
        fake_history,
    )

    response = client.get(
        "/api/scans/history"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["limit"] == 50
    assert payload["count"] == 1

    assert (
        payload["items"][0]["scan_id"]
        == 10
    )

    assert (
        payload["items"][0]["file_name"]
        == "customers.csv"
    )

    assert (
        payload["items"][0]["overall_score"]
        == 91.5
    )


def test_scan_history_respects_limit(
    monkeypatch,
):
    def fake_history(
        limit: int,
    ):
        assert limit == 5
        return build_scan_frame()

    monkeypatch.setattr(
        scan_route,
        "load_scan_history",
        fake_history,
    )

    response = client.get(
        "/api/scans/history?limit=5"
    )

    assert response.status_code == 200
    assert response.json()["limit"] == 5


def test_scan_history_can_be_empty(
    monkeypatch,
):
    monkeypatch.setattr(
        scan_route,
        "load_scan_history",
        lambda limit: pd.DataFrame(),
    )

    response = client.get(
        "/api/scans/history"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["items"] == []


def test_latest_scan_returns_detail(
    monkeypatch,
):
    monkeypatch.setattr(
        scan_route,
        "load_scan_history",
        lambda limit: build_scan_frame(),
    )

    monkeypatch.setattr(
        scan_route,
        "load_quality_issues_by_scan",
        lambda scan_id: build_issue_frame(
            scan_id=scan_id
        ),
    )

    response = client.get(
        "/api/scans/latest"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["scan"]["scan_id"] == 10

    assert (
        payload["quality_issue_count"]
        == 1
    )

    assert (
        payload["quality_issues"][0][
            "severity"
        ]
        == "High"
    )


def test_latest_scan_returns_404_when_empty(
    monkeypatch,
):
    monkeypatch.setattr(
        scan_route,
        "load_scan_history",
        lambda limit: pd.DataFrame(),
    )

    response = client.get(
        "/api/scans/latest"
    )

    assert response.status_code == 404


def test_scan_detail_returns_scan_and_issues(
    monkeypatch,
):
    monkeypatch.setattr(
        scan_route,
        "load_scan_by_id",
        lambda scan_id: build_scan_frame(
            scan_id=scan_id
        ),
    )

    monkeypatch.setattr(
        scan_route,
        "load_quality_issues_by_scan",
        lambda scan_id: build_issue_frame(
            scan_id=scan_id
        ),
    )

    response = client.get(
        "/api/scans/25"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["scan"]["scan_id"] == 25

    assert (
        payload["quality_issues"][0]["scan_id"]
        == 25
    )


def test_scan_detail_returns_404_when_missing(
    monkeypatch,
):
    monkeypatch.setattr(
        scan_route,
        "load_scan_by_id",
        lambda scan_id: pd.DataFrame(),
    )

    response = client.get(
        "/api/scans/999"
    )

    assert response.status_code == 404


def test_scan_api_hides_repository_error(
    monkeypatch,
):
    def fake_history(
        limit: int,
    ):
        raise RuntimeError(
            "database password leaked"
        )

    monkeypatch.setattr(
        scan_route,
        "load_scan_history",
        fake_history,
    )

    response = client.get(
        "/api/scans/history"
    )

    assert response.status_code == 500

    assert (
        "database password leaked"
        not in str(response.json())
    )