from __future__ import annotations

import pytest
import requests

from app.services import dataset_lineage_api


def test_load_dataset_lineage_returns_api_payload(
    monkeypatch,
):
    captured = {}

    payload = {
        "summary": {
            "version_id": 42,
            "catalog_id": 7,
            "ingestion_count": 2,
            "validation_count": 1,
        },
        "ingestions": [],
        "validations": [],
    }

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return payload

    def fake_get(
        url,
        *,
        timeout,
    ):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    result = (
        dataset_lineage_api.load_dataset_lineage(
            version_id=42,
        )
    )

    assert captured["url"] == (
        f"{dataset_lineage_api.DATASETS_URL}"
        "/42/lineage"
    )

    assert captured["timeout"] == 10
    assert result == payload


def test_load_dataset_lineage_wraps_request_error(
    monkeypatch,
):
    def fake_get(
        url,
        *,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        dataset_lineage_api.DatasetLineageApiError,
        match="Unable to load dataset lineage.",
    ):
        dataset_lineage_api.load_dataset_lineage(
            version_id=42,
        )


def test_load_catalog_lineage_returns_dataframe(
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
                        "catalog_id": 1,
                        "version_id": 5,
                        "version_number": 5,
                        "lifecycle_state": "ACTIVE",
                    },
                    {
                        "catalog_id": 1,
                        "version_id": 4,
                        "version_number": 4,
                        "lifecycle_state": "SUPERSEDED",
                    },
                ]
            }

    def fake_get(
        url,
        *,
        timeout,
    ):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    result = (
        dataset_lineage_api.load_catalog_lineage(
            catalog_id=1,
        )
    )

    assert captured["url"] == (
        f"{dataset_lineage_api.DATASETS_URL}"
        "/catalogs/1/lineage"
    )

    assert captured["timeout"] == 10

    assert result.to_dict(
        orient="records"
    ) == [
        {
            "catalog_id": 1,
            "version_id": 5,
            "version_number": 5,
            "lifecycle_state": "ACTIVE",
        },
        {
            "catalog_id": 1,
            "version_id": 4,
            "version_number": 4,
            "lifecycle_state": "SUPERSEDED",
        },
    ]


def test_load_catalog_lineage_wraps_request_error(
    monkeypatch,
):
    def fake_get(
        url,
        *,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        dataset_lineage_api.DatasetLineageApiError,
        match="Unable to load catalog lineage.",
    ):
        dataset_lineage_api.load_catalog_lineage(
            catalog_id=1,
        )


def test_load_dataset_version_history_returns_dataframe(
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
                        "version_id": 7,
                        "version_number": 2,
                        "file_name": "customers.csv",
                        "ingestion_count": 2,
                    },
                    {
                        "version_id": 6,
                        "version_number": 1,
                        "file_name": "customers.csv",
                        "ingestion_count": 0,
                    },
                ]
            }

    def fake_get(
        url,
        *,
        timeout,
    ):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    result = (
        dataset_lineage_api.load_dataset_version_history(
            catalog_id=1,
        )
    )

    assert captured["url"] == (
        f"{dataset_lineage_api.DATASETS_URL}"
        "/catalogs/1/versions"
    )

    assert captured["timeout"] == 10

    assert result.to_dict(
        orient="records"
    ) == [
        {
            "version_id": 7,
            "version_number": 2,
            "file_name": "customers.csv",
            "ingestion_count": 2,
        },
        {
            "version_id": 6,
            "version_number": 1,
            "file_name": "customers.csv",
            "ingestion_count": 0,
        },
    ]


def test_load_dataset_version_history_wraps_request_error(
    monkeypatch,
):
    def fake_get(
        url,
        *,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        dataset_lineage_api.DatasetLineageApiError,
        match="Unable to load dataset version history.",
    ):
        dataset_lineage_api.load_dataset_version_history(
            catalog_id=1,
        )


def test_load_ingestion_history_returns_dataframe(
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
                        "ingestion_event_id": 12,
                        "ingestion_id": "ing-002",
                        "catalog_id": 1,
                        "version_id": 7,
                        "version_number": 2,
                        "source_type": "UPLOAD",
                        "is_new_version": False,
                    },
                    {
                        "ingestion_event_id": 11,
                        "ingestion_id": "ing-001",
                        "catalog_id": 1,
                        "version_id": 6,
                        "version_number": 1,
                        "source_type": "UPLOAD",
                        "is_new_version": True,
                    },
                ]
            }

    def fake_get(
        url,
        *,
        params,
        timeout,
    ):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout

        return FakeResponse()

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    result = (
        dataset_lineage_api.load_ingestion_history(
            catalog_id=1,
            limit=2,
        )
    )

    assert captured["url"] == (
        f"{dataset_lineage_api.DATASETS_URL}"
        "/catalogs/1/ingestions"
    )

    assert captured["params"] == {
        "limit": 2,
    }

    assert captured["timeout"] == 10

    assert result.to_dict(
        orient="records"
    ) == [
        {
            "ingestion_event_id": 12,
            "ingestion_id": "ing-002",
            "catalog_id": 1,
            "version_id": 7,
            "version_number": 2,
            "source_type": "UPLOAD",
            "is_new_version": False,
        },
        {
            "ingestion_event_id": 11,
            "ingestion_id": "ing-001",
            "catalog_id": 1,
            "version_id": 6,
            "version_number": 1,
            "source_type": "UPLOAD",
            "is_new_version": True,
        },
    ]


def test_load_ingestion_history_wraps_request_error(
    monkeypatch,
):
    def fake_get(
        url,
        *,
        params,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        dataset_lineage_api.DatasetLineageApiError,
        match="Unable to load ingestion history.",
    ):
        dataset_lineage_api.load_ingestion_history(
            catalog_id=1,
            limit=50,
        )


def test_load_validation_history_returns_dataframe(
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
                        "validation_id": 21,
                        "catalog_id": 1,
                        "version_id": 7,
                        "version_number": 2,
                        "validation_status": "ACCEPTED",
                    }
                ]
            }

    def fake_get(
        url,
        *,
        params,
        timeout,
    ):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    result = (
        dataset_lineage_api.load_validation_history(
            catalog_id=1,
            limit=2,
        )
    )

    assert captured["url"] == (
        f"{dataset_lineage_api.DATASETS_URL}"
        "/catalogs/1/validations"
    )
    assert captured["params"] == {
        "limit": 2,
    }
    assert captured["timeout"] == 10

    assert result.to_dict(
        orient="records"
    ) == [
        {
            "validation_id": 21,
            "catalog_id": 1,
            "version_id": 7,
            "version_number": 2,
            "validation_status": "ACCEPTED",
        }
    ]


def test_load_validation_history_wraps_request_error(
    monkeypatch,
):
    def fake_get(
        url,
        *,
        params,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        dataset_lineage_api.DatasetLineageApiError,
        match="Unable to load validation history.",
    ):
        dataset_lineage_api.load_validation_history(
            catalog_id=1,
            limit=50,
        )


def test_load_governance_history_returns_dataframe(
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
                        "governance_id": 31,
                        "catalog_id": 1,
                        "version_id": 7,
                        "version_number": 2,
                        "decision": "APPROVED",
                        "promotion_eligible": True,
                    }
                ]
            }

    def fake_get(
        url,
        *,
        params,
        timeout,
    ):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    result = (
        dataset_lineage_api.load_governance_history(
            catalog_id=1,
            limit=2,
        )
    )

    assert captured["url"] == (
        f"{dataset_lineage_api.DATASETS_URL}"
        "/catalogs/1/governance"
    )
    assert captured["params"] == {
        "limit": 2,
    }
    assert captured["timeout"] == 10

    assert result.to_dict(
        orient="records"
    ) == [
        {
            "governance_id": 31,
            "catalog_id": 1,
            "version_id": 7,
            "version_number": 2,
            "decision": "APPROVED",
            "promotion_eligible": True,
        }
    ]


def test_load_governance_history_wraps_request_error(
    monkeypatch,
):
    def fake_get(
        url,
        *,
        params,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        dataset_lineage_api.DatasetLineageApiError,
        match="Unable to load governance history.",
    ):
        dataset_lineage_api.load_governance_history(
            catalog_id=1,
            limit=50,
        )


def test_load_catalog_lifecycle_returns_dataframe(
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
                        "version_id": 7,
                        "catalog_id": 1,
                        "version_number": 2,
                        "lifecycle_state": "VALIDATED",
                    }
                ]
            }

    def fake_get(
        url,
        *,
        timeout,
    ):
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    result = (
        dataset_lineage_api.load_catalog_lifecycle(
            catalog_id=1,
        )
    )

    assert captured["url"] == (
        f"{dataset_lineage_api.DATASETS_URL}"
        "/catalogs/1/lifecycle"
    )
    assert captured["timeout"] == 10

    assert result.to_dict(
        orient="records"
    ) == [
        {
            "version_id": 7,
            "catalog_id": 1,
            "version_number": 2,
            "lifecycle_state": "VALIDATED",
        }
    ]


def test_load_catalog_lifecycle_wraps_request_error(
    monkeypatch,
):
    def fake_get(
        url,
        *,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        dataset_lineage_api.DatasetLineageApiError,
        match="Unable to load catalog lifecycle.",
    ):
        dataset_lineage_api.load_catalog_lifecycle(
            catalog_id=1,
        )


def test_load_lifecycle_history_returns_dataframe(
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
                        "lifecycle_event_id": 41,
                        "catalog_id": 1,
                        "version_id": 7,
                        "from_state": "VALIDATED",
                        "to_state": "ACTIVE",
                        "reason": "Governance approved.",
                    }
                ]
            }

    def fake_get(
        url,
        *,
        timeout,
    ):
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    result = (
        dataset_lineage_api.load_lifecycle_history(
            version_id=7,
        )
    )

    assert captured["url"] == (
        f"{dataset_lineage_api.DATASETS_URL}"
        "/7/lifecycle"
    )
    assert captured["timeout"] == 10

    assert result.to_dict(
        orient="records"
    ) == [
        {
            "lifecycle_event_id": 41,
            "catalog_id": 1,
            "version_id": 7,
            "from_state": "VALIDATED",
            "to_state": "ACTIVE",
            "reason": "Governance approved.",
        }
    ]


def test_load_lifecycle_history_wraps_request_error(
    monkeypatch,
):
    def fake_get(
        url,
        *,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "get",
        fake_get,
    )

    with pytest.raises(
        dataset_lineage_api.DatasetLineageApiError,
        match="Unable to load lifecycle history.",
    ):
        dataset_lineage_api.load_lifecycle_history(
            version_id=7,
        )


def test_promote_dataset_version_returns_api_payload(
    monkeypatch,
):
    expected = {
        "version_id": 7,
        "catalog_id": 1,
        "previous_state": "VALIDATED",
        "lifecycle_state": "ACTIVE",
        "changed": True,
        "governance_decision": "APPROVED",
        "message": (
            "Dataset version promoted "
            "to ACTIVE successfully."
        ),
    }

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return expected

    def fake_post(
        url,
        *,
        timeout,
    ):
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "post",
        fake_post,
    )

    result = (
        dataset_lineage_api.promote_dataset_version(
            version_id=7,
        )
    )

    assert captured["url"] == (
        f"{dataset_lineage_api.DATASETS_URL}"
        "/7/promote"
    )
    assert captured["timeout"] == 10
    assert result == expected


def test_promote_dataset_version_wraps_request_error(
    monkeypatch,
):
    def fake_post(
        url,
        *,
        timeout,
    ):
        raise requests.RequestException(
            "connection failed"
        )

    monkeypatch.setattr(
        dataset_lineage_api.requests,
        "post",
        fake_post,
    )

    with pytest.raises(
        dataset_lineage_api.DatasetLineageApiError,
        match="Unable to promote dataset version.",
    ):
        dataset_lineage_api.promote_dataset_version(
            version_id=7,
        )