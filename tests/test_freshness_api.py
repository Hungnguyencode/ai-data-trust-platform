from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import api.routes.freshness as freshness_routes
from api.main import app

client = TestClient(app)

FIXED_TIME = datetime(
    2026,
    9,
    16,
    1,
    0,
    tzinfo=UTC,
)


def build_policy(
    *,
    catalog_id: int = 1,
    max_age_minutes: int = 1440,
    is_enabled: bool = True,
) -> dict:
    return {
        "freshness_policy_id": 10,
        "catalog_id": catalog_id,
        "max_age_minutes": max_age_minutes,
        "is_enabled": is_enabled,
        "created_at": FIXED_TIME,
        "updated_at": FIXED_TIME,
    }


def build_check(
    *,
    catalog_id: int = 1,
    freshness_status: str = "FRESH",
    age_minutes: int | None = 30,
) -> dict:
    return {
        "freshness_check_id": 20,
        "catalog_id": catalog_id,
        "ingestion_event_id": 20005,
        "version_id": 3,
        "max_age_minutes": 1440,
        "age_minutes": age_minutes,
        "freshness_status": freshness_status,
        "latest_ingested_at": FIXED_TIME,
        "checked_at": FIXED_TIME,
    }


def build_operational_event() -> dict:
    return {
        "operational_event_id": 30,
        "event_key": (
            "freshness:1:20005:stale"
        ),
        "event_type": (
            "DATASET_FRESHNESS_BREACH"
        ),
        "severity": "WARNING",
        "event_source": "DATA_OBSERVABILITY",
        "event_stage": "FRESHNESS_MONITOR",
        "catalog_id": 1,
        "version_id": 3,
        "pipeline_run_id": None,
        "reference_id": 20,
        "message": (
            "Dataset freshness SLA "
            "was breached."
        ),
        "detail_json": "{}",
        "occurred_at": FIXED_TIME,
        "created_at": FIXED_TIME,
    }


def test_get_freshness_policy(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        freshness_routes,
        "load_freshness_policy",
        lambda catalog_id: build_policy(
            catalog_id=catalog_id
        ),
    )

    response = client.get(
        "/api/freshness/catalog/1/policy"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "freshness_policy_id"
    ] == 10
    assert payload["catalog_id"] == 1
    assert payload[
        "max_age_minutes"
    ] == 1440
    assert payload["is_enabled"] is True


def test_get_freshness_policy_returns_404(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        freshness_routes,
        "load_freshness_policy",
        lambda catalog_id: None,
    )

    response = client.get(
        "/api/freshness/catalog/99/policy"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "No freshness policy for "
        "catalog_id=99."
    )


def test_get_freshness_policy_returns_500(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_load(
        catalog_id: int,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        freshness_routes,
        "load_freshness_policy",
        fail_load,
    )

    response = client.get(
        "/api/freshness/catalog/1/policy"
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Unable to load freshness policy."
    )


def test_put_freshness_policy(
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    def fake_upsert(
        **kwargs,
    ):
        captured.update(
            kwargs
        )

        return build_policy(
            catalog_id=kwargs[
                "catalog_id"
            ],
            max_age_minutes=kwargs[
                "max_age_minutes"
            ],
            is_enabled=kwargs[
                "is_enabled"
            ],
        )

    monkeypatch.setattr(
        freshness_routes,
        "upsert_freshness_policy",
        fake_upsert,
    )

    response = client.put(
        "/api/freshness/catalog/1/policy",
        json={
            "max_age_minutes": 720,
            "is_enabled": True,
        },
    )

    assert response.status_code == 200

    assert captured == {
        "catalog_id": 1,
        "max_age_minutes": 720,
        "is_enabled": True,
    }

    payload = response.json()

    assert payload[
        "max_age_minutes"
    ] == 720


def test_put_freshness_policy_rejects_invalid_body():
    response = client.put(
        "/api/freshness/catalog/1/policy",
        json={
            "max_age_minutes": 0,
            "is_enabled": True,
        },
    )

    assert response.status_code == 422


def test_put_freshness_policy_returns_400(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_upsert(
        **kwargs,
    ):
        raise ValueError(
            "Invalid freshness policy."
        )

    monkeypatch.setattr(
        freshness_routes,
        "upsert_freshness_policy",
        fail_upsert,
    )

    response = client.put(
        "/api/freshness/catalog/1/policy",
        json={
            "max_age_minutes": 60,
            "is_enabled": True,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Invalid freshness policy."
    )


def test_put_freshness_policy_returns_500(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_upsert(
        **kwargs,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        freshness_routes,
        "upsert_freshness_policy",
        fail_upsert,
    )

    response = client.put(
        "/api/freshness/catalog/1/policy",
        json={
            "max_age_minutes": 60,
            "is_enabled": True,
        },
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Unable to save freshness policy."
    )


def test_get_freshness_history(
    monkeypatch: pytest.MonkeyPatch,
):
    history = pd.DataFrame(
        [
            build_check(),
            {
                **build_check(
                    freshness_status="STALE",
                    age_minutes=1500,
                ),
                "freshness_check_id": 21,
            },
        ]
    )

    captured = {}

    def fake_history(
        catalog_id: int,
        *,
        limit: int,
    ):
        captured["catalog_id"] = (
            catalog_id
        )
        captured["limit"] = limit
        return history

    monkeypatch.setattr(
        freshness_routes,
        "load_freshness_history",
        fake_history,
    )

    response = client.get(
        "/api/freshness/catalog/1/history"
        "?limit=25"
    )

    assert response.status_code == 200

    payload = response.json()

    assert captured == {
        "catalog_id": 1,
        "limit": 25,
    }

    assert payload["catalog_id"] == 1
    assert payload["limit"] == 25
    assert payload["count"] == 2

    assert (
        payload["items"][1][
            "freshness_status"
        ]
        == "STALE"
    )


def test_get_freshness_history_empty(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        freshness_routes,
        "load_freshness_history",
        lambda catalog_id, limit: (
            pd.DataFrame()
        ),
    )

    response = client.get(
        "/api/freshness/catalog/1/history"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["count"] == 0
    assert payload["items"] == []


def test_get_freshness_history_returns_500(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_history(
        catalog_id: int,
        *,
        limit: int,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        freshness_routes,
        "load_freshness_history",
        fail_history,
    )

    response = client.get(
        "/api/freshness/catalog/1/history"
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Unable to load freshness history."
    )


def test_run_freshness_check_fresh(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        freshness_routes,
        "check_dataset_freshness",
        lambda catalog_id: {
            "policy": build_policy(
                catalog_id=catalog_id
            ),
            "check": build_check(
                catalog_id=catalog_id
            ),
            "operational_event": None,
        },
    )

    response = client.post(
        "/api/freshness/catalog/1/check"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["check"][
            "freshness_status"
        ]
        == "FRESH"
    )

    assert (
        payload["operational_event"]
        is None
    )


def test_run_freshness_check_stale_with_alert(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        freshness_routes,
        "check_dataset_freshness",
        lambda catalog_id: {
            "policy": build_policy(
                catalog_id=catalog_id
            ),
            "check": build_check(
                catalog_id=catalog_id,
                freshness_status="STALE",
                age_minutes=1500,
            ),
            "operational_event": (
                build_operational_event()
            ),
        },
    )

    response = client.post(
        "/api/freshness/catalog/1/check"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["check"][
            "freshness_status"
        ]
        == "STALE"
    )

    assert (
        payload[
            "operational_event"
        ][
            "event_type"
        ]
        == "DATASET_FRESHNESS_BREACH"
    )


def test_run_freshness_check_without_policy_returns_404(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_check(
        catalog_id: int,
    ):
        raise ValueError(
            "No freshness policy exists "
            "for catalog_id=1."
        )

    monkeypatch.setattr(
        freshness_routes,
        "check_dataset_freshness",
        fail_check,
    )

    response = client.post(
        "/api/freshness/catalog/1/check"
    )

    assert response.status_code == 404


def test_run_freshness_check_disabled_returns_409(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_check(
        catalog_id: int,
    ):
        raise ValueError(
            "Freshness policy is disabled "
            "for catalog_id=1."
        )

    monkeypatch.setattr(
        freshness_routes,
        "check_dataset_freshness",
        fail_check,
    )

    response = client.post(
        "/api/freshness/catalog/1/check"
    )

    assert response.status_code == 409


def test_run_freshness_check_returns_500(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_check(
        catalog_id: int,
    ):
        raise RuntimeError(
            "unexpected failure"
        )

    monkeypatch.setattr(
        freshness_routes,
        "check_dataset_freshness",
        fail_check,
    )

    response = client.post(
        "/api/freshness/catalog/1/check"
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Unable to run freshness check."
    )


def test_freshness_catalog_id_validation():
    response = client.get(
        "/api/freshness/catalog/0/policy"
    )

    assert response.status_code == 422