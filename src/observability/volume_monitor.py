from __future__ import annotations

from math import isfinite
from typing import Any

import pandas as pd

from database.repositories.volume_repository import (
    create_volume_check,
    get_recent_ingestions_for_catalog,
    get_volume_policy,
)
from src.observability.operational_events import (
    emit_operational_event,
)


def calculate_row_change_pct(
    *,
    baseline_row_count: int,
    current_row_count: int,
) -> float | None:
    baseline = int(
        baseline_row_count
    )
    current = int(
        current_row_count
    )

    if baseline < 0:
        raise ValueError(
            "baseline_row_count must be greater "
            "than or equal to 0."
        )

    if current < 0:
        raise ValueError(
            "current_row_count must be greater "
            "than or equal to 0."
        )

    if baseline == 0:
        if current == 0:
            return 0.0

        # Percentage growth from zero is undefined.
        return None

    change_pct = (
        (current - baseline)
        / baseline
        * 100.0
    )

    return round(
        change_pct,
        4,
    )


def classify_volume_status(
    *,
    baseline_row_count: int | None,
    current_row_count: int,
    drop_threshold_pct: float,
    spike_threshold_pct: float,
    row_change_pct: float | None = None,
) -> str:
    current = int(
        current_row_count
    )

    if current < 0:
        raise ValueError(
            "current_row_count must be greater "
            "than or equal to 0."
        )

    drop_threshold = float(
        drop_threshold_pct
    )
    spike_threshold = float(
        spike_threshold_pct
    )

    if (
        not isfinite(drop_threshold)
        or drop_threshold <= 0
    ):
        raise ValueError(
            "drop_threshold_pct must be greater "
            "than 0."
        )

    if (
        not isfinite(spike_threshold)
        or spike_threshold <= 0
    ):
        raise ValueError(
            "spike_threshold_pct must be greater "
            "than 0."
        )

    if baseline_row_count is None:
        return "NO_BASELINE"

    baseline = int(
        baseline_row_count
    )

    if baseline < 0:
        raise ValueError(
            "baseline_row_count must be greater "
            "than or equal to 0."
        )

    if baseline == 0:
        if current == 0:
            return "NORMAL"

        return "SPIKE"

    change_pct = (
        calculate_row_change_pct(
            baseline_row_count=baseline,
            current_row_count=current,
        )
        if row_change_pct is None
        else float(row_change_pct)
    )

    if not isfinite(change_pct):
        raise ValueError(
            "row_change_pct must be finite."
        )

    if change_pct <= -drop_threshold:
        return "DROP"

    if change_pct >= spike_threshold:
        return "SPIKE"

    return "NORMAL"


def _required_int(
    row: pd.Series,
    field_name: str,
) -> int:
    if (
        field_name not in row
        or pd.isna(
            row[field_name]
        )
    ):
        raise ValueError(
            f"{field_name} is required."
        )

    value = int(
        row[field_name]
    )

    if value <= 0:
        raise ValueError(
            f"{field_name} must be greater than 0."
        )

    return value


def _required_row_count(
    row: pd.Series,
) -> int:
    if (
        "row_count" not in row
        or pd.isna(
            row["row_count"]
        )
    ):
        raise ValueError(
            "row_count is required for "
            "volume monitoring."
        )

    row_count = int(
        row["row_count"]
    )

    if row_count < 0:
        raise ValueError(
            "row_count must be greater "
            "than or equal to 0."
        )

    return row_count


def check_dataset_volume(
    catalog_id: int,
) -> dict[str, Any]:
    policy = get_volume_policy(
        catalog_id
    )

    if policy is None:
        raise ValueError(
            "No volume policy for "
            f"catalog_id={catalog_id}."
        )

    if not bool(
        policy["is_enabled"]
    ):
        raise ValueError(
            "Volume monitoring is disabled for "
            f"catalog_id={catalog_id}."
        )

    recent_ingestions = (
        get_recent_ingestions_for_catalog(
            catalog_id,
            limit=2,
        )
    )

    if recent_ingestions.empty:
        raise ValueError(
            "No ingestion history for "
            f"catalog_id={catalog_id}."
        )

    current = (
        recent_ingestions.iloc[0]
    )

    current_ingestion_event_id = (
        _required_int(
            current,
            "ingestion_event_id",
        )
    )
    current_version_id = (
        _required_int(
            current,
            "version_id",
        )
    )
    current_row_count = (
        _required_row_count(
            current
        )
    )

    baseline_ingestion_event_id = None
    baseline_version_id = None
    baseline_row_count = None

    if len(recent_ingestions) >= 2:
        baseline = (
            recent_ingestions.iloc[1]
        )

        baseline_ingestion_event_id = (
            _required_int(
                baseline,
                "ingestion_event_id",
            )
        )
        baseline_version_id = (
            _required_int(
                baseline,
                "version_id",
            )
        )
        baseline_row_count = (
            _required_row_count(
                baseline
            )
        )

    row_change_pct = (
        None
        if baseline_row_count is None
        else calculate_row_change_pct(
            baseline_row_count=(
                baseline_row_count
            ),
            current_row_count=(
                current_row_count
            ),
        )
    )

    drop_threshold_pct = float(
        policy["drop_threshold_pct"]
    )
    spike_threshold_pct = float(
        policy["spike_threshold_pct"]
    )

    volume_status = (
        classify_volume_status(
            baseline_row_count=(
                baseline_row_count
            ),
            current_row_count=(
                current_row_count
            ),
            drop_threshold_pct=(
                drop_threshold_pct
            ),
            spike_threshold_pct=(
                spike_threshold_pct
            ),
            row_change_pct=(
                row_change_pct
            ),
        )
    )

    check = create_volume_check(
        volume_policy_id=int(
            policy["volume_policy_id"]
        ),
        catalog_id=int(
            policy["catalog_id"]
        ),
        ingestion_event_id=(
            current_ingestion_event_id
        ),
        version_id=(
            current_version_id
        ),
        baseline_ingestion_event_id=(
            baseline_ingestion_event_id
        ),
        baseline_version_id=(
            baseline_version_id
        ),
        baseline_row_count=(
            baseline_row_count
        ),
        current_row_count=(
            current_row_count
        ),
        drop_threshold_pct=(
            drop_threshold_pct
        ),
        spike_threshold_pct=(
            spike_threshold_pct
        ),
        row_change_pct=(
            row_change_pct
        ),
        volume_status=(
            volume_status
        ),
    )

    operational_event = None

    if volume_status in {
        "DROP",
        "SPIKE",
    }:
        volume_check_id = int(
            check["volume_check_id"]
        )

        operational_event = (
            emit_operational_event(
                event_key=(
                    "volume:"
                    f"{catalog_id}:"
                    f"{current_ingestion_event_id}:"
                    f"{volume_status.lower()}"
                ),
                event_type=(
                    "DATASET_VOLUME_BREACH"
                ),
                severity="WARNING",
                event_source=(
                    "DATA_OBSERVABILITY"
                ),
                event_stage=(
                    "VOLUME_MONITOR"
                ),
                catalog_id=catalog_id,
                version_id=(
                    current_version_id
                ),
                reference_id=(
                    volume_check_id
                ),
                message=(
                    "Dataset row volume "
                    f"{volume_status.lower()} "
                    "threshold was breached."
                ),
                detail={
                    "volume_check_id": (
                        volume_check_id
                    ),
                    "ingestion_event_id": (
                        current_ingestion_event_id
                    ),
                    "baseline_ingestion_event_id": (
                        baseline_ingestion_event_id
                    ),
                    "baseline_row_count": (
                        baseline_row_count
                    ),
                    "current_row_count": (
                        current_row_count
                    ),
                    "row_change_pct": (
                        row_change_pct
                    ),
                    "drop_threshold_pct": (
                        drop_threshold_pct
                    ),
                    "spike_threshold_pct": (
                        spike_threshold_pct
                    ),
                    "volume_status": (
                        volume_status
                    ),
                },
            )
        )

    return {
        "policy": policy,
        "check": check,
        "operational_event": (
            operational_event
        ),
    }

