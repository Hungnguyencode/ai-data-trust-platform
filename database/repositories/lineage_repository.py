from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import text

from database.db import get_engine
from src.lineage.dataset_lineage import (
    build_version_lineage,
)


def get_version_lineage(
    version_id: int,
) -> dict[str, Any]:
    """
    Return end-to-end lineage for one dataset version.

    Sources:
    - dataset_catalog
    - dataset_versions
    - ingestion_history
    - validation_history
    - governance_decisions
    - dataset_version_lifecycle_history
    """

    version_id = int(
        version_id
    )

    version_query = text(
        """
        SELECT
            dc.catalog_id,
            dc.dataset_key,
            dc.display_name,
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
            dv.lifecycle_state,
            dv.promoted_at,
            dv.superseded_at,
            dv.lifecycle_updated_at,
            dv.created_at
        FROM dbo.dataset_versions AS dv
        INNER JOIN dbo.dataset_catalog AS dc
            ON dv.catalog_id = dc.catalog_id
        WHERE dv.version_id = :version_id;
        """
    )

    ingestion_query = text(
        """
        SELECT
            ingestion_event_id,
            ingestion_id,
            catalog_id,
            version_id,
            source_type,
            ingested_at,
            raw_path,
            is_new_version,
            created_at
        FROM dbo.ingestion_history
        WHERE version_id = :version_id
        ORDER BY
            ingested_at ASC,
            ingestion_event_id ASC;
        """
    )

    contract_validation_query = text(
        """
        SELECT
            cvh.contract_validation_id,
            cvh.contract_id,
            cvh.catalog_id,
            cvh.version_id,
            dc.contract_version,
            dc.contract_name,
            dc.enforcement_mode,
            cvh.validation_status,
            cvh.missing_required_count,
            cvh.unexpected_column_count,
            cvh.type_mismatch_count,
            cvh.nullability_violation_count,
            cvh.violation_count,
            cvh.validated_at
        FROM dbo.contract_validation_history AS cvh
        INNER JOIN dbo.data_contracts AS dc
            ON cvh.contract_id = dc.contract_id
        WHERE cvh.version_id = :version_id
        ORDER BY
            cvh.validated_at ASC,
            cvh.contract_validation_id ASC;
        """
    )

    contract_violation_query = text(
        """
        SELECT
            cv.violation_id,
            cv.contract_validation_id,
            cv.column_name,
            cv.violation_type,
            cv.expected_value,
            cv.actual_value,
            cv.message,
            cv.created_at
        FROM dbo.contract_violations AS cv
        INNER JOIN dbo.contract_validation_history AS cvh
            ON cv.contract_validation_id =
                cvh.contract_validation_id
        WHERE cvh.version_id = :version_id
        ORDER BY
            cv.contract_validation_id ASC,
            cv.violation_id ASC;
        """
    )

    validation_query = text(
        """
        SELECT
            validation_id,
            ingestion_event_id,
            ingestion_id,
            catalog_id,
            version_id,
            policy_version,
            validation_status,
            validated_at,
            total_issues,
            high_issues,
            medium_issues,
            low_issues,
            blocking_issue_count,
            rejection_reason,
            artifact_path,
            validation_metadata_path,
            created_at
        FROM dbo.validation_history
        WHERE version_id = :version_id
        ORDER BY
            validated_at ASC,
            validation_id ASC;
        """
    )

    governance_query = text(
        """
        SELECT
            governance_id,
            catalog_id,
            version_id,
            validation_id,
            policy_version,
            decision,
            reason,
            promotion_eligible,
            trust_score,
            validation_status,
            privacy_status,
            blocking_issue_count,
            created_at
        FROM dbo.governance_decisions
        WHERE version_id = :version_id
        ORDER BY
            created_at ASC,
            governance_id ASC;
        """
    )

    lifecycle_query = text(
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
        ORDER BY
            changed_at ASC,
            lifecycle_event_id ASC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        version = connection.execute(
            version_query,
            {
                "version_id": (
                    version_id
                ),
            },
        ).mappings().first()

        if version is None:
            raise ValueError(
                "Không tìm thấy dataset version "
                f"version_id={version_id}."
            )

        ingestions = [
            dict(row)
            for row
            in connection.execute(
                ingestion_query,
                {
                    "version_id": (
                        version_id
                    ),
                },
            ).mappings().all()
        ]

        contract_validations = [
            dict(row)
            for row in connection.execute(
                contract_validation_query,
                {
                    "version_id": version_id,
                },
            ).mappings().all()
        ]

        contract_violations = [
            dict(row)
            for row in connection.execute(
                contract_violation_query,
                {
                    "version_id": version_id,
                },
            ).mappings().all()
        ]

        violations_by_validation: dict[
            int,
            list[dict[str, Any]],
        ] = {}

        for violation in contract_violations:
            contract_validation_id = int(
                violation[
                    "contract_validation_id"
                ]
            )

            violations_by_validation.setdefault(
                contract_validation_id,
                [],
            ).append(
                violation
            )

        for contract_validation in contract_validations:
            contract_validation_id = int(
                contract_validation[
                    "contract_validation_id"
                ]
            )

            contract_validation[
                "violations"
            ] = violations_by_validation.get(
                contract_validation_id,
                [],
            )

        validations = [
            dict(row)
            for row
            in connection.execute(
                validation_query,
                {
                    "version_id": (
                        version_id
                    ),
                },
            ).mappings().all()
        ]

        governance_decisions = [
            dict(row)
            for row
            in connection.execute(
                governance_query,
                {
                    "version_id": (
                        version_id
                    ),
                },
            ).mappings().all()
        ]

        lifecycle_events = [
            dict(row)
            for row
            in connection.execute(
                lifecycle_query,
                {
                    "version_id": (
                        version_id
                    ),
                },
            ).mappings().all()
        ]

    return build_version_lineage(
        version=dict(
            version
        ),
        ingestions=ingestions,
        validations=validations,
        governance_decisions=(
            governance_decisions
        ),
        lifecycle_events=(
            lifecycle_events
        ),
        contract_validations=(
            contract_validations
        ),
    )


def get_catalog_lineage(
    catalog_id: int,
) -> pd.DataFrame:
    """
    Return one summary row for every version
    in a logical dataset.
    """

    query = text(
        """
        SELECT
            dv.catalog_id,
            dv.version_id,
            dv.version_number,
            dv.file_name,
            dv.content_sha256,
            dv.lifecycle_state,
            dv.raw_path,
            dv.promoted_at,
            dv.superseded_at,
            dv.created_at,

            (
                SELECT COUNT(*)
                FROM dbo.ingestion_history AS ih
                WHERE ih.version_id = dv.version_id
            ) AS ingestion_count,

            (
                SELECT COUNT(*)
                FROM dbo.validation_history AS vh
                WHERE vh.version_id = dv.version_id
            ) AS validation_count,

            (
                SELECT COUNT(*)
                FROM dbo.governance_decisions AS gd_count
                WHERE gd_count.version_id = dv.version_id
            ) AS governance_count,

            latest_validation.validation_id
                AS latest_validation_id,

            latest_validation.validation_status
                AS latest_validation_status,

            latest_validation.validated_at
                AS latest_validated_at,

            latest_validation.artifact_path
                AS latest_artifact_path,

            latest_governance.governance_id
                AS latest_governance_id,

            latest_governance.decision
                AS latest_governance_decision,

            latest_governance.policy_version
                AS latest_governance_policy,

            latest_governance.trust_score
                AS latest_trust_score,

            latest_governance.privacy_status
                AS latest_privacy_status,

            CASE
                WHEN dv.lifecycle_state = 'VALIDATED'
                THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END AS lifecycle_eligible,

            CASE
                WHEN
                    latest_governance.decision = 'APPROVED'
                    AND latest_governance.promotion_eligible = 1
                THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END AS governance_approved,

            CASE
                WHEN
                    dv.lifecycle_state = 'VALIDATED'
                    AND latest_governance.decision = 'APPROVED'
                    AND latest_governance.promotion_eligible = 1
                THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END AS promotion_eligible

        FROM dbo.dataset_versions AS dv

        OUTER APPLY (
            SELECT TOP 1
                vh.validation_id,
                vh.validation_status,
                vh.validated_at,
                vh.artifact_path
            FROM dbo.validation_history AS vh
            WHERE vh.version_id = dv.version_id
            ORDER BY
                vh.validated_at DESC,
                vh.validation_id DESC
        ) AS latest_validation

        OUTER APPLY (
            SELECT TOP 1
                gd.governance_id,
                gd.decision,
                gd.policy_version,
                gd.promotion_eligible,
                gd.trust_score,
                gd.privacy_status,
                gd.created_at
            FROM dbo.governance_decisions AS gd
            WHERE gd.version_id = dv.version_id
              AND gd.validation_id =
                    latest_validation.validation_id
            ORDER BY
                gd.created_at DESC,
                gd.governance_id DESC
        ) AS latest_governance

        WHERE dv.catalog_id = :catalog_id

        ORDER BY
            dv.version_number DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
            params={
                "catalog_id": int(
                    catalog_id
                ),
            },
        )