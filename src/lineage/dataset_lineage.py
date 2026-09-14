from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

REQUIRED_VERSION_FIELDS = {
    "catalog_id",
    "version_id",
    "version_number",
    "file_name",
    "content_sha256",
    "lifecycle_state",
}

EVENT_STAGE_ORDER = {
    "INGESTION": 10,
    "DATA_CONTRACT": 15,
    "VALIDATION": 20,
    "GOVERNANCE": 30,
    "LIFECYCLE": 40,
}


def _to_dict(
    value: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    return dict(value)


def _timestamp_sort_value(
    value: Any,
) -> float:
    if value is None:
        return float("-inf")

    if isinstance(value, datetime):
        parsed = value

    else:
        text_value = str(value).strip()

        if text_value.endswith("Z"):
            text_value = (
                f"{text_value[:-1]}+00:00"
            )

        try:
            parsed = datetime.fromisoformat(
                text_value
            )

        except ValueError:
            return float("-inf")

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.timestamp()


def _as_bool(
    value: Any,
) -> bool:
    if isinstance(value, str):
        return (
            value.strip().lower()
            in {
                "1",
                "true",
                "yes",
            }
        )

    return bool(value)


def _latest_row(
    rows: Sequence[Mapping[str, Any]],
    *,
    timestamp_field: str,
    id_field: str,
) -> dict[str, Any] | None:
    if not rows:
        return None

    return max(
        (
            _to_dict(row)
            for row in rows
        ),
        key=lambda item: (
            _timestamp_sort_value(
                item.get(
                    timestamp_field
                )
            ),
            int(
                item.get(
                    id_field,
                    0,
                )
                or 0
            ),
        ),
    )


def build_lineage_timeline(
    *,
    ingestions: Sequence[Mapping[str, Any]],
    validations: Sequence[Mapping[str, Any]],
    lifecycle_events: Sequence[Mapping[str, Any]],
    governance_decisions: Sequence[
        Mapping[str, Any]
    ] = (),
    contract_validations: Sequence[
        Mapping[str, Any]
    ] = (),
) -> list[dict[str, Any]]:
    """
    Build one chronological lineage timeline.

    Timeline event types:
    - INGESTION
    - DATA_CONTRACT
    - VALIDATION
    - GOVERNANCE
    - LIFECYCLE
    """

    timeline: list[
        dict[str, Any]
    ] = []

    for ingestion in ingestions:
        row = _to_dict(
            ingestion
        )

        is_new_version = _as_bool(
            row.get(
                "is_new_version"
            )
        )

        event_status = (
            "NEW_VERSION"
            if is_new_version
            else "REINGESTED"
        )

        timeline.append(
            {
                "event_type": (
                    "INGESTION"
                ),
                "event_status": (
                    event_status
                ),
                "occurred_at": row.get(
                    "ingested_at"
                ),
                "reference_id": row.get(
                    "ingestion_event_id"
                ),
                "artifact_path": row.get(
                    "raw_path"
                ),
                "detail": (
                    "Dataset content registered "
                    "as a new version."
                    if is_new_version
                    else (
                        "Existing dataset version "
                        "was ingested again."
                    )
                ),
            }
        )

    for contract_validation in contract_validations:
        row = _to_dict(
            contract_validation
        )

        validation_status = str(
            row.get(
                "validation_status",
                "UNKNOWN",
            )
        ).upper()

        timeline.append(
            {
                "event_type": "DATA_CONTRACT",
                "event_status": validation_status,
                "occurred_at": row.get(
                    "validated_at"
                ),
                "reference_id": row.get(
                    "contract_validation_id"
                ),
                "artifact_path": None,
                "detail": (
                    "contract_id="
                    f"{row.get('contract_id', 'N/A')}; "
                    "contract_version="
                    f"{row.get('contract_version', 'N/A')}; "
                    "enforcement="
                    f"{row.get('enforcement_mode', 'N/A')}; "
                    "violations="
                    f"{row.get('violation_count', 0)}"
                ),
            }
        )

    for validation in validations:
        row = _to_dict(
            validation
        )

        validation_status = str(
            row.get(
                "validation_status",
                "UNKNOWN",
            )
        ).upper()

        timeline.append(
            {
                "event_type": (
                    "VALIDATION"
                ),
                "event_status": (
                    validation_status
                ),
                "occurred_at": row.get(
                    "validated_at"
                ),
                "reference_id": row.get(
                    "validation_id"
                ),
                "artifact_path": row.get(
                    "artifact_path"
                ),
                "detail": (
                    "policy="
                    f"{row.get('policy_version', 'N/A')}; "
                    "high_issues="
                    f"{row.get('high_issues', 0)}; "
                    "blocking_issues="
                    f"{row.get('blocking_issue_count', 0)}"
                ),
            }
        )

    for governance in governance_decisions:
        row = _to_dict(
            governance
        )

        decision = str(
            row.get(
                "decision",
                "UNKNOWN",
            )
        ).upper()

        promotion_eligible = (
            _as_bool(
                row.get(
                    "promotion_eligible"
                )
            )
        )

        timeline.append(
            {
                "event_type": (
                    "GOVERNANCE"
                ),
                "event_status": (
                    decision
                ),
                "occurred_at": row.get(
                    "created_at"
                ),
                "reference_id": row.get(
                    "governance_id"
                ),
                "artifact_path": None,
                "detail": (
                    "policy="
                    f"{row.get('policy_version', 'N/A')}; "
                    "validation_id="
                    f"{row.get('validation_id', 'N/A')}; "
                    "trust_score="
                    f"{row.get('trust_score', 'N/A')}; "
                    "privacy="
                    f"{row.get('privacy_status', 'N/A')}; "
                    "promotion_eligible="
                    f"{promotion_eligible}; "
                    "reason="
                    f"{row.get('reason', 'N/A')}"
                ),
            }
        )

    for lifecycle_event in lifecycle_events:
        row = _to_dict(
            lifecycle_event
        )

        from_state = (
            str(
                row.get(
                    "from_state"
                )
            )
            if row.get(
                "from_state"
            )
            is not None
            else "NONE"
        )

        to_state = str(
            row.get(
                "to_state",
                "UNKNOWN",
            )
        )

        timeline.append(
            {
                "event_type": (
                    "LIFECYCLE"
                ),
                "event_status": (
                    f"{from_state} -> "
                    f"{to_state}"
                ),
                "occurred_at": row.get(
                    "changed_at"
                ),
                "reference_id": row.get(
                    "lifecycle_event_id"
                ),
                "artifact_path": None,
                "detail": row.get(
                    "reason"
                ),
            }
        )

    timeline.sort(
        key=lambda item: (
            _timestamp_sort_value(
                item.get(
                    "occurred_at"
                )
            ),
            EVENT_STAGE_ORDER.get(
                str(
                    item.get(
                        "event_type",
                        "",
                    )
                ),
                999,
            ),
            str(
                item.get(
                    "reference_id",
                    "",
                )
            ),
        )
    )

    return timeline


def build_version_lineage(
    *,
    version: Mapping[str, Any],
    ingestions: Sequence[Mapping[str, Any]],
    validations: Sequence[Mapping[str, Any]],
    lifecycle_events: Sequence[Mapping[str, Any]],
    governance_decisions: Sequence[
        Mapping[str, Any]
    ] = (),
    contract_validations: Sequence[
        Mapping[str, Any]
    ] = (),
) -> dict[str, Any]:
    """
    Build the complete lineage read model
    for one dataset version.

    Promotion eligibility is intentionally
    stricter than lifecycle eligibility:

    lifecycle_eligible:
        lifecycle state is VALIDATED

    governance_approved:
        governance for the latest validation
        is APPROVED and allows promotion

    promotion_eligible:
        both conditions are true
    """

    version_row = _to_dict(
        version
    )

    missing_fields = sorted(
        field
        for field
        in REQUIRED_VERSION_FIELDS
        if version_row.get(
            field
        )
        is None
    )

    if missing_fields:
        raise ValueError(
            "Dataset version thiếu lineage "
            "field bắt buộc: "
            + ", ".join(
                missing_fields
            )
        )

    ingestion_rows = [
        _to_dict(item)
        for item in ingestions
    ]

    validation_rows = [
        _to_dict(item)
        for item in validations
    ]

    contract_validation_rows = [
        _to_dict(item)
        for item in contract_validations
    ]

    governance_rows = [
        _to_dict(item)
        for item
        in governance_decisions
    ]

    lifecycle_rows = [
        _to_dict(item)
        for item
        in lifecycle_events
    ]

    timeline = (
        build_lineage_timeline(
            ingestions=(
                ingestion_rows
            ),
            validations=(
                validation_rows
            ),
            governance_decisions=(
                governance_rows
            ),
            lifecycle_events=(
                lifecycle_rows
            ),
            contract_validations=(
                contract_validation_rows
            ),
        )
    )

    latest_validation = _latest_row(
        validation_rows,
        timestamp_field="validated_at",
        id_field="validation_id",
    )

    latest_contract_validation = _latest_row(
        contract_validation_rows,
        timestamp_field="validated_at",
        id_field="contract_validation_id",
    )

    current_governance = None

    if latest_validation is not None:
        latest_validation_id = int(
            latest_validation[
                "validation_id"
            ]
        )

        governance_for_validation = [
            row
            for row in governance_rows
            if int(
                row.get(
                    "validation_id",
                    -1,
                )
                or -1
            )
            == latest_validation_id
        ]

        current_governance = (
            _latest_row(
                governance_for_validation,
                timestamp_field=(
                    "created_at"
                ),
                id_field=(
                    "governance_id"
                ),
            )
        )

    lifecycle_state = str(
        version_row[
            "lifecycle_state"
        ]
    ).upper()

    lifecycle_eligible = (
        lifecycle_state
        == "VALIDATED"
    )

    governance_approved = (
        current_governance
        is not None
        and str(
            current_governance.get(
                "decision",
                "",
            )
        ).upper()
        == "APPROVED"
        and _as_bool(
            current_governance.get(
                "promotion_eligible"
            )
        )
    )

    promotion_eligible = (
        lifecycle_eligible
        and governance_approved
    )

    summary = {
        "catalog_id": int(
            version_row[
                "catalog_id"
            ]
        ),
        "version_id": int(
            version_row[
                "version_id"
            ]
        ),
        "version_number": int(
            version_row[
                "version_number"
            ]
        ),
        "file_name": str(
            version_row[
                "file_name"
            ]
        ),
        "content_sha256": str(
            version_row[
                "content_sha256"
            ]
        ),
        "lifecycle_state": (
            lifecycle_state
        ),
        "raw_path": version_row.get(
            "raw_path"
        ),
        "ingestion_count": len(
            ingestion_rows
        ),
        "validation_count": len(
            validation_rows
        ),
        "governance_count": len(
            governance_rows
        ),
        "lifecycle_event_count": len(
            lifecycle_rows
        ),
        "latest_validation_id": (
            int(
                latest_validation[
                    "validation_id"
                ]
            )
            if latest_validation
            else None
        ),
        "latest_validation_status": (
            str(
                latest_validation[
                    "validation_status"
                ]
            ).upper()
            if latest_validation
            else None
        ),
        "latest_governance_id": (
            int(
                current_governance[
                    "governance_id"
                ]
            )
            if current_governance
            else None
        ),
        "latest_governance_decision": (
            str(
                current_governance[
                    "decision"
                ]
            ).upper()
            if current_governance
            else None
        ),
        "latest_governance_policy": (
            str(
                current_governance[
                    "policy_version"
                ]
            )
            if current_governance
            else None
        ),
        "latest_trust_score": (
            float(
                current_governance[
                    "trust_score"
                ]
            )
            if current_governance
            else None
        ),
        "latest_privacy_status": (
            str(
                current_governance[
                    "privacy_status"
                ]
            ).upper()
            if current_governance
            else None
        ),
        "lifecycle_eligible": (
            lifecycle_eligible
        ),
        "governance_approved": (
            governance_approved
        ),
        "promotion_eligible": (
            promotion_eligible
        ),
        "is_active": (
            lifecycle_state
            == "ACTIVE"
        ),
                "contract_validation_count": len(
            contract_validation_rows
        ),
        "latest_contract_validation_id": (
            int(
                latest_contract_validation[
                    "contract_validation_id"
                ]
            )
            if latest_contract_validation
            else None
        ),
        "latest_contract_id": (
            int(
                latest_contract_validation[
                    "contract_id"
                ]
            )
            if latest_contract_validation
            else None
        ),
        "latest_contract_version": (
            int(
                latest_contract_validation[
                    "contract_version"
                ]
            )
            if latest_contract_validation
            and latest_contract_validation.get(
                "contract_version"
            )
            is not None
            else None
        ),
        "latest_contract_validation_status": (
            str(
                latest_contract_validation[
                    "validation_status"
                ]
            ).upper()
            if latest_contract_validation
            else None
        ),
        "latest_contract_enforcement_mode": (
            str(
                latest_contract_validation[
                    "enforcement_mode"
                ]
            ).upper()
            if latest_contract_validation
            and latest_contract_validation.get(
                "enforcement_mode"
            )
            is not None
            else None
        ),
        "latest_contract_violation_count": (
            int(
                latest_contract_validation.get(
                    "violation_count",
                    0,
                )
            )
            if latest_contract_validation
            else None
        ),
    }

    return {
        "summary": summary,
        "version": version_row,
        "ingestions": (
            ingestion_rows
        ),
        "validations": (
            validation_rows
        ),
        "governance_decisions": (
            governance_rows
        ),
        "lifecycle_events": (
            lifecycle_rows
        ),
        "timeline": timeline,
                "contract_validations": (
            contract_validation_rows
        ),
    }