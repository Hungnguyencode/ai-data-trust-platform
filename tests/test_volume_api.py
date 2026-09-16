from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import api.routes.volume as volume_routes
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
    drop_threshold_pct: float = 20.0,
    spike_threshold_pct: float = 10.0,
    is_enabled: bool = True,
) -> dict:
    return {
        "volume_policy_id": 10,
        "catalog_id": catalog_id,
        "drop_threshold_pct": (
            drop_threshold_pct
        ),
        "spike_threshold_pct": (
            spike_threshold_pct
        ),
        "is_enabled": is_enabled,
        "created_at": FIXED_TIME,
        "updated_at": FIXED_TIME,
    }


def build_check(
    *,
    catalog_id: int = 1,
    volume_status: str = "NORMAL",
    row_change_pct: float | None = 5.0,
) -> dict:
    return {
        "volume_check_id": 20,
        "volume_policy_id": 10,
        "catalog_id": catalog_id,
        "ingestion_event_id": 20005,
        "version_id": 3,
        "baseline_ingestion_event_id": 20004,
        "baseline_version_id": 2,
        "baseline_row_count": 7,
        "current_row_count": 8,
        "drop_threshold_pct": 20.0,
        "spike_threshold_pct": 10.0,
        "row_change_pct": row_change_pct,
        "volume_status": volume_status,
        "checked_at": FIXED_TIME,
    }


def build_operational_event() -> dict:
    return {
        "operational_event_id": 30,
        "event_key": (
            "volume:1:20005:spike"
        ),
        "event_type": (
            "DATASET_VOLUME_BREACH"
        ),
        "severity": "WARNING",
        "event_source": (
            "DATA_OBSERVABILITY"
        ),
        "event_stage": (
            "VOLUME_MONITOR"
        ),
        "catalog_id": 1,
        "version_id": 3,
        "pipeline_run_id": None,
        "reference_id": 20,
        "message": (
            "Dataset row volume spike "
            "threshold was breached."
        ),
        "detail_json": "{}",
        "occurred_at": FIXED_TIME,
        "created_at": FIXED_TIME,
    }


def test_get_volume_policy(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        volume_routes,
        "load_volume_policy",
        lambda catalog_id: build_policy(
            catalog_id=catalog_id
        ),
    )

    response = client.get(
        "/api/volume/catalog/1/policy"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "volume_policy_id"
    ] == 10

    assert payload[
        "catalog_id"
    ] == 1

    assert payload[
        "drop_threshold_pct"
    ] == 20.0

    assert payload[
        "spike_threshold_pct"
    ] == 10.0

    assert payload[
        "is_enabled"
    ] is True


def test_get_volume_policy_returns_404(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        volume_routes,
        "load_volume_policy",
        lambda catalog_id: None,
    )

    response = client.get(
        "/api/volume/catalog/99/policy"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "No volume policy for "
        "catalog_id=99."
    )


def test_get_volume_policy_returns_500(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_load(
        catalog_id: int,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        volume_routes,
        "load_volume_policy",
        fail_load,
    )

    response = client.get(
        "/api/volume/catalog/1/policy"
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Unable to load volume policy."
    )


def test_put_volume_policy(
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
            drop_threshold_pct=kwargs[
                "drop_threshold_pct"
            ],
            spike_threshold_pct=kwargs[
                "spike_threshold_pct"
            ],
            is_enabled=kwargs[
                "is_enabled"
            ],
        )

    monkeypatch.setattr(
        volume_routes,
        "upsert_volume_policy",
        fake_upsert,
    )

    response = client.put(
        "/api/volume/catalog/1/policy",
        json={
            "drop_threshold_pct": 25,
            "spike_threshold_pct": 15,
            "is_enabled": True,
        },
    )

    assert response.status_code == 200

    assert captured == {
        "catalog_id": 1,
        "drop_threshold_pct": 25.0,
        "spike_threshold_pct": 15.0,
        "is_enabled": True,
    }

    payload = response.json()

    assert payload[
        "drop_threshold_pct"
    ] == 25.0

    assert payload[
        "spike_threshold_pct"
    ] == 15.0


def test_put_volume_policy_rejects_invalid_body():
    response = client.put(
        "/api/volume/catalog/1/policy",
        json={
            "drop_threshold_pct": 0,
            "spike_threshold_pct": 10,
            "is_enabled": True,
        },
    )

    assert response.status_code == 422


def test_put_volume_policy_returns_400(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_upsert(
        **kwargs,
    ):
        raise ValueError(
            "Invalid volume policy."
        )

    monkeypatch.setattr(
        volume_routes,
        "upsert_volume_policy",
        fail_upsert,
    )

    response = client.put(
        "/api/volume/catalog/1/policy",
        json={
            "drop_threshold_pct": 20,
            "spike_threshold_pct": 10,
            "is_enabled": True,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Invalid volume policy."
    )


def test_put_volume_policy_returns_500(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_upsert(
        **kwargs,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        volume_routes,
        "upsert_volume_policy",
        fail_upsert,
    )

    response = client.put(
        "/api/volume/catalog/1/policy",
        json={
            "drop_threshold_pct": 20,
            "spike_threshold_pct": 10,
            "is_enabled": True,
        },
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Unable to save volume policy."
    )


def test_get_volume_history(
    monkeypatch: pytest.MonkeyPatch,
):
    history = pd.DataFrame(
        [
            build_check(),
            {
                **build_check(
                    volume_status="SPIKE",
                    row_change_pct=25.0,
                ),
                "volume_check_id": 21,
            },
        ]
    )

    captured = {}

    def fake_history(
        catalog_id: int,
        *,
        limit: int,
    ):
        captured[
            "catalog_id"
        ] = catalog_id

        captured[
            "limit"
        ] = limit

        return history

    monkeypatch.setattr(
        volume_routes,
        "load_volume_history",
        fake_history,
    )

    response = client.get(
        "/api/volume/catalog/1/history"
        "?limit=25"
    )

    assert response.status_code == 200

    payload = response.json()

    assert captured == {
        "catalog_id": 1,
        "limit": 25,
    }

    assert payload[
        "catalog_id"
    ] == 1

    assert payload[
        "limit"
    ] == 25

    assert payload[
        "count"
    ] == 2

    assert (
        payload["items"][1][
            "volume_status"
        ]
        == "SPIKE"
    )


def test_get_volume_history_empty(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        volume_routes,
        "load_volume_history",
        lambda catalog_id, limit: (
            pd.DataFrame()
        ),
    )

    response = client.get(
        "/api/volume/catalog/1/history"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "count"
    ] == 0

    assert payload[
        "items"
    ] == []


def test_get_volume_history_returns_500(
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
        volume_routes,
        "load_volume_history",
        fail_history,
    )

    response = client.get(
        "/api/volume/catalog/1/history"
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Unable to load volume history."
    )


def test_run_volume_check_normal(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        volume_routes,
        "check_dataset_volume",
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
        "/api/volume/catalog/1/check"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["check"][
            "volume_status"
        ]
        == "NORMAL"
    )

    assert (
        payload[
            "operational_event"
        ]
        is None
    )


def test_run_volume_check_spike_with_alert(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        volume_routes,
        "check_dataset_volume",
        lambda catalog_id: {
            "policy": build_policy(
                catalog_id=catalog_id
            ),
            "check": build_check(
                catalog_id=catalog_id,
                volume_status="SPIKE",
                row_change_pct=25.0,
            ),
            "operational_event": (
                build_operational_event()
            ),
        },
    )

    response = client.post(
        "/api/volume/catalog/1/check"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["check"][
            "volume_status"
        ]
        == "SPIKE"
    )

    assert (
        payload[
            "operational_event"
        ][
            "event_type"
        ]
        == "DATASET_VOLUME_BREACH"
    )


def test_run_volume_check_without_policy_returns_404(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_check(
        catalog_id: int,
    ):
        raise ValueError(
            "No volume policy for "
            "catalog_id=1."
        )

    monkeypatch.setattr(
        volume_routes,
        "check_dataset_volume",
        fail_check,
    )

    response = client.post(
        "/api/volume/catalog/1/check"
    )

    assert response.status_code == 404


def test_run_volume_check_disabled_returns_409(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_check(
        catalog_id: int,
    ):
        raise ValueError(
            "Volume monitoring is disabled for "
            "catalog_id=1."
        )

    monkeypatch.setattr(
        volume_routes,
        "check_dataset_volume",
        fail_check,
    )

    response = client.post(
        "/api/volume/catalog/1/check"
    )

    assert response.status_code == 409


def test_run_volume_check_without_ingestion_returns_409(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_check(
        catalog_id: int,
    ):
        raise ValueError(
            "No ingestion history for "
            "catalog_id=1."
        )

    monkeypatch.setattr(
        volume_routes,
        "check_dataset_volume",
        fail_check,
    )

    response = client.post(
        "/api/volume/catalog/1/check"
    )

    assert response.status_code == 409


def test_run_volume_check_returns_500(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_check(
        catalog_id: int,
    ):
        raise RuntimeError(
            "unexpected failure"
        )

    monkeypatch.setattr(
        volume_routes,
        "check_dataset_volume",
        fail_check,
    )

    response = client.post(
        "/api/volume/catalog/1/check"
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Unable to run volume check."
    )


def test_volume_catalog_id_validation():
    response = client.get(
        "/api/volume/catalog/0/policy"
    )

    assert response.status_code == 422