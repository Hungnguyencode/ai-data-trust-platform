from __future__ import annotations

from datetime import datetime

import pandas as pd
from fastapi.testclient import TestClient

import api.routes.pipeline_runs as pipeline_runs
from api.main import app

client = TestClient(app)


def build_pipeline_run(
    *,
    pipeline_run_id: int = 7,
    run_status: str = "FAILED",
) -> dict:
    started_at = datetime(
        2026,
        9,
        13,
        13,
        11,
        10,
    )

    finished_at = datetime(
        2026,
        9,
        13,
        13,
        11,
        58,
    )

    return {
        "pipeline_run_id": pipeline_run_id,
        "dag_id": "ai_data_trust_pipeline",
        "airflow_run_id": "manual__test",
        "source_path": "/app/data/test.csv",
        "run_status": run_status,
        "attempt_count": 3,
        "catalog_id": None,
        "version_id": None,
        "validation_status": None,
        "governance_decision": None,
        "trust_score": None,
        "lifecycle_state": None,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": 48000,
        "error_type": "DatasetWorkflowError",
        "error_message": "Intentional test failure.",
        "created_at": started_at,
        "updated_at": finished_at,
    }


def test_get_pipeline_runs_returns_history(
    monkeypatch,
):
    run = build_pipeline_run()

    history = pd.DataFrame(
        [run]
    )

    captured = {}

    def fake_load_pipeline_run_history(
        limit: int,
    ):
        captured["limit"] = limit
        return history

    monkeypatch.setattr(
        pipeline_runs,
        "load_pipeline_run_history",
        fake_load_pipeline_run_history,
    )

    response = client.get(
        "/api/pipeline-runs?limit=25"
    )

    assert response.status_code == 200

    payload = response.json()

    assert captured["limit"] == 25
    assert payload["limit"] == 25
    assert payload["count"] == 1
    assert len(payload["items"]) == 1

    item = payload["items"][0]

    assert item["pipeline_run_id"] == 7
    assert item["run_status"] == "FAILED"
    assert item["attempt_count"] == 3
    assert (
        item["error_type"]
        == "DatasetWorkflowError"
    )


def test_get_pipeline_runs_converts_nan_to_null(
    monkeypatch,
):
    run = build_pipeline_run()

    run["catalog_id"] = float("nan")
    run["version_id"] = float("nan")
    run["trust_score"] = float("nan")

    history = pd.DataFrame(
        [run]
    )

    monkeypatch.setattr(
        pipeline_runs,
        "load_pipeline_run_history",
        lambda limit: history,
    )

    response = client.get(
        "/api/pipeline-runs"
    )

    assert response.status_code == 200

    item = response.json()["items"][0]

    assert item["catalog_id"] is None
    assert item["version_id"] is None
    assert item["trust_score"] is None


def test_get_pipeline_runs_returns_empty_history(
    monkeypatch,
):
    monkeypatch.setattr(
        pipeline_runs,
        "load_pipeline_run_history",
        lambda limit: pd.DataFrame(),
    )

    response = client.get(
        "/api/pipeline-runs"
    )

    assert response.status_code == 200

    assert response.json() == {
        "limit": 50,
        "count": 0,
        "items": [],
    }


def test_get_pipeline_runs_rejects_invalid_limit():
    response = client.get(
        "/api/pipeline-runs?limit=0"
    )

    assert response.status_code == 422


def test_get_pipeline_runs_returns_500_on_repository_error(
    monkeypatch,
):
    def fake_load_pipeline_run_history(
        limit: int,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        pipeline_runs,
        "load_pipeline_run_history",
        fake_load_pipeline_run_history,
    )

    response = client.get(
        "/api/pipeline-runs"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": (
            "Unable to load "
            "pipeline run history."
        )
    }


def test_get_pipeline_run_detail_returns_run(
    monkeypatch,
):
    run = build_pipeline_run(
        pipeline_run_id=6,
        run_status="SUCCESS",
    )

    run["attempt_count"] = 1
    run["catalog_id"] = 1
    run["version_id"] = 2
    run["validation_status"] = "ACCEPTED"
    run["governance_decision"] = "REJECTED"
    run["trust_score"] = 100.0
    run["lifecycle_state"] = "VALIDATED"
    run["error_type"] = None
    run["error_message"] = None

    captured = {}

    def fake_load_pipeline_run(
        pipeline_run_id: int,
    ):
        captured[
            "pipeline_run_id"
        ] = pipeline_run_id

        return run

    monkeypatch.setattr(
        pipeline_runs,
        "load_pipeline_run",
        fake_load_pipeline_run,
    )

    response = client.get(
        "/api/pipeline-runs/6"
    )

    assert response.status_code == 200

    payload = response.json()

    assert captured["pipeline_run_id"] == 6
    assert payload["pipeline_run_id"] == 6
    assert payload["run_status"] == "SUCCESS"
    assert payload["attempt_count"] == 1
    assert payload["catalog_id"] == 1
    assert payload["version_id"] == 2
    assert payload["trust_score"] == 100.0
    assert (
        payload["lifecycle_state"]
        == "VALIDATED"
    )


def test_get_pipeline_run_detail_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        pipeline_runs,
        "load_pipeline_run",
        lambda pipeline_run_id: None,
    )

    response = client.get(
        "/api/pipeline-runs/999"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Pipeline run 999 "
            "was not found."
        )
    }


def test_get_pipeline_run_detail_rejects_invalid_id():
    response = client.get(
        "/api/pipeline-runs/0"
    )

    assert response.status_code == 422


def test_get_pipeline_run_detail_returns_500_on_repository_error(
    monkeypatch,
):
    def fake_load_pipeline_run(
        pipeline_run_id: int,
    ):
        raise RuntimeError(
            "database unavailable"
        )

    monkeypatch.setattr(
        pipeline_runs,
        "load_pipeline_run",
        fake_load_pipeline_run,
    )

    response = client.get(
        "/api/pipeline-runs/7"
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": (
            "Unable to load "
            "pipeline run."
        )
    }