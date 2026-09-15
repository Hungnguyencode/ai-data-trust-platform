from __future__ import annotations

import src.observability.operational_events as operational_events


def test_emit_operational_event_delegates_to_repository(
    monkeypatch,
):
    calls = []

    def fake_create_operational_event(
        **kwargs,
    ):
        calls.append(kwargs)

        return {
            "operational_event_id": 7,
            **kwargs,
        }

    monkeypatch.setattr(
        operational_events,
        "create_operational_event",
        fake_create_operational_event,
    )

    result = operational_events.emit_operational_event(
        event_key="validation:42:rejected",
        event_type="VALIDATION_REJECTED",
        severity="ERROR",
        event_source="DATASET_WORKFLOW",
        event_stage="VALIDATION_GATE",
        catalog_id=1,
        version_id=2,
        reference_id=42,
        message="Dataset failed Validation Gate.",
        detail={
            "validation_status": "REJECTED",
        },
    )

    assert result is not None
    assert result["operational_event_id"] == 7

    assert len(calls) == 1

    assert calls[0]["event_key"] == (
        "validation:42:rejected"
    )
    assert calls[0]["severity"] == "ERROR"
    assert calls[0]["catalog_id"] == 1
    assert calls[0]["version_id"] == 2
    assert calls[0]["reference_id"] == 42


def test_emit_operational_event_is_best_effort(
    monkeypatch,
):
    def fail_create_operational_event(
        **kwargs,
    ):
        raise RuntimeError(
            "SQL Server unavailable"
        )

    monkeypatch.setattr(
        operational_events,
        "create_operational_event",
        fail_create_operational_event,
    )

    result = operational_events.emit_operational_event(
        event_key="governance:99:rejected",
        event_type="GOVERNANCE_REJECTED",
        severity="ERROR",
        event_source="DATASET_WORKFLOW",
        event_stage="GOVERNANCE",
        message="Governance rejected dataset.",
    )

    assert result is None


def test_emit_pipeline_failed_event_builds_expected_event(
    monkeypatch,
):
    calls = []

    def fake_emit_operational_event(
        **kwargs,
    ):
        calls.append(kwargs)

        return {
            "operational_event_id": 88,
            **kwargs,
        }

    monkeypatch.setattr(
        operational_events,
        "emit_operational_event",
        fake_emit_operational_event,
    )

    error = RuntimeError(
        "dataset workflow exploded"
    )

    result = (
        operational_events.emit_pipeline_failed_event(
            pipeline_run_id=51,
            event_stage="PLATFORM_WORKFLOW",
            error=error,
        )
    )

    assert result is not None
    assert result[
        "operational_event_id"
    ] == 88

    assert len(calls) == 1

    event = calls[0]

    assert event["event_key"] == (
        "pipeline-run:51:failed"
    )

    assert (
        event["event_type"]
        == "PIPELINE_FAILED"
    )

    assert (
        event["severity"]
        == "CRITICAL"
    )

    assert (
        event["event_source"]
        == "AIRFLOW"
    )

    assert (
        event["event_stage"]
        == "PLATFORM_WORKFLOW"
    )

    assert (
        event["pipeline_run_id"]
        == 51
    )

    assert event["detail"] == {
        "error_type": "RuntimeError",
        "error_message": (
            "dataset workflow exploded"
        ),
    }