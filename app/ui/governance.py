from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_governance_summary(
    result: Mapping[str, Any] | None,
) -> dict[str, str]:
    data = result if isinstance(result, Mapping) else {}

    decision = str(data.get("decision") or "").strip().upper()
    privacy = str(data.get("privacy_status") or "Unknown").strip()
    reason = str(data.get("reason") or "").strip()

    eligible = data.get("promotion_eligible")
    if eligible is True:
        promotion = "YES"
    elif eligible is False:
        promotion = "NO"
    else:
        promotion = "Unknown"

    return {
        "decision": decision or "Not evaluated",
        "privacy_status": privacy,
        "reason": reason,
        "promotion_eligible": promotion,
    }
