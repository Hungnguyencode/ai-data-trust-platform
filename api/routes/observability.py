from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from api.schemas.observability_schema import (
    DatasetObservabilityResponse,
    ObservabilityOverviewResponse,
    ObservabilitySummaryResponse,
)
from database.repositories.freshness_repository import (
    get_enabled_freshness_policies as load_enabled_freshness_policies,
)
from database.repositories.freshness_repository import (
    get_freshness_history as load_freshness_history,
)
from database.repositories.operational_event_repository import (
    get_operational_event_history as load_operational_event_history,
)
from database.repositories.pipeline_run_repository import (
    get_pipeline_run_history as load_pipeline_run_history,
)
from database.repositories.volume_repository import (
    get_enabled_volume_policies as load_enabled_volume_policies,
)
from database.repositories.volume_repository import (
    get_volume_history as load_volume_history,
)

router = APIRouter()


def _frame_records(
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    if frame.empty:
        return []

    normalized = (
        frame.astype(object)
        .where(
            pd.notna(frame),
            None,
        )
    )

    return normalized.to_dict(
        orient="records"
    )


def _catalog_ids(
    records: list[dict[str, Any]],
) -> set[int]:
    catalog_ids: set[int] = set()

    for record in records:
        catalog_id = record.get(
            "catalog_id"
        )

        if catalog_id is None:
            continue

        catalog_ids.add(
            int(catalog_id)
        )

    return catalog_ids


@router.get(
    "/overview",
    response_model=ObservabilityOverviewResponse,
)
def get_observability_overview(
    event_limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
    run_limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
):
    try:
        freshness_policies = (
            load_enabled_freshness_policies()
        )

        volume_policies = (
            load_enabled_volume_policies()
        )

        event_history = (
            load_operational_event_history(
                limit=event_limit
            )
        )

        pipeline_history = (
            load_pipeline_run_history(
                limit=run_limit
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "observability overview."
            ),
        ) from exc

    freshness_policy_records = (
        _frame_records(
            freshness_policies
        )
    )

    volume_policy_records = (
        _frame_records(
            volume_policies
        )
    )

    event_records = _frame_records(
        event_history
    )

    pipeline_records = _frame_records(
        pipeline_history
    )

    freshness_catalog_ids = (
        _catalog_ids(
            freshness_policy_records
        )
    )

    volume_catalog_ids = (
        _catalog_ids(
            volume_policy_records
        )
    )

    monitored_catalog_ids = sorted(
        freshness_catalog_ids
        | volume_catalog_ids
    )

    dataset_items: list[
        DatasetObservabilityResponse
    ] = []

    freshness_breach_count = 0
    volume_breach_count = 0

    for catalog_id in monitored_catalog_ids:
        try:
            freshness_history = (
                load_freshness_history(
                    catalog_id,
                    limit=1,
                )
                if catalog_id
                in freshness_catalog_ids
                else pd.DataFrame()
            )

            volume_history = (
                load_volume_history(
                    catalog_id,
                    limit=1,
                )
                if catalog_id
                in volume_catalog_ids
                else pd.DataFrame()
            )

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Unable to load "
                    "observability overview."
                ),
            ) from exc

        freshness_records = (
            _frame_records(
                freshness_history
            )
        )

        volume_records = (
            _frame_records(
                volume_history
            )
        )

        latest_freshness = (
            freshness_records[0]
            if freshness_records
            else None
        )

        latest_volume = (
            volume_records[0]
            if volume_records
            else None
        )

        freshness_status = (
            str(
                latest_freshness[
                    "freshness_status"
                ]
            )
            if latest_freshness
            else None
        )

        volume_status = (
            str(
                latest_volume[
                    "volume_status"
                ]
            )
            if latest_volume
            else None
        )

        if freshness_status == "STALE":
            freshness_breach_count += 1

        if volume_status in {
            "DROP",
            "SPIKE",
        }:
            volume_breach_count += 1

        catalog_pipeline_runs = [
            record
            for record in pipeline_records
            if (
                record.get(
                    "catalog_id"
                )
                is not None
                and int(
                    record[
                        "catalog_id"
                    ]
                )
                == catalog_id
            )
        ]

        latest_pipeline = (
            catalog_pipeline_runs[0]
            if catalog_pipeline_runs
            else None
        )

        catalog_events = [
            record
            for record in event_records
            if (
                record.get(
                    "catalog_id"
                )
                is not None
                and int(
                    record[
                        "catalog_id"
                    ]
                )
                == catalog_id
            )
        ]

        dataset_items.append(
            DatasetObservabilityResponse(
                catalog_id=catalog_id,
                freshness_enabled=(
                    catalog_id
                    in freshness_catalog_ids
                ),
                freshness_status=(
                    freshness_status
                ),
                freshness_checked_at=(
                    latest_freshness.get(
                        "checked_at"
                    )
                    if latest_freshness
                    else None
                ),
                volume_enabled=(
                    catalog_id
                    in volume_catalog_ids
                ),
                volume_status=volume_status,
                volume_checked_at=(
                    latest_volume.get(
                        "checked_at"
                    )
                    if latest_volume
                    else None
                ),
                latest_pipeline_run_id=(
                    int(
                        latest_pipeline[
                            "pipeline_run_id"
                        ]
                    )
                    if latest_pipeline
                    else None
                ),
                latest_pipeline_status=(
                    str(
                        latest_pipeline[
                            "run_status"
                        ]
                    )
                    if latest_pipeline
                    else None
                ),
                latest_pipeline_finished_at=(
                    latest_pipeline.get(
                        "finished_at"
                    )
                    if latest_pipeline
                    else None
                ),
                recent_operational_event_count=(
                    len(catalog_events)
                ),
            )
        )

    failed_pipeline_run_count = sum(
        1
        for record in pipeline_records
        if str(
            record.get(
                "run_status",
                "",
            )
        ).upper()
        == "FAILED"
    )

    return ObservabilityOverviewResponse(
        summary=ObservabilitySummaryResponse(
            monitored_dataset_count=len(
                monitored_catalog_ids
            ),
            freshness_policy_count=len(
                freshness_catalog_ids
            ),
            freshness_breach_count=(
                freshness_breach_count
            ),
            volume_policy_count=len(
                volume_catalog_ids
            ),
            volume_breach_count=(
                volume_breach_count
            ),
            operational_event_count=len(
                event_records
            ),
            recent_failed_pipeline_run_count=(
                failed_pipeline_run_count
            ),
        ),
        datasets=dataset_items,
    )