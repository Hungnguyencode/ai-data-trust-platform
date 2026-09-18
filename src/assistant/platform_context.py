from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from database.repositories.catalog_repository import (
    get_dataset_version_history,
)
from database.repositories.data_contract_repository import (
    get_active_data_contract,
)
from database.repositories.freshness_repository import (
    get_freshness_history,
)
from database.repositories.governance_repository import (
    get_governance_history,
)
from database.repositories.lineage_repository import (
    get_version_lineage,
)
from database.repositories.operational_event_repository import (
    get_operational_event_history,
)
from database.repositories.pipeline_run_repository import (
    get_pipeline_run_history,
)
from database.repositories.validation_repository import (
    get_validation_history,
)
from database.repositories.volume_repository import (
    get_volume_history,
)


def _json_safe(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()

    if isinstance(value, pd.DataFrame):
        return _frame_records(value)

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            _json_safe(item)
            for item in value
        ]

    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except (TypeError, ValueError):
            pass

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    return value


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

    records = normalized.to_dict(
        orient="records"
    )

    return [
        _json_safe(record)
        for record in records
    ]


def _filter_catalog_records(
    records: list[dict[str, Any]],
    catalog_id: int,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []

    for record in records:
        record_catalog_id = record.get(
            "catalog_id"
        )

        if record_catalog_id is None:
            continue

        try:
            matches = (
                int(record_catalog_id)
                == catalog_id
            )
        except (TypeError, ValueError):
            continue

        if matches:
            filtered.append(record)

    return filtered


def _latest_version_id(
    version_records: list[dict[str, Any]],
) -> int | None:
    candidates = [
        record
        for record in version_records
        if record.get("version_id") is not None
    ]

    if not candidates:
        return None

    latest = max(
        candidates,
        key=lambda record: (
            int(
                record.get(
                    "version_number",
                    0,
                )
                or 0
            ),
            int(
                record.get(
                    "version_id",
                    0,
                )
                or 0
            ),
        ),
    )

    return int(
        latest["version_id"]
    )


def _latest_record_for_version(
    records: list[dict[str, Any]],
    version_id: int | None,
) -> dict[str, Any] | None:
    if version_id is None:
        return None

    for record in records:
        record_version_id = record.get(
            "version_id"
        )

        if record_version_id is None:
            continue

        try:
            matches = (
                int(record_version_id)
                == version_id
            )
        except (TypeError, ValueError):
            continue

        if matches:
            return record

    return None


def build_platform_context(
    catalog_id: int,
    *,
    validation_limit: int = 10,
    governance_limit: int = 10,
    freshness_limit: int = 10,
    volume_limit: int = 10,
    pipeline_limit: int = 100,
    event_limit: int = 100,
) -> dict[str, Any]:
    if (
        not isinstance(catalog_id, int)
        or isinstance(catalog_id, bool)
        or catalog_id <= 0
    ):
        raise ValueError(
            "catalog_id must be a positive integer."
        )

    version_history = (
        get_dataset_version_history(
            catalog_id
        )
    )

    version_records = _frame_records(
        version_history
    )

    latest_version_id = _latest_version_id(
        version_records
    )

    active_contract = (
        get_active_data_contract(
            catalog_id
        )
    )

    validation_records = _frame_records(
        get_validation_history(
            catalog_id,
            limit=validation_limit,
        )
    )

    governance_records = _frame_records(
        get_governance_history(
            catalog_id,
            limit=governance_limit,
        )
    )

    latest_version_validation = (
        _latest_record_for_version(
            validation_records,
            latest_version_id,
        )
    )

    latest_version_governance = (
        _latest_record_for_version(
            governance_records,
            latest_version_id,
        )
    )

    freshness_records = _frame_records(
        get_freshness_history(
            catalog_id,
            limit=freshness_limit,
        )
    )

    volume_records = _frame_records(
        get_volume_history(
            catalog_id,
            limit=volume_limit,
        )
    )

    pipeline_records = _filter_catalog_records(
        _frame_records(
            get_pipeline_run_history(
                limit=pipeline_limit
            )
        ),
        catalog_id,
    )

    operational_event_records = (
        _filter_catalog_records(
            _frame_records(
                get_operational_event_history(
                    limit=event_limit
                )
            ),
            catalog_id,
        )
    )

    lineage = None

    if latest_version_id is not None:
        try:
            lineage = get_version_lineage(
                latest_version_id
            )
        except ValueError:
            lineage = None

    context = {
        "catalog_id": catalog_id,
        "dataset": {
            "latest_version_id": (
                latest_version_id
            ),
            "version_history": (
                version_records
            ),
            "lineage": lineage,
        },
        "data_contract": {
            "active": active_contract,
        },
        "validation": {
            "latest": (
                validation_records[0]
                if validation_records
                else None
            ),
            "latest_version": (
                latest_version_validation
            ),
            "history": validation_records,
        },
        "governance": {
            "latest": (
                governance_records[0]
                if governance_records
                else None
            ),
            "latest_version": (
                latest_version_governance
            ),
            "history": governance_records,
        },
        "observability": {
            "freshness": {
                "latest": (
                    freshness_records[0]
                    if freshness_records
                    else None
                ),
                "history": (
                    freshness_records
                ),
            },
            "volume": {
                "latest": (
                    volume_records[0]
                    if volume_records
                    else None
                ),
                "history": (
                    volume_records
                ),
            },
        },
        "operations": {
            "pipeline_runs": (
                pipeline_records
            ),
            "operational_events": (
                operational_event_records
            ),
        },
        "evidence_summary": {
            "version_count": len(
                version_records
            ),
            "has_active_contract": (
                active_contract is not None
            ),
            "validation_count": len(
                validation_records
            ),
            "governance_count": len(
                governance_records
            ),
            "freshness_check_count": len(
                freshness_records
            ),
            "volume_check_count": len(
                volume_records
            ),
            "pipeline_run_count": len(
                pipeline_records
            ),
            "operational_event_count": len(
                operational_event_records
            ),
            "has_lineage": (
                lineage is not None
            ),
        },
    }

    return _json_safe(context)