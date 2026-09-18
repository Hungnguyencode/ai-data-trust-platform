from __future__ import annotations

from typing import Any

SUPPORTED_STATES = {
    "ACTION_REQUIRED",
    "ATTENTION",
    "HEALTHY",
    "UNKNOWN",
}


def _mapping(
    value: Any,
) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    return {}


def _records(
    value: Any,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    return [
        item
        for item in value
        if isinstance(item, dict)
    ]


def _positive_int(
    value: Any,
    *,
    field_name: str,
) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ValueError(
            f"{field_name} must be "
            "a positive integer."
        )

    return value


def _normalize_state(
    value: Any,
) -> str:
    state = str(
        value or "UNKNOWN"
    ).strip().upper()

    if state not in SUPPORTED_STATES:
        return "UNKNOWN"

    return state


def _finding_code(
    finding: dict[str, Any],
) -> str:
    return str(
        finding.get(
            "code",
            "UNKNOWN_FINDING",
        )
    ).strip()


def _action_code(
    action: dict[str, Any],
) -> str:
    return str(
        action.get(
            "code",
            "UNKNOWN_ACTION",
        )
    ).strip()


def _finding_markdown(
    finding: dict[str, Any],
) -> str:
    code = _finding_code(
        finding
    )

    category = str(
        finding.get(
            "category",
            "UNKNOWN",
        )
    ).strip().upper()

    severity = str(
        finding.get(
            "severity",
            "INFO",
        )
    ).strip().upper()

    message = str(
        finding.get(
            "message",
            "No explanation is available.",
        )
    ).strip()

    return (
        f"- **{severity} | {category}** - "
        f"{message} (`{code}`)"
    )


def _action_markdown(
    action: dict[str, Any],
    *,
    position: int,
) -> str:
    code = _action_code(
        action
    )

    action_text = str(
        action.get(
            "action",
            "No action description is available.",
        )
    ).strip()

    reason = str(
        action.get(
            "reason",
            "No reason is available.",
        )
    ).strip()

    priority = action.get(
        "priority"
    )

    priority_text = (
        str(priority)
        if priority is not None
        else "N/A"
    )

    return (
        f"{position}. **{code}** "
        f"(priority {priority_text}) - "
        f"{action_text}\n"
        f"   - Why: {reason}"
    )


def _headline(
    state: str,
) -> str:
    mapping = {
        "ACTION_REQUIRED": (
            "Action is required before "
            "trusted downstream use."
        ),
        "ATTENTION": (
            "The dataset needs attention "
            "before normal downstream use."
        ),
        "HEALTHY": (
            "Current platform evidence "
            "does not show a blocking issue."
        ),
        "UNKNOWN": (
            "There is not enough evidence "
            "for a reliable platform diagnosis."
        ),
    }

    return mapping[state]


def _summary_text(
    *,
    state: str,
    latest_version_id: int | None,
    findings: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> str:
    high_count = sum(
        1
        for finding in findings
        if str(
            finding.get(
                "severity",
                "",
            )
        ).strip().upper()
        in {
            "HIGH",
            "CRITICAL",
        }
    )

    warning_count = sum(
        1
        for finding in findings
        if str(
            finding.get(
                "severity",
                "",
            )
        ).strip().upper()
        == "WARNING"
    )

    version_text = (
        f"Dataset version {latest_version_id}"
        if latest_version_id
        is not None
        else "The dataset"
    )

    if state == "ACTION_REQUIRED":
        return (
            f"{version_text} requires action. "
            f"The deterministic diagnosis found "
            f"{high_count} high-severity finding(s), "
            f"{warning_count} warning(s), and "
            f"{len(actions)} recommended action(s)."
        )

    if state == "ATTENTION":
        return (
            f"{version_text} has no blocking "
            "high-severity diagnosis, but "
            f"{warning_count} warning(s) require "
            "attention."
        )

    if state == "HEALTHY":
        return (
            f"{version_text} currently has no "
            "high-severity or warning diagnosis "
            "in the supplied platform evidence."
        )

    return (
        f"{version_text} does not have enough "
        "platform evidence for a reliable "
        "explanation."
    )


def _sorted_actions(
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def priority(
        item: dict[str, Any],
    ) -> int:
        try:
            return int(
                item.get(
                    "priority",
                    9999,
                )
            )
        except (TypeError, ValueError):
            return 9999

    return sorted(
        actions,
        key=priority,
    )


def _build_explanation_markdown(
    *,
    headline: str,
    summary: str,
    findings: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> str:
    lines = [
        "### Platform diagnosis",
        "",
        f"**{headline}**",
        "",
        summary,
    ]

    if findings:
        lines.extend(
            [
                "",
                "#### Evidence",
                "",
            ]
        )

        lines.extend(
            _finding_markdown(
                finding
            )
            for finding in findings
        )

    else:
        lines.extend(
            [
                "",
                "#### Evidence",
                "",
                (
                    "- No structured finding "
                    "was supplied."
                ),
            ]
        )

    lines.extend(
        [
            "",
            "#### Recommended next steps",
            "",
        ]
    )

    if actions:
        for position, action in enumerate(
            actions,
            start=1,
        ):
            lines.append(
                _action_markdown(
                    action,
                    position=position,
                )
            )
    else:
        lines.append(
            (
                "No corrective action is "
                "currently recommended by "
                "the deterministic reasoning "
                "engine."
            )
        )

    lines.extend(
        [
            "",
            "#### Grounding",
            "",
            (
                "This explanation is generated "
                "only from the structured "
                "platform diagnosis. It does "
                "not introduce external facts "
                "or unsupported conclusions."
            ),
        ]
    )

    return "\n".join(lines)


def explain_platform_diagnosis(
    diagnosis: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(
        diagnosis,
        dict,
    ):
        raise ValueError(
            "diagnosis must be a dictionary."
        )

    catalog_id = _positive_int(
        diagnosis.get(
            "catalog_id"
        ),
        field_name=(
            "diagnosis.catalog_id"
        ),
    )

    latest_version_value = (
        diagnosis.get(
            "latest_version_id"
        )
    )

    latest_version_id = None

    if latest_version_value is not None:
        latest_version_id = (
            _positive_int(
                latest_version_value,
                field_name=(
                    "diagnosis.latest_version_id"
                ),
            )
        )

    state = _normalize_state(
        diagnosis.get(
            "overall_state"
        )
    )

    findings = _records(
        diagnosis.get(
            "findings"
        )
    )

    actions = _sorted_actions(
        _records(
            diagnosis.get(
                "recommended_actions"
            )
        )
    )

    headline = _headline(
        state
    )

    summary = _summary_text(
        state=state,
        latest_version_id=(
            latest_version_id
        ),
        findings=findings,
        actions=actions,
    )

    explanation = (
        _build_explanation_markdown(
            headline=headline,
            summary=summary,
            findings=findings,
            actions=actions,
        )
    )

    return {
        "catalog_id": catalog_id,
        "latest_version_id": (
            latest_version_id
        ),
        "overall_state": state,
        "headline": headline,
        "summary": summary,
        "explanation": explanation,
        "source_finding_codes": [
            _finding_code(
                finding
            )
            for finding in findings
        ],
        "source_action_codes": [
            _action_code(
                action
            )
            for action in actions
        ],
    }