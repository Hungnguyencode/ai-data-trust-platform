from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

import src.observability.volume_monitor as volume_monitor


def build_policy(
    *,
    is_enabled: bool = True,
) -> dict[str, Any]:
    return {
        "volume_policy_id": 10,
        "catalog_id": 1,
        "drop_threshold_pct": 25.0,
        "spike_threshold_pct": 50.0,
        "is_enabled": is_enabled,
    }


def build_ingestion_frame(
    *,
    current_rows: int | None,
    baseline_rows: int | None = None,
) -> pd.DataFrame:
    rows: list[
        dict[str, Any]
    ] = [
        {
            "ingestion_event_id": 200,
            "catalog_id": 1,
            "version_id": 20,
            "version_number": 2,
            "row_count": current_rows,
        }
    ]

    if baseline_rows is not None:
        rows.append(
            {
                "ingestion_event_id": 100,
                "catalog_id": 1,
                "version_id": 10,
                "version_number": 1,
                "row_count": baseline_rows,
            }
        )

    return pd.DataFrame(
        rows
    )


def test_check_dataset_volume_rejects_missing_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        volume_monitor,
        "get_volume_policy",
        lambda catalog_id: None,
    )

    with pytest.raises(
        ValueError,
        match="No volume policy",
    ):
        volume_monitor.check_dataset_volume(
            1
        )


def test_check_dataset_volume_rejects_disabled_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        volume_monitor,
        "get_volume_policy",
        lambda catalog_id: build_policy(
            is_enabled=False
        ),
    )

    def fail_recent_ingestions(
        catalog_id: int,
        *,
        limit: int,
    ) -> pd.DataFrame:
        raise AssertionError(
            "ingestion lookup must not occur"
        )

    monkeypatch.setattr(
        volume_monitor,
        "get_recent_ingestions_for_catalog",
        fail_recent_ingestions,
    )

    with pytest.raises(
        ValueError,
        match="disabled",
    ):
        volume_monitor.check_dataset_volume(
            1
        )


def test_check_dataset_volume_rejects_missing_ingestion_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        volume_monitor,
        "get_volume_policy",
        lambda catalog_id: build_policy(),
    )

    monkeypatch.setattr(
        volume_monitor,
        "get_recent_ingestions_for_catalog",
        lambda catalog_id, limit=2: (
            pd.DataFrame()
        ),
    )

    with pytest.raises(
        ValueError,
        match="No ingestion history",
    ):
        volume_monitor.check_dataset_volume(
            1
        )


def test_first_ingestion_is_no_baseline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        volume_monitor,
        "get_volume_policy",
        lambda catalog_id: build_policy(),
    )

    monkeypatch.setattr(
        volume_monitor,
        "get_recent_ingestions_for_catalog",
        lambda catalog_id, limit=2: (
            build_ingestion_frame(
                current_rows=100
            )
        ),
    )

    captured: dict[
        str,
        Any,
    ] = {}

    def fake_create_volume_check(
        **kwargs: Any,
    ) -> dict[str, Any]:
        captured.update(
            kwargs
        )

        return {
            "volume_check_id": 1,
            **kwargs,
        }

    monkeypatch.setattr(
        volume_monitor,
        "create_volume_check",
        fake_create_volume_check,
    )

    result = (
        volume_monitor
        .check_dataset_volume(
            1
        )
    )

    assert result[
        "check"
    ][
        "volume_status"
    ] == "NO_BASELINE"

    assert captured[
        "baseline_ingestion_event_id"
    ] is None

    assert captured[
        "baseline_version_id"
    ] is None

    assert captured[
        "baseline_row_count"
    ] is None

    assert captured[
        "row_change_pct"
    ] is None


def test_volume_normal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        volume_monitor,
        "get_volume_policy",
        lambda catalog_id: build_policy(),
    )

    monkeypatch.setattr(
        volume_monitor,
        "get_recent_ingestions_for_catalog",
        lambda catalog_id, limit=2: (
            build_ingestion_frame(
                current_rows=110,
                baseline_rows=100,
            )
        ),
    )

    captured: dict[
        str,
        Any,
    ] = {}

    def fake_create_volume_check(
        **kwargs: Any,
    ) -> dict[str, Any]:
        captured.update(
            kwargs
        )

        return {
            "volume_check_id": 19,
            **kwargs,
        }

    monkeypatch.setattr(
        volume_monitor,
        "create_volume_check",
        fake_create_volume_check,
    )

    def fail_emit_operational_event(
        **kwargs: Any,
    ) -> None:
        raise AssertionError(
            "NORMAL volume must not emit "
            "an operational alert."
        )

    monkeypatch.setattr(
        volume_monitor,
        "emit_operational_event",
        fail_emit_operational_event,
    )

    result = (
        volume_monitor
        .check_dataset_volume(
            1
        )
    )

    assert captured[
        "row_change_pct"
    ] == 10.0

    assert captured[
        "volume_status"
    ] == "NORMAL"

    assert result[
        "operational_event"
    ] is None


def test_volume_drop_at_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        volume_monitor,
        "get_volume_policy",
        lambda catalog_id: build_policy(),
    )

    monkeypatch.setattr(
        volume_monitor,
        "get_recent_ingestions_for_catalog",
        lambda catalog_id, limit=2: (
            build_ingestion_frame(
                current_rows=75,
                baseline_rows=100,
            )
        ),
    )

    captured: dict[
        str,
        Any,
    ] = {}

    def fake_create_volume_check(
        **kwargs: Any,
    ) -> dict[str, Any]:
        captured.update(
            kwargs
        )

        return {
            "volume_check_id": 20,
            **kwargs,
        }

    monkeypatch.setattr(
        volume_monitor,
        "create_volume_check",
        fake_create_volume_check,
    )

    emitted: dict[
        str,
        Any,
    ] = {}

    def fake_emit_operational_event(
        **kwargs: Any,
    ) -> dict[str, Any]:
        emitted.update(
            kwargs
        )

        return {
            "operational_event_id": 30,
            **kwargs,
        }

    monkeypatch.setattr(
        volume_monitor,
        "emit_operational_event",
        fake_emit_operational_event,
    )

    result = (
        volume_monitor
        .check_dataset_volume(
            1
        )
    )

    assert captured[
        "row_change_pct"
    ] == -25.0

    assert captured[
        "volume_status"
    ] == "DROP"

    assert emitted[
        "event_key"
    ] == "volume:1:200:drop"

    assert emitted[
        "event_type"
    ] == "DATASET_VOLUME_BREACH"

    assert emitted[
        "severity"
    ] == "WARNING"

    assert emitted[
        "event_stage"
    ] == "VOLUME_MONITOR"

    assert emitted[
        "catalog_id"
    ] == 1

    assert emitted[
        "version_id"
    ] == 20

    assert emitted[
        "reference_id"
    ] == 20

    assert emitted[
        "detail"
    ][
        "row_change_pct"
    ] == -25.0

    assert result[
        "operational_event"
    ][
        "operational_event_id"
    ] == 30


def test_volume_spike_at_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        volume_monitor,
        "get_volume_policy",
        lambda catalog_id: build_policy(),
    )

    monkeypatch.setattr(
        volume_monitor,
        "get_recent_ingestions_for_catalog",
        lambda catalog_id, limit=2: (
            build_ingestion_frame(
                current_rows=150,
                baseline_rows=100,
            )
        ),
    )

    captured: dict[
        str,
        Any,
    ] = {}

    def fake_create_volume_check(
        **kwargs: Any,
    ) -> dict[str, Any]:
        captured.update(
            kwargs
        )

        return {
            "volume_check_id": 21,
            **kwargs,
        }

    monkeypatch.setattr(
        volume_monitor,
        "create_volume_check",
        fake_create_volume_check,
    )

    emitted: dict[
        str,
        Any,
    ] = {}

    def fake_emit_operational_event(
        **kwargs: Any,
    ) -> dict[str, Any]:
        emitted.update(
            kwargs
        )

        return {
            "operational_event_id": 31,
            **kwargs,
        }

    monkeypatch.setattr(
        volume_monitor,
        "emit_operational_event",
        fake_emit_operational_event,
    )

    result = (
        volume_monitor
        .check_dataset_volume(
            1
        )
    )

    assert captured[
        "row_change_pct"
    ] == 50.0

    assert captured[
        "volume_status"
    ] == "SPIKE"

    assert emitted[
        "event_key"
    ] == "volume:1:200:spike"

    assert emitted[
        "event_type"
    ] == "DATASET_VOLUME_BREACH"

    assert emitted[
        "severity"
    ] == "WARNING"

    assert emitted[
        "event_stage"
    ] == "VOLUME_MONITOR"

    assert emitted[
        "reference_id"
    ] == 21

    assert emitted[
        "detail"
    ][
        "row_change_pct"
    ] == 50.0

    assert result[
        "operational_event"
    ][
        "operational_event_id"
    ] == 31


def test_zero_baseline_and_zero_current_is_normal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status = (
        volume_monitor
        .classify_volume_status(
            baseline_row_count=0,
            current_row_count=0,
            drop_threshold_pct=25,
            spike_threshold_pct=50,
        )
    )

    change = (
        volume_monitor
        .calculate_row_change_pct(
            baseline_row_count=0,
            current_row_count=0,
        )
    )

    assert change == 0.0
    assert status == "NORMAL"


def test_zero_baseline_and_positive_current_is_spike(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status = (
        volume_monitor
        .classify_volume_status(
            baseline_row_count=0,
            current_row_count=50,
            drop_threshold_pct=25,
            spike_threshold_pct=50,
        )
    )

    change = (
        volume_monitor
        .calculate_row_change_pct(
            baseline_row_count=0,
            current_row_count=50,
        )
    )

    assert change is None
    assert status == "SPIKE"


def test_missing_current_row_count_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        volume_monitor,
        "get_volume_policy",
        lambda catalog_id: build_policy(),
    )

    monkeypatch.setattr(
        volume_monitor,
        "get_recent_ingestions_for_catalog",
        lambda catalog_id, limit=2: (
            build_ingestion_frame(
                current_rows=None,
                baseline_rows=100,
            )
        ),
    )

    def fail_create(
        **kwargs: Any,
    ) -> dict[str, Any]:
        raise AssertionError(
            "volume check must not be persisted"
        )

    monkeypatch.setattr(
        volume_monitor,
        "create_volume_check",
        fail_create,
    )

    with pytest.raises(
        ValueError,
        match="row_count is required",
    ):
        volume_monitor.check_dataset_volume(
            1
        )


def test_check_enabled_volume_policies_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        volume_monitor,
        "get_enabled_volume_policies",
        lambda: pd.DataFrame(),
    )

    result = (
        volume_monitor
        .check_enabled_volume_policies()
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
        "normal_count"
    ] == 0

    assert result[
        "drop_count"
    ] == 0

    assert result[
        "spike_count"
    ] == 0

    assert result[
        "no_baseline_count"
    ] == 0

    assert result["results"] == []
    assert result["errors"] == []


def test_check_enabled_volume_policies_checks_all_and_isolates_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policies = pd.DataFrame(
        [
            {"catalog_id": 1},
            {"catalog_id": 2},
            {"catalog_id": 3},
            {"catalog_id": 4},
            {"catalog_id": 5},
        ]
    )

    monkeypatch.setattr(
        volume_monitor,
        "get_enabled_volume_policies",
        lambda: policies,
    )

    checked_catalog_ids: list[int] = []

    statuses = {
        1: "NORMAL",
        2: "DROP",
        3: "SPIKE",
        4: "NO_BASELINE",
    }

    def fake_check_dataset_volume(
        catalog_id: int,
    ) -> dict[str, Any]:
        checked_catalog_ids.append(
            catalog_id
        )

        if catalog_id == 5:
            raise RuntimeError(
                "simulated failure"
            )

        return {
            "policy": {
                "catalog_id": catalog_id,
            },
            "check": {
                "catalog_id": catalog_id,
                "volume_status": (
                    statuses[catalog_id]
                ),
            },
            "operational_event": None,
        }

    monkeypatch.setattr(
        volume_monitor,
        "check_dataset_volume",
        fake_check_dataset_volume,
    )

    result = (
        volume_monitor
        .check_enabled_volume_policies()
    )

    assert checked_catalog_ids == [
        1,
        2,
        3,
        4,
        5,
    ]

    assert result[
        "policy_count"
    ] == 5

    assert result[
        "checked_count"
    ] == 4

    assert result[
        "failed_count"
    ] == 1

    assert result[
        "normal_count"
    ] == 1

    assert result[
        "drop_count"
    ] == 1

    assert result[
        "spike_count"
    ] == 1

    assert result[
        "no_baseline_count"
    ] == 1

    assert result[
        "errors"
    ][0][
        "catalog_id"
    ] == 5

    assert result[
        "errors"
    ][0][
        "error_type"
    ] == "RuntimeError"

    assert result[
        "errors"
    ][0][
        "error_message"
    ] == "simulated failure"