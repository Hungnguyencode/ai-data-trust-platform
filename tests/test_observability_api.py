from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import api.routes.observability as observability_routes
from api.main import app

client = TestClient(app)

FIXED_TIME = datetime(
    2026,
    9,
    17,
    1,
    0,
    tzinfo=UTC,
)


def patch_empty_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        observability_routes,
        "load_enabled_freshness_policies",
        lambda: pd.DataFrame(),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_enabled_volume_policies",
        lambda: pd.DataFrame(),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_operational_event_history",
        lambda limit: pd.DataFrame(),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_pipeline_run_history",
        lambda limit: pd.DataFrame(),
    )


def test_observability_overview_empty(
    monkeypatch: pytest.MonkeyPatch,
):
    patch_empty_sources(
        monkeypatch
    )

    response = client.get(
        "/api/observability/overview"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["summary"] == {
        "monitored_dataset_count": 0,
        "freshness_policy_count": 0,
        "freshness_breach_count": 0,
        "volume_policy_count": 0,
        "volume_breach_count": 0,
        "operational_event_count": 0,
        "recent_failed_pipeline_run_count": 0,
    }

    assert payload["datasets"] == []


def test_observability_overview_aggregates_dataset(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        observability_routes,
        "load_enabled_freshness_policies",
        lambda: pd.DataFrame(
            [
                {
                    "catalog_id": 1,
                }
            ]
        ),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_enabled_volume_policies",
        lambda: pd.DataFrame(
            [
                {
                    "catalog_id": 1,
                }
            ]
        ),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_freshness_history",
        lambda catalog_id, limit: pd.DataFrame(
            [
                {
                    "catalog_id": catalog_id,
                    "freshness_status": "STALE",
                    "checked_at": FIXED_TIME,
                }
            ]
        ),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_volume_history",
        lambda catalog_id, limit: pd.DataFrame(
            [
                {
                    "catalog_id": catalog_id,
                    "volume_status": "SPIKE",
                    "checked_at": FIXED_TIME,
                }
            ]
        ),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_operational_event_history",
        lambda limit: pd.DataFrame(
            [
                {
                    "operational_event_id": 10,
                    "catalog_id": 1,
                },
                {
                    "operational_event_id": 11,
                    "catalog_id": 1,
                },
            ]
        ),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_pipeline_run_history",
        lambda limit: pd.DataFrame(
            [
                {
                    "pipeline_run_id": 20,
                    "catalog_id": 1,
                    "run_status": "FAILED",
                    "finished_at": FIXED_TIME,
                }
            ]
        ),
    )

    response = client.get(
        "/api/observability/overview"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["summary"][
        "monitored_dataset_count"
    ] == 1

    assert payload["summary"][
        "freshness_breach_count"
    ] == 1

    assert payload["summary"][
        "volume_breach_count"
    ] == 1

    assert payload["summary"][
        "operational_event_count"
    ] == 2

    assert payload["summary"][
        "recent_failed_pipeline_run_count"
    ] == 1

    dataset = payload["datasets"][0]

    assert dataset[
        "catalog_id"
    ] == 1

    assert dataset[
        "freshness_status"
    ] == "STALE"

    assert dataset[
        "volume_status"
    ] == "SPIKE"

    assert dataset[
        "latest_pipeline_status"
    ] == "FAILED"

    assert dataset[
        "recent_operational_event_count"
    ] == 2


def test_observability_overview_unions_policy_catalogs(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        observability_routes,
        "load_enabled_freshness_policies",
        lambda: pd.DataFrame(
            [
                {"catalog_id": 1},
            ]
        ),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_enabled_volume_policies",
        lambda: pd.DataFrame(
            [
                {"catalog_id": 2},
            ]
        ),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_freshness_history",
        lambda catalog_id, limit: pd.DataFrame(),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_volume_history",
        lambda catalog_id, limit: pd.DataFrame(),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_operational_event_history",
        lambda limit: pd.DataFrame(),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_pipeline_run_history",
        lambda limit: pd.DataFrame(),
    )

    response = client.get(
        "/api/observability/overview"
    )

    assert response.status_code == 200

    payload = response.json()

    assert [
        item["catalog_id"]
        for item in payload["datasets"]
    ] == [
        1,
        2,
    ]

    assert payload["datasets"][0][
        "freshness_enabled"
    ] is True

    assert payload["datasets"][0][
        "volume_enabled"
    ] is False

    assert payload["datasets"][1][
        "freshness_enabled"
    ] is False

    assert payload["datasets"][1][
        "volume_enabled"
    ] is True


def test_observability_overview_passes_limits(
    monkeypatch: pytest.MonkeyPatch,
):
    captured = {}

    monkeypatch.setattr(
        observability_routes,
        "load_enabled_freshness_policies",
        lambda: pd.DataFrame(),
    )

    monkeypatch.setattr(
        observability_routes,
        "load_enabled_volume_policies",
        lambda: pd.DataFrame(),
    )

    def fake_events(
        *,
        limit: int,
    ):
        captured["event_limit"] = limit
        return pd.DataFrame()

    def fake_runs(
        *,
        limit: int,
    ):
        captured["run_limit"] = limit
        return pd.DataFrame()

    monkeypatch.setattr(
        observability_routes,
        "load_operational_event_history",
        fake_events,
    )

    monkeypatch.setattr(
        observability_routes,
        "load_pipeline_run_history",
        fake_runs,
    )

    response = client.get(
        "/api/observability/overview"
        "?event_limit=25&run_limit=30"
    )

    assert response.status_code == 200

    assert captured == {
        "event_limit": 25,
        "run_limit": 30,
    }


def test_observability_overview_returns_500(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_load():
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        observability_routes,
        "load_enabled_freshness_policies",
        fail_load,
    )

    response = client.get(
        "/api/observability/overview"
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Unable to load "
        "observability overview."
    )


def test_observability_overview_limit_validation():
    response = client.get(
        "/api/observability/overview"
        "?event_limit=0"
    )

    assert response.status_code == 422