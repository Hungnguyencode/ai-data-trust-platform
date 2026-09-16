from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

import src.observability.freshness_monitor as freshness_monitor

FIXED_NOW = datetime(
    2026,
    9,
    15,
    12,
    0,
    tzinfo=UTC,
)


def build_policy(
    *,
    max_age_minutes: int = 60,
    is_enabled: bool = True,
) -> dict:
    return {
        "freshness_policy_id": 10,
        "catalog_id": 1,
        "max_age_minutes": (
            max_age_minutes
        ),
        "is_enabled": is_enabled,
    }


def build_ingestion(
    *,
    minutes_old: int,
) -> dict:
    return {
        "ingestion_event_id": 20,
        "catalog_id": 1,
        "version_id": 3,
        "ingested_at": (
            FIXED_NOW
            - timedelta(
                minutes=minutes_old
            )
        ),
    }


def install_create_check(
    monkeypatch,
    captured: dict,
):
    def fake_create_freshness_check(
        **kwargs,
    ):
        captured.update(
            kwargs
        )

        return {
            "freshness_check_id": 501,
            **kwargs,
        }

    monkeypatch.setattr(
        freshness_monitor,
        "create_freshness_check",
        fake_create_freshness_check,
    )


def test_calculate_age_minutes_clamps_future_time():
    age = (
        freshness_monitor
        .calculate_age_minutes(
            latest_ingested_at=(
                FIXED_NOW
                + timedelta(
                    minutes=10
                )
            ),
            checked_at=FIXED_NOW,
        )
    )

    assert age == 0


def test_check_dataset_freshness_marks_fresh(
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(
        freshness_monitor,
        "get_freshness_policy",
        lambda catalog_id: (
            build_policy()
        ),
    )

    monkeypatch.setattr(
        freshness_monitor,
        "get_latest_ingestion_for_catalog",
        lambda catalog_id: (
            build_ingestion(
                minutes_old=30
            )
        ),
    )

    install_create_check(
        monkeypatch,
        captured,
    )

    def fail_emit(
        **kwargs,
    ):
        pytest.fail(
            "FRESH dataset must not "
            "emit an alert."
        )

    monkeypatch.setattr(
        freshness_monitor,
        "emit_operational_event",
        fail_emit,
    )

    result = (
        freshness_monitor
        .check_dataset_freshness(
            1,
            now=FIXED_NOW,
        )
    )

    assert (
        result["check"][
            "freshness_status"
        ]
        == "FRESH"
    )

    assert (
        result["check"][
            "age_minutes"
        ]
        == 30
    )

    assert (
        result[
            "operational_event"
        ]
        is None
    )

    assert (
        captured[
            "max_age_minutes"
        ]
        == 60
    )


def test_check_dataset_freshness_threshold_is_fresh(
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(
        freshness_monitor,
        "get_freshness_policy",
        lambda catalog_id: (
            build_policy()
        ),
    )

    monkeypatch.setattr(
        freshness_monitor,
        "get_latest_ingestion_for_catalog",
        lambda catalog_id: (
            build_ingestion(
                minutes_old=60
            )
        ),
    )

    install_create_check(
        monkeypatch,
        captured,
    )

    monkeypatch.setattr(
        freshness_monitor,
        "emit_operational_event",
        lambda **kwargs: pytest.fail(
            "Threshold must remain FRESH."
        ),
    )

    result = (
        freshness_monitor
        .check_dataset_freshness(
            1,
            now=FIXED_NOW,
        )
    )

    assert (
        result["check"][
            "freshness_status"
        ]
        == "FRESH"
    )


def test_check_dataset_freshness_marks_stale_and_emits_alert(
    monkeypatch,
):
    captured_check = {}
    captured_event = {}

    monkeypatch.setattr(
        freshness_monitor,
        "get_freshness_policy",
        lambda catalog_id: (
            build_policy()
        ),
    )

    monkeypatch.setattr(
        freshness_monitor,
        "get_latest_ingestion_for_catalog",
        lambda catalog_id: (
            build_ingestion(
                minutes_old=120
            )
        ),
    )

    install_create_check(
        monkeypatch,
        captured_check,
    )

    def fake_emit_operational_event(
        **kwargs,
    ):
        captured_event.update(
            kwargs
        )

        return {
            "operational_event_id": 701,
            **kwargs,
        }

    monkeypatch.setattr(
        freshness_monitor,
        "emit_operational_event",
        fake_emit_operational_event,
    )

    result = (
        freshness_monitor
        .check_dataset_freshness(
            1,
            now=FIXED_NOW,
        )
    )

    assert (
        result["check"][
            "freshness_status"
        ]
        == "STALE"
    )

    assert (
        result["check"][
            "age_minutes"
        ]
        == 120
    )

    assert (
        captured_event[
            "event_key"
        ]
        == "freshness:1:20:stale"
    )

    assert (
        captured_event[
            "event_type"
        ]
        == "DATASET_FRESHNESS_BREACH"
    )

    assert (
        captured_event[
            "severity"
        ]
        == "WARNING"
    )

    assert (
        captured_event[
            "event_source"
        ]
        == "DATA_OBSERVABILITY"
    )

    assert (
        captured_event[
            "event_stage"
        ]
        == "FRESHNESS_MONITOR"
    )

    assert (
        captured_event[
            "version_id"
        ]
        == 3
    )

    assert (
        captured_event[
            "reference_id"
        ]
        == 501
    )

    assert (
        result[
            "operational_event"
        ][
            "operational_event_id"
        ]
        == 701
    )


def test_check_dataset_freshness_handles_no_data(
    monkeypatch,
):
    captured = {}

    monkeypatch.setattr(
        freshness_monitor,
        "get_freshness_policy",
        lambda catalog_id: (
            build_policy()
        ),
    )

    monkeypatch.setattr(
        freshness_monitor,
        "get_latest_ingestion_for_catalog",
        lambda catalog_id: None,
    )

    install_create_check(
        monkeypatch,
        captured,
    )

    result = (
        freshness_monitor
        .check_dataset_freshness(
            1,
            now=FIXED_NOW,
        )
    )

    assert (
        result["check"][
            "freshness_status"
        ]
        == "NO_DATA"
    )

    assert (
        result["check"][
            "age_minutes"
        ]
        is None
    )

    assert (
        result["check"][
            "version_id"
        ]
        is None
    )

    assert (
        result[
            "operational_event"
        ]
        is None
    )


def test_check_dataset_freshness_requires_policy(
    monkeypatch,
):
    monkeypatch.setattr(
        freshness_monitor,
        "get_freshness_policy",
        lambda catalog_id: None,
    )

    with pytest.raises(
        ValueError,
        match="No freshness policy",
    ):
        freshness_monitor.check_dataset_freshness(
            1,
            now=FIXED_NOW,
        )


def test_check_dataset_freshness_rejects_disabled_policy(
    monkeypatch,
):
    monkeypatch.setattr(
        freshness_monitor,
        "get_freshness_policy",
        lambda catalog_id: (
            build_policy(
                is_enabled=False
            )
        ),
    )

    with pytest.raises(
        ValueError,
        match="disabled",
    ):
        freshness_monitor.check_dataset_freshness(
            1,
            now=FIXED_NOW,
        )


def test_check_enabled_freshness_policies_empty(
    monkeypatch,
):
    monkeypatch.setattr(
        freshness_monitor,
        "get_enabled_freshness_policies",
        lambda: pd.DataFrame(),
    )

    result = (
        freshness_monitor
        .check_enabled_freshness_policies(
            now=FIXED_NOW,
        )
    )

    assert result[
        "policy_count"
    ] == 0

    assert result[
        "checked_count"
    ] == 0

    assert result[
        "failed_count"
    ] == 0

    assert result[
        "fresh_count"
    ] == 0

    assert result[
        "stale_count"
    ] == 0

    assert result[
        "no_data_count"
    ] == 0

    assert result["results"] == []
    assert result["errors"] == []


def test_check_enabled_freshness_policies_checks_all_and_isolates_errors(
    monkeypatch,
):
    policies = pd.DataFrame(
        [
            {
                "catalog_id": 1,
            },
            {
                "catalog_id": 2,
            },
            {
                "catalog_id": 3,
            },
        ]
    )

    monkeypatch.setattr(
        freshness_monitor,
        "get_enabled_freshness_policies",
        lambda: policies,
    )

    checked_catalog_ids = []

    def fake_check_dataset_freshness(
        catalog_id,
        *,
        now=None,
    ):
        checked_catalog_ids.append(
            catalog_id
        )

        if catalog_id == 2:
            raise RuntimeError(
                "simulated failure"
            )

        status = (
            "STALE"
            if catalog_id == 3
            else "FRESH"
        )

        return {
            "policy": {
                "catalog_id": (
                    catalog_id
                ),
            },
            "check": {
                "catalog_id": (
                    catalog_id
                ),
                "freshness_status": (
                    status
                ),
            },
            "operational_event": None,
        }

    monkeypatch.setattr(
        freshness_monitor,
        "check_dataset_freshness",
        fake_check_dataset_freshness,
    )

    result = (
        freshness_monitor
        .check_enabled_freshness_policies(
            now=FIXED_NOW,
        )
    )

    assert checked_catalog_ids == [
        1,
        2,
        3,
    ]

    assert result[
        "policy_count"
    ] == 3

    assert result[
        "checked_count"
    ] == 2

    assert result[
        "failed_count"
    ] == 1

    assert result[
        "fresh_count"
    ] == 1

    assert result[
        "stale_count"
    ] == 1

    assert result[
        "no_data_count"
    ] == 0

    assert (
        result["errors"][0][
            "catalog_id"
        ]
        == 2
    )

    assert (
        result["errors"][0][
            "error_type"
        ]
        == "RuntimeError"
    )

    assert (
        result["errors"][0][
            "error_message"
        ]
        == "simulated failure"
    )