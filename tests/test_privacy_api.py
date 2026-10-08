from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_privacy_api_returns_serialized_report():
    response = client.post(
        "/api/privacy/scan",
        json={
            "records": [
                {
                    "name": "Nguyen Van A",
                    "email": "alice@example.com",
                },
                {
                    "name": "Tran Thi B",
                    "email": "bob@example.com",
                },
            ],
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["summary"]["total_rows"] == 2

    assert isinstance(
        payload["findings_records"],
        list,
    )

    assert payload["summary"][
        "privacy_safety_score"
    ] <= 100.0

    assert payload["summary"][
        "risk_level"
    ] in {
        "Low",
        "Medium",
        "High",
        "Critical",
    }