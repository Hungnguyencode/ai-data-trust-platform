from __future__ import annotations

import pandas as pd
from fastapi.testclient import TestClient

from api.main import app
from src.validation.rule_engine import run_quality_checks

client = TestClient(app)


def test_dataset_quality_matches_core_summary():
    records = [
        {
            "age": 25,
            "status": "active",
        },
        {
            "age": None,
            "status": "active",
        },
        {
            "age": 200,
            "status": "unknown",
        },
    ]

    df = pd.DataFrame(records)
    core_result = run_quality_checks(df)

    response = client.post(
        "/api/datasets/quality",
        json={
            "file_name": "quality.csv",
            "file_type": "CSV",
            "records": records,
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["summary"]
        == core_result["summary"]
    )


def test_dataset_quality_serializes_issue_records():
    records = [
        {
            "age": 25,
            "status": "active",
        },
        {
            "age": None,
            "status": "active",
        },
        {
            "age": 200,
            "status": "unknown",
        },
    ]

    df = pd.DataFrame(records)
    core_result = run_quality_checks(df)

    response = client.post(
        "/api/datasets/quality",
        json={
            "file_name": "quality.csv",
            "file_type": "CSV",
            "records": records,
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["issue_records"]
        == core_result["issues_df"].to_dict(
            orient="records",
        )
    )


def test_dataset_quality_serializes_detail_tables():
    records = [
        {
            "age": 25,
            "status": "active",
        },
        {
            "age": None,
            "status": "active",
        },
        {
            "age": 200,
            "status": "unknown",
        },
    ]

    df = pd.DataFrame(records)
    core_result = run_quality_checks(df)

    response = client.post(
        "/api/datasets/quality",
        json={
            "file_name": "quality.csv",
            "file_type": "CSV",
            "records": records,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["missing_records"]
        == core_result["missing_summary"].to_dict(
            orient="records",
        )
    )
    assert (
        payload["duplicate_row_records"]
        == core_result["duplicate_rows_df"].to_dict(
            orient="records",
        )
    )
    assert (
        payload["type_issue_records"]
        == core_result["type_issues_df"].to_dict(
            orient="records",
        )
    )
    assert (
        payload["range_issue_records"]
        == core_result["range_issues_df"].to_dict(
            orient="records",
        )
    )
    assert (
        payload["categorical_issue_records"]
        == core_result[
            "categorical_issues_df"
        ].to_dict(
            orient="records",
        )
    )


def test_dataset_quality_serializes_raw_issues():
    records = [
        {
            "age": 25,
            "status": "active",
        },
        {
            "age": None,
            "status": "active",
        },
        {
            "age": 200,
            "status": "unknown",
        },
    ]

    df = pd.DataFrame(records)
    core_result = run_quality_checks(df)

    response = client.post(
        "/api/datasets/quality",
        json={
            "file_name": "quality.csv",
            "file_type": "CSV",
            "records": records,
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["issues"]
        == core_result["issues"]
    )