from __future__ import annotations

from math import isfinite
from typing import Any

import pandas as pd
from sqlalchemy import text

from database.db import get_engine


def _positive_int(
    value: Any,
    *,
    field_name: str,
) -> int:
    normalized = int(value)

    if normalized <= 0:
        raise ValueError(
            f"{field_name} must be greater than 0."
        )

    return normalized


def _positive_number(
    value: Any,
    *,
    field_name: str,
    maximum: float | None = None,
) -> float:
    normalized = float(value)

    if (
        not isfinite(normalized)
        or normalized <= 0
    ):
        raise ValueError(
            f"{field_name} must be greater than 0."
        )

    if (
        maximum is not None
        and normalized > maximum
    ):
        raise ValueError(
            f"{field_name} must be less than "
            f"or equal to {maximum}."
        )

    return normalized


def get_volume_policy(
    catalog_id: int,
) -> dict[str, Any] | None:
    normalized_catalog_id = _positive_int(
        catalog_id,
        field_name="catalog_id",
    )

    query = text(
        """
        SELECT TOP 1
            volume_policy_id,
            catalog_id,
            drop_threshold_pct,
            spike_threshold_pct,
            is_enabled,
            created_at,
            updated_at
        FROM dbo.dataset_volume_policies
        WHERE catalog_id = :catalog_id;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "catalog_id": normalized_catalog_id,
            },
        ).mappings().first()

    if row is None:
        return None

    result = dict(row)
    result["is_enabled"] = bool(
        result["is_enabled"]
    )

    return result


def upsert_volume_policy(
    *,
    catalog_id: int,
    drop_threshold_pct: float,
    spike_threshold_pct: float,
    is_enabled: bool = True,
) -> dict[str, Any]:
    normalized_catalog_id = _positive_int(
        catalog_id,
        field_name="catalog_id",
    )

    normalized_drop_threshold = (
        _positive_number(
            drop_threshold_pct,
            field_name="drop_threshold_pct",
            maximum=100.0,
        )
    )

    normalized_spike_threshold = (
        _positive_number(
            spike_threshold_pct,
            field_name="spike_threshold_pct",
        )
    )

    find_query = text(
        """
        SELECT TOP 1
            volume_policy_id
        FROM dbo.dataset_volume_policies
            WITH (UPDLOCK, HOLDLOCK)
        WHERE catalog_id = :catalog_id;
        """
    )

    insert_query = text(
        """
        INSERT INTO dbo.dataset_volume_policies (
            catalog_id,
            drop_threshold_pct,
            spike_threshold_pct,
            is_enabled
        )
        VALUES (
            :catalog_id,
            :drop_threshold_pct,
            :spike_threshold_pct,
            :is_enabled
        );
        """
    )

    update_query = text(
        """
        UPDATE dbo.dataset_volume_policies
        SET
            drop_threshold_pct = :drop_threshold_pct,
            spike_threshold_pct = :spike_threshold_pct,
            is_enabled = :is_enabled,
            updated_at = SYSUTCDATETIME()
        WHERE catalog_id = :catalog_id;
        """
    )

    params = {
        "catalog_id": normalized_catalog_id,
        "drop_threshold_pct": (
            normalized_drop_threshold
        ),
        "spike_threshold_pct": (
            normalized_spike_threshold
        ),
        "is_enabled": int(
            bool(is_enabled)
        ),
    }

    engine = get_engine()

    with engine.begin() as connection:
        existing = connection.execute(
            find_query,
            {
                "catalog_id": (
                    normalized_catalog_id
                ),
            },
        ).mappings().first()

        if existing is None:
            connection.execute(
                insert_query,
                params,
            )
        else:
            connection.execute(
                update_query,
                params,
            )

    policy = get_volume_policy(
        normalized_catalog_id
    )

    if policy is None:
        raise RuntimeError(
            "Volume policy was saved but "
            "could not be loaded."
        )

    return policy


def get_enabled_volume_policies() -> pd.DataFrame:
    query = text(
        """
        SELECT
            p.volume_policy_id,
            p.catalog_id,
            c.dataset_key,
            c.display_name,
            p.drop_threshold_pct,
            p.spike_threshold_pct,
            p.is_enabled,
            p.created_at,
            p.updated_at
        FROM dbo.dataset_volume_policies AS p
        INNER JOIN dbo.dataset_catalog AS c
            ON c.catalog_id = p.catalog_id
        WHERE p.is_enabled = 1
        ORDER BY p.catalog_id ASC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
        )


def get_recent_ingestions_for_catalog(
    catalog_id: int,
    *,
    limit: int = 2,
) -> pd.DataFrame:
    normalized_catalog_id = _positive_int(
        catalog_id,
        field_name="catalog_id",
    )

    safe_limit = max(
        1,
        min(
            int(limit),
            1000,
        ),
    )

    query = text(
        f"""
        SELECT TOP {safe_limit}
            ih.ingestion_event_id,
            ih.ingestion_id,
            ih.catalog_id,
            ih.version_id,
            dv.version_number,
            dv.row_count,
            ih.source_type,
            ih.ingested_at
        FROM dbo.ingestion_history AS ih
        INNER JOIN dbo.dataset_versions AS dv
            ON dv.version_id = ih.version_id
        WHERE ih.catalog_id = :catalog_id
        ORDER BY
            ih.ingested_at DESC,
            ih.ingestion_event_id DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
            params={
                "catalog_id": (
                    normalized_catalog_id
                ),
            },
        )


VOLUME_STATUSES = {
    "NORMAL",
    "DROP",
    "SPIKE",
    "NO_BASELINE",
}


def _normalize_volume_status(
    value: str,
) -> str:
    normalized = str(
        value
    ).strip().upper()

    if normalized not in VOLUME_STATUSES:
        raise ValueError(
            "volume_status must be one of: "
            + ", ".join(
                sorted(VOLUME_STATUSES)
            )
            + "."
        )

    return normalized


def create_volume_check(
    *,
    volume_policy_id: int,
    catalog_id: int,
    ingestion_event_id: int,
    version_id: int,
    current_row_count: int,
    drop_threshold_pct: float,
    spike_threshold_pct: float,
    volume_status: str,
    baseline_ingestion_event_id: int | None = None,
    baseline_version_id: int | None = None,
    baseline_row_count: int | None = None,
    row_change_pct: float | None = None,
) -> dict[str, Any]:
    normalized_policy_id = _positive_int(
        volume_policy_id,
        field_name="volume_policy_id",
    )
    normalized_catalog_id = _positive_int(
        catalog_id,
        field_name="catalog_id",
    )
    normalized_ingestion_event_id = _positive_int(
        ingestion_event_id,
        field_name="ingestion_event_id",
    )
    normalized_version_id = _positive_int(
        version_id,
        field_name="version_id",
    )

    normalized_current_rows = int(
        current_row_count
    )
    if normalized_current_rows < 0:
        raise ValueError(
            "current_row_count must be greater "
            "than or equal to 0."
        )

    normalized_baseline_rows = (
        None
        if baseline_row_count is None
        else int(baseline_row_count)
    )
    if (
        normalized_baseline_rows is not None
        and normalized_baseline_rows < 0
    ):
        raise ValueError(
            "baseline_row_count must be greater "
            "than or equal to 0."
        )

    normalized_status = (
        _normalize_volume_status(
            volume_status
        )
    )

    normalized_drop_threshold = (
        _positive_number(
            drop_threshold_pct,
            field_name="drop_threshold_pct",
            maximum=100.0,
        )
    )
    normalized_spike_threshold = (
        _positive_number(
            spike_threshold_pct,
            field_name="spike_threshold_pct",
        )
    )

    normalized_row_change = (
        None
        if row_change_pct is None
        else float(row_change_pct)
    )
    if (
        normalized_row_change is not None
        and not isfinite(
            normalized_row_change
        )
    ):
        raise ValueError(
            "row_change_pct must be finite."
        )

    params = {
        "volume_policy_id": (
            normalized_policy_id
        ),
        "catalog_id": (
            normalized_catalog_id
        ),
        "ingestion_event_id": (
            normalized_ingestion_event_id
        ),
        "version_id": (
            normalized_version_id
        ),
        "baseline_ingestion_event_id": (
            _positive_int(
                baseline_ingestion_event_id,
                field_name=(
                    "baseline_ingestion_event_id"
                ),
            )
            if baseline_ingestion_event_id
            is not None
            else None
        ),
        "baseline_version_id": (
            _positive_int(
                baseline_version_id,
                field_name="baseline_version_id",
            )
            if baseline_version_id
            is not None
            else None
        ),
        "baseline_row_count": (
            normalized_baseline_rows
        ),
        "current_row_count": (
            normalized_current_rows
        ),
        "drop_threshold_pct": (
            normalized_drop_threshold
        ),
        "spike_threshold_pct": (
            normalized_spike_threshold
        ),
        "row_change_pct": (
            normalized_row_change
        ),
        "volume_status": normalized_status,
    }

    find_query = text(
        """
        SELECT TOP 1
            volume_check_id
        FROM dbo.dataset_volume_history
            WITH (UPDLOCK, HOLDLOCK)
        WHERE volume_policy_id =
            :volume_policy_id
          AND ingestion_event_id =
            :ingestion_event_id;
        """
    )

    insert_query = text(
        """
        INSERT INTO dbo.dataset_volume_history (
            volume_policy_id,
            catalog_id,
            ingestion_event_id,
            version_id,
            baseline_ingestion_event_id,
            baseline_version_id,
            baseline_row_count,
            current_row_count,
            drop_threshold_pct,
            spike_threshold_pct,
            row_change_pct,
            volume_status
        )
        OUTPUT INSERTED.volume_check_id
        VALUES (
            :volume_policy_id,
            :catalog_id,
            :ingestion_event_id,
            :version_id,
            :baseline_ingestion_event_id,
            :baseline_version_id,
            :baseline_row_count,
            :current_row_count,
            :drop_threshold_pct,
            :spike_threshold_pct,
            :row_change_pct,
            :volume_status
        );
        """
    )

    engine = get_engine()

    with engine.begin() as connection:
        existing = (
            connection.execute(
                find_query,
                {
                    "volume_policy_id": (
                        normalized_policy_id
                    ),
                    "ingestion_event_id": (
                        normalized_ingestion_event_id
                    ),
                },
            )
            .mappings()
            .first()
        )

        if existing is not None:
            volume_check_id = int(
                existing[
                    "volume_check_id"
                ]
            )
        else:
            volume_check_id = int(
                connection.execute(
                    insert_query,
                    params,
                ).scalar_one()
            )

    check = get_volume_check(
        volume_check_id
    )

    if check is None:
        raise RuntimeError(
            "Volume check was created but "
            "could not be loaded."
        )

    return check


def get_volume_check(
    volume_check_id: int,
) -> dict[str, Any] | None:
    normalized_check_id = _positive_int(
        volume_check_id,
        field_name="volume_check_id",
    )

    query = text(
        """
        SELECT TOP 1
            volume_check_id,
            volume_policy_id,
            catalog_id,
            ingestion_event_id,
            version_id,
            baseline_ingestion_event_id,
            baseline_version_id,
            baseline_row_count,
            current_row_count,
            drop_threshold_pct,
            spike_threshold_pct,
            row_change_pct,
            volume_status,
            checked_at
        FROM dbo.dataset_volume_history
        WHERE volume_check_id =
            :volume_check_id;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        row = (
            connection.execute(
                query,
                {
                    "volume_check_id": (
                        normalized_check_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    return (
        dict(row)
        if row is not None
        else None
    )


def get_volume_history(
    catalog_id: int,
    limit: int = 50,
) -> pd.DataFrame:
    normalized_catalog_id = _positive_int(
        catalog_id,
        field_name="catalog_id",
    )

    safe_limit = max(
        1,
        min(
            int(limit),
            1000,
        ),
    )

    query = text(
        f"""
        SELECT TOP {safe_limit}
            volume_check_id,
            volume_policy_id,
            catalog_id,
            ingestion_event_id,
            version_id,
            baseline_ingestion_event_id,
            baseline_version_id,
            baseline_row_count,
            current_row_count,
            drop_threshold_pct,
            spike_threshold_pct,
            row_change_pct,
            volume_status,
            checked_at
        FROM dbo.dataset_volume_history
        WHERE catalog_id = :catalog_id
        ORDER BY
            checked_at DESC,
            volume_check_id DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
            params={
                "catalog_id": (
                    normalized_catalog_id
                ),
            },
        )