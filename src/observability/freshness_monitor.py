from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from database.repositories.freshness_repository import (
    create_freshness_check,
    get_enabled_freshness_policies,
    get_freshness_policy,
    get_latest_ingestion_for_catalog,
)
from src.observability.operational_events import (
    emit_operational_event,
)


def _as_utc(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value.replace(
            tzinfo=UTC
        )

    return value.astimezone(
        UTC
    )


def calculate_age_minutes(
    *,
    latest_ingested_at: datetime,
    checked_at: datetime,
) -> int:
    latest_utc = _as_utc(
        latest_ingested_at
    )

    checked_utc = _as_utc(
        checked_at
    )

    age_seconds = (
        checked_utc
        - latest_utc
    ).total_seconds()

    return max(
        0,
        int(age_seconds // 60),
    )


def check_dataset_freshness(
    catalog_id: int,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    policy = get_freshness_policy(
        catalog_id
    )

    if policy is None:
        raise ValueError(
            "No freshness policy exists "
            f"for catalog_id={catalog_id}."
        )

    if not bool(
        policy["is_enabled"]
    ):
        raise ValueError(
            "Freshness policy is disabled "
            f"for catalog_id={catalog_id}."
        )

    max_age_minutes = int(
        policy["max_age_minutes"]
    )

    checked_at = _as_utc(
        now
        or datetime.now(UTC)
    )

    latest_ingestion = (
        get_latest_ingestion_for_catalog(
            catalog_id
        )
    )

    if latest_ingestion is None:
        check = create_freshness_check(
            catalog_id=catalog_id,
            max_age_minutes=(
                max_age_minutes
            ),
            freshness_status="NO_DATA",
            ingestion_event_id=None,
            version_id=None,
            age_minutes=None,
            latest_ingested_at=None,
            checked_at=(
                checked_at.replace(
                    tzinfo=None
                )
            ),
        )

        return {
            "policy": policy,
            "check": check,
            "operational_event": None,
        }

    ingestion_event_id = int(
        latest_ingestion[
            "ingestion_event_id"
        ]
    )

    version_id = int(
        latest_ingestion[
            "version_id"
        ]
    )

    latest_ingested_at = _as_utc(
        latest_ingestion[
            "ingested_at"
        ]
    )

    age_minutes = calculate_age_minutes(
        latest_ingested_at=(
            latest_ingested_at
        ),
        checked_at=checked_at,
    )

    freshness_status = (
        "STALE"
        if age_minutes
        > max_age_minutes
        else "FRESH"
    )

    check = create_freshness_check(
        catalog_id=catalog_id,
        ingestion_event_id=(
            ingestion_event_id
        ),
        version_id=version_id,
        max_age_minutes=(
            max_age_minutes
        ),
        age_minutes=age_minutes,
        freshness_status=(
            freshness_status
        ),
        latest_ingested_at=(
            latest_ingested_at
        ),
        checked_at=(
            checked_at.replace(
                tzinfo=None
            )
        ),
    )

    operational_event = None

    if freshness_status == "STALE":
        freshness_check_id = int(
            check[
                "freshness_check_id"
            ]
        )

        operational_event = (
            emit_operational_event(
                event_key=(
                    "freshness:"
                    f"{catalog_id}:"
                    f"{ingestion_event_id}:"
                    "stale"
                ),
                event_type=(
                    "DATASET_FRESHNESS_BREACH"
                ),
                severity="WARNING",
                event_source=(
                    "DATA_OBSERVABILITY"
                ),
                event_stage=(
                    "FRESHNESS_MONITOR"
                ),
                catalog_id=catalog_id,
                version_id=version_id,
                reference_id=(
                    freshness_check_id
                ),
                message=(
                    "Dataset freshness SLA "
                    "was breached."
                ),
                detail={
                    "freshness_check_id": (
                        freshness_check_id
                    ),
                    "ingestion_event_id": (
                        ingestion_event_id
                    ),
                    "max_age_minutes": (
                        max_age_minutes
                    ),
                    "age_minutes": (
                        age_minutes
                    ),
                    "latest_ingested_at": (
                        latest_ingested_at
                        .isoformat()
                    ),
                    "checked_at": (
                        checked_at
                        .isoformat()
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


def check_enabled_freshness_policies(
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    policies = (
        get_enabled_freshness_policies()
    )

    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    fresh_count = 0
    stale_count = 0
    no_data_count = 0

    for row in policies.to_dict(
        orient="records"
    ):
        catalog_id = int(
            row["catalog_id"]
        )

        try:
            result = (
                check_dataset_freshness(
                    catalog_id,
                    now=now,
                )
            )

            results.append(
                result
            )

            status = str(
                result["check"][
                    "freshness_status"
                ]
            )

            if status == "FRESH":
                fresh_count += 1
            elif status == "STALE":
                stale_count += 1
            elif status == "NO_DATA":
                no_data_count += 1

        except Exception as exc:
            errors.append(
                {
                    "catalog_id": (
                        catalog_id
                    ),
                    "error_type": (
                        type(exc).__name__
                    ),
                    "error_message": (
                        str(exc)
                    ),
                }
            )

    return {
        "policy_count": int(
            len(policies)
        ),
        "checked_count": len(
            results
        ),
        "failed_count": len(
            errors
        ),
        "fresh_count": fresh_count,
        "stale_count": stale_count,
        "no_data_count": (
            no_data_count
        ),
        "results": results,
        "errors": errors,
    }