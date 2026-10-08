from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest
import requests

import app.services.dataset_workflow_api as dataset_workflow_api


def test_run_dataset_workflow_reconstructs_dataframes(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "records": [
                    {
                        "customer_id": 1,
                        "age": 25,
                    }
                ],
                "profile": {
                    "basic_info": {
                        "total_rows": 1,
                    },
                    "schema_summary": [
                        {
                            "column_name": "age",
                            "dtype": "int64",
                        }
                    ],
                    "missing_summary": [
                        {
                            "column_name": "age",
                            "missing_count": 0,
                        }
                    ],
                    "numeric_summary": [
                        {
                            "column_name": "age",
                            "mean": 25.0,
                        }
                    ],
                    "categorical_summary": [],
                },
                "ingestion_metadata": {
                    "ingestion_id": "ingestion-123",
                },
                "catalog_registration": {
                    "catalog_id": 1,
                    "version_id": 7,
                    "version_number": 3,
                },
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
        dataset_workflow_api.requests,
        "post",
        fake_post,
    )

    uploaded_file = BytesIO(
        b"customer_id,age\n1,25\n"
    )
    uploaded_file.name = "customers.csv"

    result = (
        dataset_workflow_api.run_dataset_workflow(
            uploaded_file
        )
    )

    assert captured["url"] == (
        dataset_workflow_api.DATASET_WORKFLOW_URL
    )

    assert captured["files"]["file"] == (
        "customers.csv",
        b"customer_id,age\n1,25\n",
    )

    assert isinstance(
        result["dataframe"],
        pd.DataFrame,
    )

    assert result["dataframe"].to_dict(
        orient="records"
    ) == [
        {
            "customer_id": 1,
            "age": 25,
        }
    ]

    for key in (
        "schema_summary",
        "missing_summary",
        "numeric_summary",
        "categorical_summary",
    ):
        assert isinstance(
            result["profile"][key],
            pd.DataFrame,
        )


def test_run_dataset_workflow_wraps_request_error(
    monkeypatch,
):
    def fake_post(
        url,
        *,
        files,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        dataset_workflow_api.requests,
        "post",
        fake_post,
    )

    uploaded_file = BytesIO(
        b"customer_id,age\n1,25\n"
    )
    uploaded_file.name = "customers.csv"

    with pytest.raises(
        dataset_workflow_api.DatasetWorkflowApiError,
        match="Unable to run dataset workflow.",
    ):
        dataset_workflow_api.run_dataset_workflow(
            uploaded_file
        )


def test_continue_dataset_workflow_reuses_ingestion_payload(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "records": [
                    {
                        "customer_id": 1,
                        "age": 25,
                    }
                ],
                "profile": {
                    "schema_summary": [],
                    "missing_summary": [],
                    "numeric_summary": [],
                    "categorical_summary": [],
                },
                "ingestion_metadata": {
                    "ingestion_id": "ingestion-123",
                },
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
        dataset_workflow_api.requests,
        "post",
        fake_post,
    )

    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 1,
                "age": 25,
            }
        ]
    )

    ingestion_metadata = {
        "ingestion_id": "ingestion-123",
        "source_type": "upload",
        "file_name": "customers.csv",
        "file_type": "csv",
        "extension": ".csv",
        "content_sha256": "abc123",
        "byte_size": 21,
        "row_count": 1,
        "column_count": 2,
        "ingested_at": "2026-09-18T10:00:00",
        "raw_path": "data/raw/customers.csv",
    }

    result = (
        dataset_workflow_api.continue_dataset_workflow(
            dataframe=dataframe,
            ingestion_metadata=ingestion_metadata,
        )
    )

    assert captured["url"] == (
        dataset_workflow_api.DATASET_WORKFLOW_CONTINUE_URL
    )

    assert captured["json"] == {
        "records": [
            {
                "customer_id": 1,
                "age": 25,
            }
        ],
        "ingestion_metadata": ingestion_metadata,
    }

    assert result["ingestion_metadata"][
        "ingestion_id"
    ] == "ingestion-123"

    assert isinstance(
        result["dataframe"],
        pd.DataFrame,
    )


def test_ingest_dataset_returns_reusable_ingestion(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "records": [
                    {
                        "customer_id": 1,
                        "age": 25,
                    }
                ],
                "ingestion_metadata": {
                    "ingestion_id": "ingestion-123",
                    "source_type": "upload",
                    "file_name": "customers.csv",
                    "file_type": "csv",
                    "extension": ".csv",
                    "content_sha256": "abc123",
                    "byte_size": 21,
                    "row_count": 1,
                    "column_count": 2,
                    "ingested_at": "2026-09-18T10:00:00",
                    "raw_path": "data/raw/customers.csv",
                },
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
        dataset_workflow_api.requests,
        "post",
        fake_post,
    )

    uploaded_file = BytesIO(
        b"customer_id,age\n1,25\n"
    )
    uploaded_file.name = "customers.csv"

    result = (
        dataset_workflow_api.ingest_dataset(
            uploaded_file
        )
    )

    assert captured["url"] == (
        dataset_workflow_api.DATASET_WORKFLOW_INGEST_URL
    )

    assert captured["files"]["file"] == (
        "customers.csv",
        b"customer_id,age\n1,25\n",
    )

    assert isinstance(
        result["dataframe"],
        pd.DataFrame,
    )

    assert result["dataframe"].to_dict(
        orient="records"
    ) == [
        {
            "customer_id": 1,
            "age": 25,
        }
    ]

    assert result["ingestion_metadata"][
        "ingestion_id"
    ] == "ingestion-123"


def test_continue_dataset_workflow_preserves_api_stage(
    monkeypatch,
):
    class FakeResponse:
        def raise_for_status(self):
            raise requests.HTTPError(
                "500 Server Error",
                response=self,
            )

        def json(self):
            return {
                "detail": {
                    "stage": "VALIDATION",
                    "message": (
                        "Dataset workflow could not "
                        "be completed."
                    ),
                }
            }

    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        return FakeResponse()

    monkeypatch.setattr(
        dataset_workflow_api.requests,
        "post",
        fake_post,
    )

    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 1,
                "age": 25,
            }
        ]
    )

    with pytest.raises(
        dataset_workflow_api.DatasetWorkflowApiError
    ) as exc_info:
        dataset_workflow_api.continue_dataset_workflow(
            dataframe=dataframe,
            ingestion_metadata={
                "ingestion_id": "ingestion-123",
            },
        )

    assert exc_info.value.stage == "VALIDATION"

    assert str(exc_info.value) == (
        "Dataset workflow could not be completed."
    )


def test_calculate_sha256():
    assert (
        dataset_workflow_api.calculate_sha256(
            b"abc"
        )
        == (
            "ba7816bf8f01cfea414140de5dae2223"
            "b00361a396177a9cb410ff61f20015ad"
        )
    )


def test_continue_dataset_workflow_normalizes_missing_values(
    monkeypatch,
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "records": [
                    {
                        "customer_id": 1,
                        "age": None,
                    }
                ],
                "profile": {
                    "schema_summary": [],
                    "missing_summary": [],
                    "numeric_summary": [],
                    "categorical_summary": [],
                },
                "ingestion_metadata": {
                    "ingestion_id": "ingestion-123",
                },
            }

    def fake_post(
        url,
        *,
        json,
        timeout,
    ):
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(
        dataset_workflow_api.requests,
        "post",
        fake_post,
    )

    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 1,
                "age": float("nan"),
            }
        ]
    )

    dataset_workflow_api.continue_dataset_workflow(
        dataframe=dataframe,
        ingestion_metadata={
            "ingestion_id": "ingestion-123",
        },
    )

    assert captured["json"]["records"] == [
        {
            "customer_id": 1,
            "age": None,
        }
    ]