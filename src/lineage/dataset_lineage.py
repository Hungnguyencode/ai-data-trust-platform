from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

REQUIRED_VERSION_FIELDS = {
    "catalog_id",
    "version_id",
    "version_number",
    "file_name",
    "content_sha256",
    "lifecycle_state",
}


def _to_dict(
    value: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    return dict(value)


def _timestamp_sort_value(
    value: Any,
) -> float:
    if value is None:
        return float("-inf")

    if isinstance(value, datetime):
        parsed = value
    else:
        text_value = str(value).strip()

        if text_value.endswith("Z"):
            text_value = f"{text_value[:-1]}+00:00"

        try:
            parsed = datetime.fromisoformat(text_value)
        except ValueError:
            return float("-inf")

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.timestamp()


def build_lineage_timeline(
    *,
    ingestions: Sequence[Mapping[str, Any]],
    validations: Sequence[Mapping[str, Any]],
    lifecycle_events: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build one chronological lineage timeline.

    Timeline event types:
    - INGESTION
    - VALIDATION
    - LIFECYCLE
    """

    timeline: list[dict[str, Any]] = []

    for ingestion in ingestions:
        row = _to_dict(ingestion)

        is_new_version = bool(
            row.get("is_new_version")
        )

        event_status = (
            "NEW_VERSION"
            if is_new_version
            else "REINGESTED"
        )

        timeline.append(
            {
                "event_type": "INGESTION",
                "event_status": event_status,
                "occurred_at": row.get(
                    "ingested_at"
                ),
                "reference_id": row.get(
                    "ingestion_event_id"
                ),
                "artifact_path": row.get(
                    "raw_path"
                ),
                "detail": (
                    "Dataset content registered as a new version."
                    if is_new_version
                    else "Existing dataset version was ingested again."
                ),
            }
        )

    for validation in validations:
        row = _to_dict(validation)

        validation_status = str(
            row.get(
                "validation_status",
                "UNKNOWN",
            )
        ).upper()

        timeline.append(
            {
                "event_type": "VALIDATION",
                "event_status": validation_status,
                "occurred_at": row.get(
                    "validated_at"
                ),
                "reference_id": row.get(
                    "validation_id"
                ),
                "artifact_path": row.get(
                    "artifact_path"
                ),
                "detail": (
                    "policy="
                    f"{row.get('policy_version', 'N/A')}; "
                    "high_issues="
                    f"{row.get('high_issues', 0)}; "
                    "blocking_issues="
                    f"{row.get('blocking_issue_count', 0)}"
                ),
            }
        )

    for lifecycle_event in lifecycle_events:
        row = _to_dict(
            lifecycle_event
        )

        from_state = (
            str(row.get("from_state"))
            if row.get("from_state") is not None
            else "NONE"
        )

        to_state = str(
            row.get(
                "to_state",
                "UNKNOWN",
            )
        )

        timeline.append(
            {
                "event_type": "LIFECYCLE",
                "event_status": (
                    f"{from_state} -> {to_state}"
                ),
                "occurred_at": row.get(
                    "changed_at"
                ),
                "reference_id": row.get(
                    "lifecycle_event_id"
                ),
                "artifact_path": None,
                "detail": row.get(
                    "reason"
                ),
            }
        )

    timeline.sort(
        key=lambda item: (
            _timestamp_sort_value(
                item.get("occurred_at")
            ),
            str(
                item.get(
                    "event_type",
                    "",
                )
            ),
            str(
                item.get(
                    "reference_id",
                    "",
                )
            ),
        )
    )

    return timeline


def build_version_lineage(
    *,
    version: Mapping[str, Any],
    ingestions: Sequence[Mapping[str, Any]],
    validations: Sequence[Mapping[str, Any]],
    lifecycle_events: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """
    Build the complete lineage read model for one dataset version.
    """

    version_row = _to_dict(
        version
    )

    missing_fields = sorted(
        field
        for field in REQUIRED_VERSION_FIELDS
        if version_row.get(field) is None
    )

    if missing_fields:
        raise ValueError(
            "Dataset version thiếu lineage field bắt buộc: "
            + ", ".join(missing_fields)
        )

    ingestion_rows = [
        _to_dict(item)
        for item in ingestions
    ]

    validation_rows = [
        _to_dict(item)
        for item in validations
    ]

    lifecycle_rows = [
        _to_dict(item)
        for item in lifecycle_events
    ]

    timeline = build_lineage_timeline(
        ingestions=ingestion_rows,
        validations=validation_rows,
        lifecycle_events=lifecycle_rows,
    )

    latest_validation = None

    if validation_rows:
        latest_validation = max(
            validation_rows,
            key=lambda item: (
                _timestamp_sort_value(
                    item.get(
                        "validated_at"
                    )
                ),
                int(
                    item.get(
                        "validation_id",
                        0,
                    )
                    or 0
                ),
            ),
        )

    lifecycle_state = str(
        version_row[
            "lifecycle_state"
        ]
    ).upper()

    summary = {
        "catalog_id": int(
            version_row["catalog_id"]
        ),
        "version_id": int(
            version_row["version_id"]
        ),
        "version_number": int(
            version_row["version_number"]
        ),
        "file_name": str(
            version_row["file_name"]
        ),
        "content_sha256": str(
            version_row["content_sha256"]
        ),
        "lifecycle_state": lifecycle_state,
        "raw_path": version_row.get(
            "raw_path"
        ),
        "ingestion_count": len(
            ingestion_rows
        ),
        "validation_count": len(
            validation_rows
        ),
        "lifecycle_event_count": len(
            lifecycle_rows
        ),
        "latest_validation_status": (
            str(
                latest_validation[
                    "validation_status"
                ]
            ).upper()
            if latest_validation
            else None
        ),
        "promotion_eligible": (
            lifecycle_state
            == "VALIDATED"
        ),
        "is_active": (
            lifecycle_state
            == "ACTIVE"
        ),
    }

    return {
        "summary": summary,
        "version": version_row,
        "ingestions": ingestion_rows,
        "validations": validation_rows,
        "lifecycle_events": lifecycle_rows,
        "timeline": timeline,
    }