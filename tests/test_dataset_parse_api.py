from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_parse_dataset_returns_records_and_metadata():
    response = client.post(
        "/api/datasets/parse",
        files={
            "file": (
                "customers.csv",
                b"name,age\nAlice,30\nBob,41\n",
                "text/csv",
            ),
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "file_name": "customers.csv",
        "file_type": "CSV",
        "total_rows": 2,
        "total_columns": 2,
        "records": [
            {
                "name": "Alice",
                "age": 30,
            },
            {
                "name": "Bob",
                "age": 41,
            },
        ],
    }


def test_parse_dataset_rejects_unsupported_file_type():
    response = client.post(
        "/api/datasets/parse",
        files={
            "file": (
                "customers.txt",
                b"name,age\nAlice,30\n",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]