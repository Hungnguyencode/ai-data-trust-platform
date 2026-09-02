from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Mapping

import pandas as pd
from sqlalchemy import text

from database.db import get_engine


def _to_dict(
    value: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return dict(
            value.to_dict()
        )

    return dict(value)


def _parse_datetime(
    value: Any,
) -> datetime:
    if isinstance(value, datetime):
        return value

    text_value = str(
        value
    ).strip()

    if text_value.endswith("Z"):
        text_value = (
            f"{text_value[:-1]}+00:00"
        )

    return datetime.fromisoformat(
        text_value
    )


def build_rejection_reason(
    validation_result: Mapping[str, Any] | Any,
) -> str | None:
    values = _to_dict(
        validation_result
    )

    if (
        str(values.get("status"))
        != "REJECTED"
    ):
        return None

    blocking_issues = values.get(
        "blocking_issues",
        [],
    )

    if not isinstance(
        blocking_issues,
        list,
    ):
        blocking_issues = []

    reasons: list[str] = []

    for issue in blocking_issues[:10]:
        if not isinstance(
            issue,
            dict,
        ):
            continue

        issue_type = str(
            issue.get(
                "issue_type",
                "Quality issue",
            )
        )

        column_name = str(
            issue.get(
                "column_name",
                "unknown",
            )
        )

        severity = str(
            issue.get(
                "severity",
                "High",
            )
        )

        reasons.append(
            f"{issue_type} at {column_name} "
            f"(severity={severity})"
        )

    if reasons:
        return "; ".join(
            reasons
        )

    return (
        "Dataset bị Validation Gate từ chối "
        "do có blocking issue."
    )


def register_validation(
    validation_result: Mapping[str, Any] | Any,
    catalog_registration: Mapping[str, Any],
) -> dict[str, Any]:
    values = _to_dict(
        validation_result
    )

    catalog = dict(
        catalog_registration
    )

    required_validation_fields = {
        "ingestion_id",
        "status",
        "policy_version",
        "validated_at",
        "total_issues",
        "high_issues",
        "medium_issues",
        "low_issues",
        "blocking_issue_count",
        "artifact_path",
        "validation_metadata_path",
    }

    missing_validation_fields = sorted(
        field
        for field in required_validation_fields
        if values.get(field) in {None, ""}
    )

    if missing_validation_fields:
        raise ValueError(
            "Validation result thiếu field bắt buộc: "
            + ", ".join(
                missing_validation_fields
            )
        )

    required_catalog_fields = {
        "ingestion_event_id",
        "catalog_id",
        "version_id",
    }

    missing_catalog_fields = sorted(
        field
        for field in required_catalog_fields
        if catalog.get(field) in {None, ""}
    )

    if missing_catalog_fields:
        raise ValueError(
            "Catalog registration thiếu field bắt buộc: "
            + ", ".join(
                missing_catalog_fields
            )
        )

    status = str(
        values["status"]
    ).upper()

    if status not in {
        "ACCEPTED",
        "REJECTED",
    }:
        raise ValueError(
            "Validation status không hợp lệ: "
            f"{status}"
        )

    blocking_issues = values.get(
        "blocking_issues",
        [],
    )

    if not isinstance(
        blocking_issues,
        list,
    ):
        blocking_issues = []

    params = {
        "ingestion_event_id": int(
            catalog[
                "ingestion_event_id"
            ]
        ),
        "ingestion_id": str(
            values[
                "ingestion_id"
            ]
        ),
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
        "policy_version": str(
            values[
                "policy_version"
            ]
        ),
        "validation_status": status,
        "validated_at": _parse_datetime(
            values[
                "validated_at"
            ]
        ),
        "total_issues": int(
            values[
                "total_issues"
            ]
        ),
        "high_issues": int(
            values[
                "high_issues"
            ]
        ),
        "medium_issues": int(
            values[
                "medium_issues"
            ]
        ),
        "low_issues": int(
            values[
                "low_issues"
            ]
        ),
        "blocking_issue_count": int(
            values[
                "blocking_issue_count"
            ]
        ),
        "blocking_issues_json": (
            json.dumps(
                blocking_issues,
                ensure_ascii=False,
                default=str,
            )
        ),
        "artifact_path": str(
            values[
                "artifact_path"
            ]
        ),
        "validation_metadata_path": str(
            values[
                "validation_metadata_path"
            ]
        ),
        "rejection_reason": (
            build_rejection_reason(
                values
            )
        ),
    }

    existing_query = text(
        """
        SELECT TOP 1
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
            artifact_path,
            validation_metadata_path,
            rejection_reason
        FROM dbo.validation_history
        WHERE ingestion_id = :ingestion_id
          AND policy_version = :policy_version;
        """
    )

    insert_query = text(
        """
        INSERT INTO dbo.validation_history (
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
            blocking_issues_json,
            artifact_path,
            validation_metadata_path,
            rejection_reason
        )
        OUTPUT INSERTED.validation_id
        VALUES (
            :ingestion_event_id,
            :ingestion_id,
            :catalog_id,
            :version_id,
            :policy_version,
            :validation_status,
            :validated_at,
            :total_issues,
            :high_issues,
            :medium_issues,
            :low_issues,
            :blocking_issue_count,
            :blocking_issues_json,
            :artifact_path,
            :validation_metadata_path,
            :rejection_reason
        );
        """
    )

    engine = get_engine()

    with engine.begin() as connection:
        existing = connection.execute(
            existing_query,
            {
                "ingestion_id": params[
                    "ingestion_id"
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
                "is_new_validation"
            ] = False

            return result

        validation_id = connection.execute(
            insert_query,
            params,
        ).scalar_one()

    return {
        "validation_id": int(
            validation_id
        ),
        **params,
        "is_new_validation": True,
    }


def get_validation_history(
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
            vh.validation_id,
            vh.ingestion_event_id,
            vh.ingestion_id,
            vh.catalog_id,
            vh.version_id,
            dv.version_number,
            vh.policy_version,
            vh.validation_status,
            vh.validated_at,
            vh.total_issues,
            vh.high_issues,
            vh.medium_issues,
            vh.low_issues,
            vh.blocking_issue_count,
            vh.rejection_reason,
            vh.artifact_path,
            vh.validation_metadata_path
        FROM dbo.validation_history AS vh
        INNER JOIN dbo.dataset_versions AS dv
            ON vh.version_id = dv.version_id
        WHERE vh.catalog_id = :catalog_id
        ORDER BY vh.validated_at DESC;
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