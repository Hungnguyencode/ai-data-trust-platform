from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
from sqlalchemy import text

from database.db import get_engine
from src.lifecycle.dataset_lifecycle import (
    lifecycle_state_from_validation,
)


def apply_validation_lifecycle(
    catalog_registration: Mapping[str, Any],
    validation_result: Mapping[str, Any],
) -> dict[str, Any]:
    catalog = dict(catalog_registration)
    validation = dict(validation_result)

    catalog_id = int(
        catalog["catalog_id"]
    )
    version_id = int(
        catalog["version_id"]
    )

    target_state = (
        lifecycle_state_from_validation(
            str(validation["status"])
        )
    )

    select_query = text(
        """
        SELECT
            catalog_id,
            version_id,
            version_number,
            lifecycle_state
        FROM dbo.dataset_versions
            WITH (UPDLOCK, HOLDLOCK)
        WHERE version_id = :version_id
          AND catalog_id = :catalog_id;
        """
    )

    update_query = text(
        """
        UPDATE dbo.dataset_versions
        SET
            lifecycle_state = :to_state,
            lifecycle_updated_at =
                SYSUTCDATETIME()
        WHERE version_id = :version_id
          AND catalog_id = :catalog_id;
        """
    )

    history_query = text(
        """
        INSERT INTO
            dbo.dataset_version_lifecycle_history (
                catalog_id,
                version_id,
                from_state,
                to_state,
                reason
            )
        VALUES (
            :catalog_id,
            :version_id,
            :from_state,
            :to_state,
            :reason
        );
        """
    )

    engine = get_engine()

    with engine.begin() as connection:
        version = connection.execute(
            select_query,
            {
                "catalog_id": catalog_id,
                "version_id": version_id,
            },
        ).mappings().first()

        if version is None:
            raise ValueError(
                "Không tìm thấy dataset version "
                "trong catalog."
            )

        current_state = str(
            version["lifecycle_state"]
        ).upper()

        if current_state in {
            "ACTIVE",
            "SUPERSEDED",
        }:
            return {
                "catalog_id": catalog_id,
                "version_id": version_id,
                "version_number": int(
                    version["version_number"]
                ),
                "previous_state": current_state,
                "lifecycle_state": current_state,
                "changed": False,
            }

        if current_state == target_state:
            return {
                "catalog_id": catalog_id,
                "version_id": version_id,
                "version_number": int(
                    version["version_number"]
                ),
                "previous_state": current_state,
                "lifecycle_state": target_state,
                "changed": False,
            }

        connection.execute(
            update_query,
            {
                "catalog_id": catalog_id,
                "version_id": version_id,
                "to_state": target_state,
            },
        )

        connection.execute(
            history_query,
            {
                "catalog_id": catalog_id,
                "version_id": version_id,
                "from_state": current_state,
                "to_state": target_state,
                "reason": (
                    "Validation Gate status="
                    + str(
                        validation["status"]
                    ).upper()
                ),
            },
        )

    return {
        "catalog_id": catalog_id,
        "version_id": version_id,
        "version_number": int(
            catalog["version_number"]
        ),
        "previous_state": current_state,
        "lifecycle_state": target_state,
        "changed": True,
    }


def promote_version(
    *,
    catalog_id: int,
    version_id: int,
) -> dict[str, Any]:
    catalog_id = int(catalog_id)
    version_id = int(version_id)

    target_query = text(
        """
        SELECT
            catalog_id,
            version_id,
            version_number,
            lifecycle_state
        FROM dbo.dataset_versions
            WITH (UPDLOCK, HOLDLOCK)
        WHERE catalog_id = :catalog_id
          AND version_id = :version_id;
        """
    )

    active_query = text(
        """
        SELECT TOP 1
            version_id,
            version_number,
            lifecycle_state
        FROM dbo.dataset_versions
            WITH (UPDLOCK, HOLDLOCK)
        WHERE catalog_id = :catalog_id
          AND lifecycle_state = 'ACTIVE';
        """
    )

    supersede_query = text(
        """
        UPDATE dbo.dataset_versions
        SET
            lifecycle_state = 'SUPERSEDED',
            superseded_at = SYSUTCDATETIME(),
            lifecycle_updated_at =
                SYSUTCDATETIME()
        WHERE catalog_id = :catalog_id
          AND version_id = :version_id;
        """
    )

    activate_query = text(
        """
        UPDATE dbo.dataset_versions
        SET
            lifecycle_state = 'ACTIVE',
            promoted_at = SYSUTCDATETIME(),
            superseded_at = NULL,
            lifecycle_updated_at =
                SYSUTCDATETIME()
        WHERE catalog_id = :catalog_id
          AND version_id = :version_id;
        """
    )

    history_query = text(
        """
        INSERT INTO
            dbo.dataset_version_lifecycle_history (
                catalog_id,
                version_id,
                from_state,
                to_state,
                reason
            )
        VALUES (
            :catalog_id,
            :version_id,
            :from_state,
            :to_state,
            :reason
        );
        """
    )

    engine = get_engine()

    with engine.begin() as connection:
        target = connection.execute(
            target_query,
            {
                "catalog_id": catalog_id,
                "version_id": version_id,
            },
        ).mappings().first()

        if target is None:
            raise ValueError(
                "Không tìm thấy dataset version "
                "cần promote."
            )

        current_state = str(
            target["lifecycle_state"]
        ).upper()

        if current_state == "ACTIVE":
            return {
                "catalog_id": catalog_id,
                "version_id": version_id,
                "version_number": int(
                    target["version_number"]
                ),
                "lifecycle_state": "ACTIVE",
                "changed": False,
                "superseded_version_id": None,
            }

        if current_state != "VALIDATED":
            raise ValueError(
                "Chỉ version ở trạng thái VALIDATED "
                "mới được promote. "
                f"Trạng thái hiện tại: {current_state}"
            )

        current_active = connection.execute(
            active_query,
            {
                "catalog_id": catalog_id,
            },
        ).mappings().first()

        superseded_version_id = None

        if (
            current_active is not None
            and int(
                current_active["version_id"]
            )
            != version_id
        ):
            superseded_version_id = int(
                current_active["version_id"]
            )

            connection.execute(
                supersede_query,
                {
                    "catalog_id": catalog_id,
                    "version_id": (
                        superseded_version_id
                    ),
                },
            )

            connection.execute(
                history_query,
                {
                    "catalog_id": catalog_id,
                    "version_id": (
                        superseded_version_id
                    ),
                    "from_state": "ACTIVE",
                    "to_state": "SUPERSEDED",
                    "reason": (
                        "Replaced by promoted "
                        f"version_id={version_id}"
                    ),
                },
            )

        connection.execute(
            activate_query,
            {
                "catalog_id": catalog_id,
                "version_id": version_id,
            },
        )

        connection.execute(
            history_query,
            {
                "catalog_id": catalog_id,
                "version_id": version_id,
                "from_state": current_state,
                "to_state": "ACTIVE",
                "reason": "Version promoted to ACTIVE.",
            },
        )

    return {
        "catalog_id": catalog_id,
        "version_id": version_id,
        "version_number": int(
            target["version_number"]
        ),
        "lifecycle_state": "ACTIVE",
        "changed": True,
        "superseded_version_id": (
            superseded_version_id
        ),
    }


def get_catalog_lifecycle(
    catalog_id: int,
) -> pd.DataFrame:
    query = text(
        """
        SELECT
            version_id,
            catalog_id,
            version_number,
            content_sha256,
            file_name,
            lifecycle_state,
            promoted_at,
            superseded_at,
            lifecycle_updated_at,
            created_at
        FROM dbo.dataset_versions
        WHERE catalog_id = :catalog_id
        ORDER BY version_number DESC;
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


def get_lifecycle_history(
    version_id: int,
) -> pd.DataFrame:
    query = text(
        """
        SELECT
            lifecycle_event_id,
            catalog_id,
            version_id,
            from_state,
            to_state,
            reason,
            changed_at
        FROM dbo.dataset_version_lifecycle_history
        WHERE version_id = :version_id
        ORDER BY changed_at DESC,
                 lifecycle_event_id DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
            params={
                "version_id": int(version_id),
            },
        )