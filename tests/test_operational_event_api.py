from __future__ import annotations

from datetime import datetime

import pandas as pd
from fastapi.testclient import TestClient

import api.routes.operational_events as operational_events
from api.main import app

client = TestClient(app)


def build_operational_event(
    *,
    operational_event_id: int = 10002,
    event_type: str = "PIPELINE_FAILED",
    severity: str = "CRITICAL",
) -> dict:
    occurred_at = datetime(
        2026,
        9,
        15,
        11,
        0,
        50,
    )

    return {
        "operational_event_id": (
            operational_event_id
        ),
        "event_key": (
            "pipeline-run:"
            f"{operational_event_id}:failed"
        ),
        "event_type": event_type,
        "severity": severity,
        "event_source": "AIRFLOW",
        "event_stage": "VALIDATE_INPUT",
        "catalog_id": None,
        "version_id": None,
        "pipeline_run_id": 10002,
        "reference_id": None,
        "message": (
            "Airflow pipeline run failed."
        ),
        "detail_json": (
            '{"error_type": '
            '"FileNotFoundError"}'
        ),
        "occurred_at": occurred_at,
        "created_at": occurred_at,
    }


def test_get_operational_events_returns_history(
    monkeypatch,
):
    event = build_operational_event()

    history = pd.DataFrame(
        [event]
    )

    captured = {}

    def fake_load_history(
        limit: int,
    ):
        captured["limit"] = limit
        return history

    monkeypatch.setattr(
        operational_events,
        "load_operational_event_history",
        fake_load_history,
    )

    response = client.get(
        "/api/operational-events?limit=25"
    )

    assert response.status_code == 200

    payload = response.json()

    assert captured["limit"] == 25
    assert payload["limit"] == 25
    assert payload["count"] == 1
    assert len(payload["items"]) == 1

    item = payload["items"][0]

    assert (
        item["operational_event_id"]
        == 10002
    )
    assert (
        item["event_type"]
        == "PIPELINE_FAILED"
    )
    assert (
        item["severity"]
        == "CRITICAL"
    )
    assert (
        item["pipeline_run_id"]
        == 10002
    )


def test_get_operational_events_converts_nan_to_null(
    monkeypatch,
):
    event = build_operational_event()

    event["catalog_id"] = float("nan")
    event["version_id"] = float("nan")
    event["reference_id"] = float("nan")

    history = pd.DataFrame(
        [event]
    )

    monkeypatch.setattr(
        operational_events,
        "load_operational_event_history",
        lambda limit: history,
    )

    response = client.get(
        "/api/operational-events"
    )

    assert response.status_code == 200

    item = response.json()["items"][0]

    assert item["catalog_id"] is None
    assert item["version_id"] is None
    assert item["reference_id"] is None


def test_get_operational_events_returns_empty_history(
    monkeypatch,
):
    monkeypatch.setattr(
        operational_events,
        "load_operational_event_history",
        lambda limit: pd.DataFrame(),
    )

    response = client.get(
        "/api/operational-events"
    )

    assert response.status_code == 200

    assert response.json() == {
        "limit": 100,
        "count": 0,
        "items": [],
    }


def test_get_operational_events_rejects_invalid_limit():
    response = client.get(
        "/api/operational-events?limit=0"
    )

    assert response.status_code == 422


def test_get_operational_events_returns_500_on_repository_error(
    monkeypatch,
):
    def fake_load_history(
        limit: int,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        operational_events,
        "load_operational_event_history",
        fake_load_history,
    )

    response = client.get(
        "/api/operational-events"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": (
            "Unable to load "
            "operational event history."
        )
    }


def test_get_operational_event_detail_returns_event(
    monkeypatch,
):
    event = build_operational_event(
        operational_event_id=77,
        event_type="VALIDATION_REJECTED",
        severity="ERROR",
    )

    event["event_key"] = (
        "validation:41:rejected"
    )
    event["event_source"] = (
        "DATASET_WORKFLOW"
    )
    event["event_stage"] = (
        "VALIDATION_GATE"
    )
    event["catalog_id"] = 1
    event["version_id"] = 3
    event["pipeline_run_id"] = None
    event["reference_id"] = 41

    captured = {}

    def fake_load_event(
        operational_event_id: int,
    ):
        captured[
            "operational_event_id"
        ] = operational_event_id

        return event

    monkeypatch.setattr(
        operational_events,
        "load_operational_event",
        fake_load_event,
    )

    response = client.get(
        "/api/operational-events/77"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        captured["operational_event_id"]
        == 77
    )
    assert (
        payload["operational_event_id"]
        == 77
    )
    assert (
        payload["event_type"]
        == "VALIDATION_REJECTED"
    )
    assert (
        payload["severity"]
        == "ERROR"
    )
    assert (
        payload["event_stage"]
        == "VALIDATION_GATE"
    )
    assert payload["catalog_id"] == 1
    assert payload["version_id"] == 3
    assert payload["reference_id"] == 41


def test_get_operational_event_detail_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        operational_events,
        "load_operational_event",
        lambda operational_event_id: None,
    )

    response = client.get(
        "/api/operational-events/999"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Operational event "
            "999 was not found."
        )
    }


def test_get_operational_event_detail_rejects_invalid_id():
    response = client.get(
        "/api/operational-events/0"
    )

    assert response.status_code == 422


def test_get_operational_event_detail_returns_500_on_repository_error(
    monkeypatch,
):
    def fake_load_event(
        operational_event_id: int,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        operational_events,
        "load_operational_event",
        fake_load_event,
    )

    response = client.get(
        "/api/operational-events/77"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": (
            "Unable to load "
            "operational event."
        )
    }