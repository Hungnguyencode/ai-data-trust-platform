from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

import pandas as pd
from sqlalchemy import text

from database.db import get_engine
from src.ingestion.contracts import IngestionMetadata
from src.ingestion.raw_storage import sanitize_file_name


def normalize_dataset_key(file_name: str) -> str:
    """
    Logical dataset identity used by the first catalog version.

    For now, files with the same normalized file name belong to the
    same logical dataset.

    Example:
        Customers.CSV
        customers.csv

    both resolve to:
        customers.csv
    """
    safe_name = sanitize_file_name(file_name)
    return safe_name.casefold()


def _metadata_to_dict(
    metadata: IngestionMetadata | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(metadata, IngestionMetadata):
        return metadata.to_dict()

    return dict(metadata)


def _parse_ingested_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value

    text_value = str(value).strip()

    if text_value.endswith("Z"):
        text_value = f"{text_value[:-1]}+00:00"

    return datetime.fromisoformat(text_value)


def register_ingestion(
    metadata: IngestionMetadata | Mapping[str, Any],
) -> dict[str, Any]:
    """
    Register one ingestion event into SQL Server catalog.

    Behaviour:
    - same file name + new SHA -> new dataset version
    - same file name + same SHA -> reuse existing version
    - every new ingestion_id -> append ingestion history
    - same ingestion_id -> idempotent, no duplicate event
    """
    values = _metadata_to_dict(metadata)

    required_fields = {
        "ingestion_id",
        "source_type",
        "file_name",
        "file_type",
        "extension",
        "content_sha256",
        "byte_size",
        "row_count",
        "column_count",
        "ingested_at",
    }

    missing_fields = sorted(
        field
        for field in required_fields
        if values.get(field) in {None, ""}
    )

    if missing_fields:
        raise ValueError(
            "Ingestion metadata thiếu field bắt buộc: "
            + ", ".join(missing_fields)
        )

    display_name = sanitize_file_name(
        str(values["file_name"])
    )
    dataset_key = normalize_dataset_key(display_name)

    params = {
        "ingestion_id": str(values["ingestion_id"]),
        "source_type": str(values["source_type"]),
        "file_name": display_name,
        "file_type": str(values["file_type"]),
        "extension": str(values["extension"]),
        "content_sha256": str(values["content_sha256"]),
        "byte_size": int(values["byte_size"]),
        "row_count": int(values["row_count"]),
        "column_count": int(values["column_count"]),
        "ingested_at": _parse_ingested_at(
            values["ingested_at"]
        ),
        "raw_path": (
            str(values["raw_path"])
            if values.get("raw_path")
            else None
        ),
        "dataset_key": dataset_key,
        "display_name": display_name,
    }

    existing_ingestion_query = text(
        """
        SELECT TOP 1
            ih.ingestion_event_id,
            ih.ingestion_id,
            ih.catalog_id,
            ih.version_id,
            dv.version_number,
            dv.content_sha256,
            ih.is_new_version
        FROM dbo.ingestion_history AS ih
        INNER JOIN dbo.dataset_versions AS dv
            ON ih.version_id = dv.version_id
        WHERE ih.ingestion_id = :ingestion_id;
        """
    )

    find_catalog_query = text(
        """
        SELECT catalog_id
        FROM dbo.dataset_catalog WITH (UPDLOCK, HOLDLOCK)
        WHERE dataset_key = :dataset_key;
        """
    )

    insert_catalog_query = text(
        """
        INSERT INTO dbo.dataset_catalog (
            dataset_key,
            display_name
        )
        OUTPUT INSERTED.catalog_id
        VALUES (
            :dataset_key,
            :display_name
        );
        """
    )

    update_catalog_query = text(
        """
        UPDATE dbo.dataset_catalog
        SET
            display_name = :display_name,
            updated_at = SYSUTCDATETIME()
        WHERE catalog_id = :catalog_id;
        """
    )

    find_version_query = text(
        """
        SELECT TOP 1
            version_id,
            version_number,
            content_sha256
        FROM dbo.dataset_versions
        WHERE catalog_id = :catalog_id
          AND content_sha256 = :content_sha256;
        """
    )

    next_version_query = text(
        """
        SELECT
            COALESCE(MAX(version_number), 0) + 1
        FROM dbo.dataset_versions WITH (UPDLOCK, HOLDLOCK)
        WHERE catalog_id = :catalog_id;
        """
    )

    insert_version_query = text(
        """
        INSERT INTO dbo.dataset_versions (
            catalog_id,
            version_number,
            content_sha256,
            file_name,
            file_type,
            extension,
            byte_size,
            row_count,
            column_count,
            raw_path
        )
        OUTPUT
            INSERTED.version_id,
            INSERTED.version_number
        VALUES (
            :catalog_id,
            :version_number,
            :content_sha256,
            :file_name,
            :file_type,
            :extension,
            :byte_size,
            :row_count,
            :column_count,
            :raw_path
        );
        """
    )

    insert_ingestion_query = text(
        """
        INSERT INTO dbo.ingestion_history (
            ingestion_id,
            catalog_id,
            version_id,
            source_type,
            ingested_at,
            raw_path,
            is_new_version
        )
        OUTPUT INSERTED.ingestion_event_id
        VALUES (
            :ingestion_id,
            :catalog_id,
            :version_id,
            :source_type,
            :ingested_at,
            :raw_path,
            :is_new_version
        );
        """
    )

    engine = get_engine()

    with engine.begin() as connection:
        existing_ingestion = connection.execute(
            existing_ingestion_query,
            {
                "ingestion_id": params["ingestion_id"],
            },
        ).mappings().first()

        if existing_ingestion is not None:
            result = dict(existing_ingestion)
            result["is_new_version"] = bool(
                result["is_new_version"]
            )
            result["dataset_key"] = dataset_key
            result["display_name"] = display_name
            return result

        catalog_id = connection.execute(
            find_catalog_query,
            {
                "dataset_key": dataset_key,
            },
        ).scalar_one_or_none()

        if catalog_id is None:
            catalog_id = connection.execute(
                insert_catalog_query,
                {
                    "dataset_key": dataset_key,
                    "display_name": display_name,
                },
            ).scalar_one()
        else:
            connection.execute(
                update_catalog_query,
                {
                    "catalog_id": int(catalog_id),
                    "display_name": display_name,
                },
            )

        catalog_id = int(catalog_id)

        version_row = connection.execute(
            find_version_query,
            {
                "catalog_id": catalog_id,
                "content_sha256": params[
                    "content_sha256"
                ],
            },
        ).mappings().first()

        if version_row is None:
            version_number = int(
                connection.execute(
                    next_version_query,
                    {
                        "catalog_id": catalog_id,
                    },
                ).scalar_one()
            )

            inserted_version = connection.execute(
                insert_version_query,
                {
                    **params,
                    "catalog_id": catalog_id,
                    "version_number": version_number,
                },
            ).mappings().one()

            version_id = int(
                inserted_version["version_id"]
            )
            version_number = int(
                inserted_version["version_number"]
            )
            is_new_version = True

        else:
            version_id = int(
                version_row["version_id"]
            )
            version_number = int(
                version_row["version_number"]
            )
            is_new_version = False

        ingestion_event_id = connection.execute(
            insert_ingestion_query,
            {
                **params,
                "catalog_id": catalog_id,
                "version_id": version_id,
                "is_new_version": is_new_version,
            },
        ).scalar_one()

    return {
        "ingestion_event_id": int(
            ingestion_event_id
        ),
        "ingestion_id": params["ingestion_id"],
        "catalog_id": catalog_id,
        "version_id": version_id,
        "version_number": version_number,
        "content_sha256": params["content_sha256"],
        "is_new_version": is_new_version,
        "dataset_key": dataset_key,
        "display_name": display_name,
    }


def get_dataset_version_history(
    catalog_id: int,
) -> pd.DataFrame:
    """
    Return all known versions of one logical dataset.
    """
    query = text(
        """
        SELECT
            dv.version_id,
            dv.version_number,
            dv.content_sha256,
            dv.file_name,
            dv.file_type,
            dv.extension,
            dv.byte_size,
            dv.row_count,
            dv.column_count,
            dv.raw_path,
            dv.created_at,
            COUNT(ih.ingestion_event_id)
                AS ingestion_count,
            MAX(ih.ingested_at)
                AS last_ingested_at
        FROM dbo.dataset_versions AS dv
        LEFT JOIN dbo.ingestion_history AS ih
            ON dv.version_id = ih.version_id
        WHERE dv.catalog_id = :catalog_id
        GROUP BY
            dv.version_id,
            dv.version_number,
            dv.content_sha256,
            dv.file_name,
            dv.file_type,
            dv.extension,
            dv.byte_size,
            dv.row_count,
            dv.column_count,
            dv.raw_path,
            dv.created_at
        ORDER BY dv.version_number DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
            params={
                "catalog_id": int(catalog_id),
            },
        )


def get_ingestion_history(
    catalog_id: int,
    limit: int = 50,
) -> pd.DataFrame:
    """
    Return recent ingestion events for one logical dataset.
    """
    safe_limit = max(
        1,
        min(int(limit), 1000),
    )

    query = text(
        f"""
        SELECT TOP {safe_limit}
            ih.ingestion_event_id,
            ih.ingestion_id,
            ih.catalog_id,
            ih.version_id,
            dv.version_number,
            ih.source_type,
            ih.ingested_at,
            ih.is_new_version,
            ih.raw_path
        FROM dbo.ingestion_history AS ih
        INNER JOIN dbo.dataset_versions AS dv
            ON ih.version_id = dv.version_id
        WHERE ih.catalog_id = :catalog_id
        ORDER BY ih.ingested_at DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
            params={
                "catalog_id": int(catalog_id),
            },
        )