from __future__ import annotations

from typing import Any, Mapping

VALID_LIFECYCLE_STATES = {
    "NEW",
    "VALIDATED",
    "QUARANTINED",
    "ACTIVE",
    "SUPERSEDED",
}


def lifecycle_state_from_validation(
    validation_status: str,
) -> str:
    status = str(validation_status).strip().upper()

    if status == "ACCEPTED":
        return "VALIDATED"

    if status == "REJECTED":
        return "QUARANTINED"

    raise ValueError(
        "Validation status không hợp lệ: "
        f"{validation_status}"
    )


def is_promotion_eligible(
    lifecycle_state: str,
) -> bool:
    return (
        str(lifecycle_state)
        .strip()
        .upper()
        == "VALIDATED"
    )


def is_governed_promotion_eligible(
    lifecycle_state: str,
    governance_decision: Mapping[str, Any] | None,
) -> bool:
    """
    Final promotion gate.

    A version can be promoted only when:
    - lifecycle state is VALIDATED
    - governance decision exists
    - decision is APPROVED
    - promotion_eligible is True
    """

    if not is_promotion_eligible(
        lifecycle_state
    ):
        return False

    if governance_decision is None:
        return False

    decision = str(
        governance_decision.get(
            "decision",
            "",
        )
    ).strip().upper()

    eligible_value = (
        governance_decision.get(
            "promotion_eligible",
            False,
        )
    )

    if isinstance(
        eligible_value,
        str,
    ):
        eligible = (
            eligible_value.strip().lower()
            in {
                "1",
                "true",
                "yes",
            }
        )
    else:
        eligible = bool(
            eligible_value
        )

    return (
        decision == "APPROVED"
        and eligible
    )


def lifecycle_summary(
    *,
    lifecycle_state: str,
) -> dict[str, Any]:
    state = (
        str(lifecycle_state)
        .strip()
        .upper()
    )

    if state not in VALID_LIFECYCLE_STATES:
        raise ValueError(
            "Lifecycle state không hợp lệ: "
            f"{lifecycle_state}"
        )

    descriptions = {
        "NEW": (
            "Version mới được ingest và chưa có "
            "kết luận validation."
        ),
        "VALIDATED": (
            "Version đã qua Validation Gate. "
            "Governance Decision sẽ quyết định "
            "version có được promote hay không."
        ),
        "QUARANTINED": (
            "Version bị Validation Gate reject "
            "và không được dùng chính thức."
        ),
        "ACTIVE": (
            "Version chính thức hiện tại của "
            "logical dataset."
        ),
        "SUPERSEDED": (
            "Version từng được active nhưng đã "
            "được thay thế bởi version mới hơn."
        ),
    }

    return {
        "state": state,
        "promotion_eligible": (
            is_promotion_eligible(state)
        ),
        "description": descriptions[state],
    }


def get_validation_status(
    validation_result: Mapping[str, Any],
) -> str:
    status = validation_result.get("status")

    if status is None:
        raise ValueError(
            "Validation result thiếu status."
        )

    return str(status).upper()