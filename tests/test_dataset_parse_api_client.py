from __future__ import annotations

import requests

from app.services import dataset_parse_api


class FakeUploadedFile:
    name = "customers.csv"

    def getvalue(self):
        return b"name,age\nAlice,30\nBob,41\n"


def test_parse_dataset_posts_uploaded_file(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
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

    def fake_post(
        url,
        *,
        files,
        timeout,
    ):
        captured["url"] = url
        captured["files"] = files
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        dataset_parse_api.requests,
        "post",
        fake_post,
    )

    result = dataset_parse_api.parse_dataset(
        FakeUploadedFile()
    )

    assert captured["url"] == (
        dataset_parse_api.DATASET_PARSE_URL
    )

    assert captured["files"] == {
        "file": (
            "customers.csv",
            b"name,age\nAlice,30\nBob,41\n",
        )
    }

    assert captured["timeout"] == 15

    assert result["file_name"] == "customers.csv"
    assert result["file_type"] == "CSV"
    assert result["total_rows"] == 2
    assert result["total_columns"] == 2
    assert result["records"] == [
        {
            "name": "Alice",
            "age": 30,
        },
        {
            "name": "Bob",
            "age": 41,
        },
    ]


def test_parse_dataset_wraps_request_error(
    monkeypatch,
):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError(
            "internal network detail"
        )

    monkeypatch.setattr(
        dataset_parse_api.requests,
        "post",
        fake_post,
    )

    try:
        dataset_parse_api.parse_dataset(
            FakeUploadedFile()
        )
    except dataset_parse_api.DatasetParseApiError as exc:
        assert str(exc) == (
            "Unable to parse dataset."
        )
        assert (
            "internal network detail"
            not in str(exc)
        )
    else:
        raise AssertionError(
            "DatasetParseApiError was not raised."
        )