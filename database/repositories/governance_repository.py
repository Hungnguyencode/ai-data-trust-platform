from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
from sqlalchemy import text

from database.db import get_engine
from src.governance.governance_engine import (
    GovernanceResult,
)


def _to_dict(
    value: GovernanceResult | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(
        value,
        GovernanceResult,
    ):
        return value.to_dict()

    return dict(
        value
    )


def register_governance_decision(
    *,
    governance_result: GovernanceResult
    | Mapping[str, Any],
    catalog_registration: Mapping[str, Any],
    validation_registration: Mapping[str, Any],
) -> dict[str, Any]:
    governance = _to_dict(
        governance_result
    )

    catalog = dict(
        catalog_registration
    )

    validation = dict(
        validation_registration
    )

    required_governance_fields = {
        "decision",
        "reason",
        "promotion_eligible",
        "policy_version",
        "validation_status",
        "trust_score",
        "privacy_status",
        "blocking_issue_count",
    }

    missing_governance_fields = sorted(
        field
        for field in required_governance_fields
        if governance.get(field) is None
    )

    if missing_governance_fields:
        raise ValueError(
            "Governance result thiếu field bắt buộc: "
            + ", ".join(
                missing_governance_fields
            )
        )

    params = {
        "catalog_id": int(
            catalog[
                "catalog_id"
            ]
        ),
        "version_id": int(
            catalog[
                "version_id"
            ]
        ),
        "validation_id": int(
            validation[
                "validation_id"
            ]
        ),
        "policy_version": str(
            governance[
                "policy_version"
            ]
        ),
        "decision": str(
            governance[
                "decision"
            ]
        ).upper(),
        "reason": str(
            governance[
                "reason"
            ]
        ),
        "promotion_eligible": bool(
            governance[
                "promotion_eligible"
            ]
        ),
        "trust_score": float(
            governance[
                "trust_score"
            ]
        ),
        "validation_status": str(
            governance[
                "validation_status"
            ]
        ).upper(),
        "privacy_status": str(
            governance[
                "privacy_status"
            ]
        ).upper(),
        "blocking_issue_count": int(
            governance[
                "blocking_issue_count"
            ]
        ),
    }

    existing_query = text(
        """
        SELECT TOP 1
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
          AND validation_id = :validation_id
          AND policy_version = :policy_version;
        """
    )

    insert_query = text(
        """
        INSERT INTO dbo.governance_decisions (
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
            blocking_issue_count
        )
        OUTPUT INSERTED.governance_id
        VALUES (
            :catalog_id,
            :version_id,
            :validation_id,
            :policy_version,
            :decision,
            :reason,
            :promotion_eligible,
            :trust_score,
            :validation_status,
            :privacy_status,
            :blocking_issue_count
        );
        """
    )

    engine = get_engine()

    with engine.begin() as connection:
        existing = connection.execute(
            existing_query,
            {
                "version_id": params[
                    "version_id"
                ],
                "validation_id": params[
                    "validation_id"
                ],
                "policy_version": params[
                    "policy_version"
                ],
            },
        ).mappings().first()

        if existing is not None:
            result = dict(
                existing
            )

            result[
                "is_new_decision"
            ] = False

            return result

        governance_id = connection.execute(
            insert_query,
            params,
        ).scalar_one()

    return {
        "governance_id": int(
            governance_id
        ),
        **params,
        "is_new_decision": True,
    }


def get_governance_history(
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
            gd.governance_id,
            gd.catalog_id,
            gd.version_id,
            dv.version_number,
            gd.validation_id,
            gd.policy_version,
            gd.decision,
            gd.reason,
            gd.promotion_eligible,
            gd.trust_score,
            gd.validation_status,
            gd.privacy_status,
            gd.blocking_issue_count,
            gd.created_at
        FROM dbo.governance_decisions AS gd
        INNER JOIN dbo.dataset_versions AS dv
            ON gd.version_id = dv.version_id
        WHERE gd.catalog_id = :catalog_id
        ORDER BY
            gd.created_at DESC,
            gd.governance_id DESC;
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


def get_latest_governance_decision(
    version_id: int,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT TOP 1
            gd.governance_id,
            gd.catalog_id,
            gd.version_id,
            gd.validation_id,
            gd.policy_version,
            gd.decision,
            gd.reason,
            gd.promotion_eligible,
            gd.trust_score,
            gd.validation_status,
            gd.privacy_status,
            gd.blocking_issue_count,
            gd.created_at
        FROM dbo.governance_decisions AS gd
        WHERE gd.version_id = :version_id
          AND gd.validation_id = (
                SELECT TOP 1
                    vh.validation_id
                FROM dbo.validation_history AS vh
                WHERE vh.version_id = :version_id
                ORDER BY
                    vh.validated_at DESC,
                    vh.validation_id DESC
          )
        ORDER BY
            gd.created_at DESC,
            gd.governance_id DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "version_id": int(
                    version_id
                ),
            },
        ).mappings().first()

    return (
        dict(row)
        if row is not None
        else None
    )