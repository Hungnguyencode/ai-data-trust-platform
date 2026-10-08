from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_anomaly_api_returns_serialized_report():
    response = client.post(
        "/api/anomaly/analyze",
        json={
            "records": [
                {"value": 1.0},
                {"value": 2.0},
                {"value": 3.0},
                {"value": 100.0},
            ],
            "zscore_threshold": 3.0,
            "isolation_contamination": 0.1,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["summary"]["total_rows"] == 4

    assert isinstance(
        payload["summary_records"],
        list,
    )

    assert isinstance(
        payload["combined_outlier_records"],
        list,
    )

    assert isinstance(
        payload["iqr_result"]["summary_records"],
        list,
    )

    assert isinstance(
        payload["iqr_result"]["outlier_row_indexes"],
        list,
    )

    assert isinstance(
        payload["zscore_result"]["summary_records"],
        list,
    )

    assert isinstance(
        payload["zscore_result"]["outlier_row_indexes"],
        list,
    )

    assert isinstance(
        payload[
            "isolation_forest_result"
        ]["score_records"],
        list,
    )

    assert isinstance(
        payload[
            "isolation_forest_result"
        ]["outlier_row_indexes"],
        list,
    )