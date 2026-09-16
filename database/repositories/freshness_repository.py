from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import text

from database.db import get_engine

FRESHNESS_STATUSES = {
    "FRESH",
    "STALE",
    "NO_DATA",
}


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


def _normalize_status(
    freshness_status: str,
) -> str:
    normalized = str(
        freshness_status
    ).strip().upper()

    if normalized not in FRESHNESS_STATUSES:
        raise ValueError(
            "Unsupported freshness status: "
            f"{freshness_status}"
        )

    return normalized


def get_freshness_policy(
    catalog_id: int,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT TOP 1
            freshness_policy_id,
            catalog_id,
            max_age_minutes,
            is_enabled,
            created_at,
            updated_at
        FROM dbo.dataset_freshness_policies
        WHERE catalog_id = :catalog_id;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "catalog_id": _positive_int(
                    catalog_id,
                    field_name="catalog_id",
                ),
            },
        ).mappings().first()

    if row is None:
        return None

    result = dict(row)
    result["is_enabled"] = bool(
        result["is_enabled"]
    )

    return result


def upsert_freshness_policy(
    *,
    catalog_id: int,
    max_age_minutes: int,
    is_enabled: bool = True,
) -> dict[str, Any]:
    normalized_catalog_id = _positive_int(
        catalog_id,
        field_name="catalog_id",
    )

    normalized_max_age = _positive_int(
        max_age_minutes,
        field_name="max_age_minutes",
    )

    find_query = text(
        """
        SELECT TOP 1
            freshness_policy_id
        FROM dbo.dataset_freshness_policies
            WITH (
                UPDLOCK,
                HOLDLOCK
            )
        WHERE catalog_id = :catalog_id;
        """
    )

    insert_query = text(
        """
        INSERT INTO dbo.dataset_freshness_policies (
            catalog_id,
            max_age_minutes,
            is_enabled
        )
        VALUES (
            :catalog_id,
            :max_age_minutes,
            :is_enabled
        );
        """
    )

    update_query = text(
        """
        UPDATE dbo.dataset_freshness_policies
        SET
            max_age_minutes = :max_age_minutes,
            is_enabled = :is_enabled,
            updated_at = SYSUTCDATETIME()
        WHERE catalog_id = :catalog_id;
        """
    )

    params = {
        "catalog_id": normalized_catalog_id,
        "max_age_minutes": normalized_max_age,
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

    policy = get_freshness_policy(
        normalized_catalog_id
    )

    if policy is None:
        raise RuntimeError(
            "Freshness policy was saved but "
            "could not be loaded."
        )

    return policy


def get_enabled_freshness_policies() -> pd.DataFrame:
    query = text(
        """
        SELECT
            p.freshness_policy_id,
            p.catalog_id,
            c.dataset_key,
            c.display_name,
            p.max_age_minutes,
            p.is_enabled,
            p.created_at,
            p.updated_at
        FROM dbo.dataset_freshness_policies AS p
        INNER JOIN dbo.dataset_catalog AS c
            ON c.catalog_id = p.catalog_id
        WHERE p.is_enabled = 1
        ORDER BY
            p.catalog_id ASC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
        )


def get_latest_ingestion_for_catalog(
    catalog_id: int,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT TOP 1
            ih.ingestion_event_id,
            ih.ingestion_id,
            ih.catalog_id,
            ih.version_id,
            dv.version_number,
            ih.source_type,
            ih.ingested_at,
            ih.raw_path
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
        row = connection.execute(
            query,
            {
                "catalog_id": _positive_int(
                    catalog_id,
                    field_name="catalog_id",
                ),
            },
        ).mappings().first()

    return (
        dict(row)
        if row is not None
        else None
    )


def create_freshness_check(
    *,
    catalog_id: int,
    max_age_minutes: int,
    freshness_status: str,
    ingestion_event_id: int | None = None,
    version_id: int | None = None,
    age_minutes: int | None = None,
    latest_ingested_at: datetime | None = None,
    checked_at: datetime | None = None,
) -> dict[str, Any]:
    normalized_status = _normalize_status(
        freshness_status
    )

    normalized_age = (
        None
        if age_minutes is None
        else int(age_minutes)
    )

    if (
        normalized_age is not None
        and normalized_age < 0
    ):
        raise ValueError(
            "age_minutes must be greater "
            "than or equal to 0."
        )

    if (
        normalized_status != "NO_DATA"
        and normalized_age is None
    ):
        raise ValueError(
            "age_minutes is required for "
            "FRESH and STALE checks."
        )

    insert_query = text(
        """
        INSERT INTO dbo.dataset_freshness_history (
            catalog_id,
            ingestion_event_id,
            version_id,
            max_age_minutes,
            age_minutes,
            freshness_status,
            latest_ingested_at,
            checked_at
        )
        OUTPUT
            INSERTED.freshness_check_id
        VALUES (
            :catalog_id,
            :ingestion_event_id,
            :version_id,
            :max_age_minutes,
            :age_minutes,
            :freshness_status,
            :latest_ingested_at,
            COALESCE(
                :checked_at,
                SYSUTCDATETIME()
            )
        );
        """
    )

    params = {
        "catalog_id": _positive_int(
            catalog_id,
            field_name="catalog_id",
        ),
        "ingestion_event_id": (
            _positive_int(
                ingestion_event_id,
                field_name="ingestion_event_id",
            )
            if ingestion_event_id is not None
            else None
        ),
        "version_id": (
            _positive_int(
                version_id,
                field_name="version_id",
            )
            if version_id is not None
            else None
        ),
        "max_age_minutes": _positive_int(
            max_age_minutes,
            field_name="max_age_minutes",
        ),
        "age_minutes": normalized_age,
        "freshness_status": normalized_status,
        "latest_ingested_at": latest_ingested_at,
        "checked_at": checked_at,
    }

    engine = get_engine()

    with engine.begin() as connection:
        freshness_check_id = (
            connection.execute(
                insert_query,
                params,
            ).scalar_one()
        )

    check = get_freshness_check(
        int(freshness_check_id)
    )

    if check is None:
        raise RuntimeError(
            "Freshness check was created but "
            "could not be loaded."
        )

    return check


def get_freshness_check(
    freshness_check_id: int,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT TOP 1
            freshness_check_id,
            catalog_id,
            ingestion_event_id,
            version_id,
            max_age_minutes,
            age_minutes,
            freshness_status,
            latest_ingested_at,
            checked_at
        FROM dbo.dataset_freshness_history
        WHERE freshness_check_id =
            :freshness_check_id;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "freshness_check_id": (
                    _positive_int(
                        freshness_check_id,
                        field_name=(
                            "freshness_check_id"
                        ),
                    )
                ),
            },
        ).mappings().first()

    return (
        dict(row)
        if row is not None
        else None
    )


def get_freshness_history(
    catalog_id: int,
    limit: int = 50,
) -> pd.DataFrame:
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
            freshness_check_id,
            catalog_id,
            ingestion_event_id,
            version_id,
            max_age_minutes,
            age_minutes,
            freshness_status,
            latest_ingested_at,
            checked_at
        FROM dbo.dataset_freshness_history
        WHERE catalog_id = :catalog_id
        ORDER BY
            checked_at DESC,
            freshness_check_id DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
            params={
                "catalog_id": _positive_int(
                    catalog_id,
                    field_name="catalog_id",
                ),
            },
        )