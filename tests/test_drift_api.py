from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_analyze_drift_returns_serialized_report():
    response = client.post(
        "/api/drift/analyze",
        json={
            "baseline_records": [
                {
                    "age": 20,
                    "score": 70,
                },
                {
                    "age": 30,
                    "score": 80,
                },
            ],
            "current_records": [
                {
                    "age": 21,
                    "score": 72,
                },
                {
                    "age": 31,
                    "score": 82,
                },
            ],
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["summary"][
        "baseline_rows"
    ] == 2

    assert payload["summary"][
        "current_rows"
    ] == 2

    assert payload["schema_report"][
        "summary"
    ]["baseline_columns"] == 2

    assert payload["schema_report"][
        "summary"
    ]["current_columns"] == 2

    assert isinstance(
        payload["schema_report"][
            "change_records"
        ],
        list,
    )

    assert isinstance(
        payload["numeric_drift_records"],
        list,
    )

    assert isinstance(
        payload["categorical_drift_records"],
        list,
    )

    assert isinstance(
        payload["all_drift_records"],
        list,
    )


def test_analyze_drift_rejects_empty_baseline_records():
    response = client.post(
        "/api/drift/analyze",
        json={
            "baseline_records": [],
            "current_records": [
                {
                    "age": 21,
                    "score": 72,
                }
            ],
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "baseline_records must not be empty"
        )
    }


def test_analyze_drift_rejects_empty_current_records():
    response = client.post(
        "/api/drift/analyze",
        json={
            "baseline_records": [
                {
                    "age": 20,
                    "score": 70,
                }
            ],
            "current_records": [],
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "current_records must not be empty"
        )
    }


def test_categorical_distribution_returns_serialized_records():
    response = client.post(
        "/api/drift/categorical-distribution",
        json={
            "baseline_records": [
                {
                    "country": "VN",
                },
                {
                    "country": "VN",
                },
                {
                    "country": "US",
                },
            ],
            "current_records": [
                {
                    "country": "VN",
                },
                {
                    "country": "US",
                },
                {
                    "country": "US",
                },
            ],
            "column_name": "country",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
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
        ],
    }


def test_categorical_distribution_rejects_unknown_column():
    response = client.post(
        "/api/drift/categorical-distribution",
        json={
            "baseline_records": [
                {
                    "country": "VN",
                }
            ],
            "current_records": [
                {
                    "country": "US",
                }
            ],
            "column_name": "segment",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "column_name must exist in both datasets"
        )
    }