from __future__ import annotations

from typing import Any

SEVERITY_RANK = {
    "INFO": 0,
    "WARNING": 1,
    "HIGH": 2,
    "CRITICAL": 3,
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


def _status(
    record: dict[str, Any] | None,
    *keys: str,
) -> str | None:
    if not record:
        return None

    for key in keys:
        value = record.get(key)

        if value is None:
            continue

        text = str(value).strip().upper()

        if text:
            return text

    return None


def _latest_version_record(
    context: dict[str, Any],
    version_id: int | None,
) -> dict[str, Any] | None:
    if version_id is None:
        return None

    dataset = _mapping(
        context.get("dataset")
    )

    history = _records(
        dataset.get("version_history")
    )

    for record in history:
        record_version_id = record.get(
            "version_id"
        )

        try:
            if int(record_version_id) == version_id:
                return record
        except (TypeError, ValueError):
            continue

    return None


def _lifecycle_state(
    context: dict[str, Any],
    version_id: int | None,
) -> str | None:
    dataset = _mapping(
        context.get("dataset")
    )

    lineage = _mapping(
        dataset.get("lineage")
    )

    lineage_summary = _mapping(
        lineage.get("summary")
    )

    lifecycle_state = _status(
        lineage_summary,
        "lifecycle_state",
        "state",
    )

    if lifecycle_state is not None:
        return lifecycle_state

    version_record = _latest_version_record(
        context,
        version_id,
    )

    return _status(
        version_record,
        "lifecycle_state",
        "state",
    )


def _add_finding(
    findings: list[dict[str, Any]],
    *,
    code: str,
    category: str,
    severity: str,
    message: str,
    evidence: dict[str, Any] | None = None,
) -> None:
    normalized_severity = (
        severity.strip().upper()
    )

    if normalized_severity not in SEVERITY_RANK:
        raise ValueError(
            f"Unsupported finding severity: {severity}"
        )

    findings.append(
        {
            "code": code,
            "category": category,
            "severity": normalized_severity,
            "message": message,
            "evidence": evidence or {},
        }
    )


def _add_action(
    actions: list[dict[str, Any]],
    *,
    code: str,
    priority: int,
    action: str,
    reason: str,
) -> None:
    actions.append(
        {
            "code": code,
            "priority": priority,
            "action": action,
            "reason": reason,
        }
    )


def _evaluate_validation(
    *,
    validation: dict[str, Any],
    version_id: int | None,
    findings: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> None:
    record = _mapping(
        validation.get("latest_version")
    )

    status = _status(
        record,
        "validation_status",
        "status",
    )

    quality_evidence = {
        "version_id": version_id,
        "validation_id": record.get(
            "validation_id"
        ),
        "total_issues": record.get(
            "total_issues"
        ),
        "high_issues": record.get(
            "high_issues"
        ),
        "medium_issues": record.get(
            "medium_issues"
        ),
        "low_issues": record.get(
            "low_issues"
        ),
        "blocking_issue_count": record.get(
            "blocking_issue_count"
        ),
    }

    quality_count_keys = (
        "total_issues",
        "high_issues",
        "medium_issues",
        "low_issues",
        "blocking_issue_count",
    )

    has_quality_summary = any(
        quality_evidence[key] is not None
        for key in quality_count_keys
    )

    if has_quality_summary:
        _add_finding(
            findings,
            code="QUALITY_SUMMARY_RECORDED",
            category="QUALITY",
            severity="INFO",
            message=(
                "The latest dataset version "
                "has persisted quality summary: "
                f"{quality_evidence['total_issues']} total issues, "
                f"{quality_evidence['high_issues']} high, "
                f"{quality_evidence['medium_issues']} medium, "
                f"{quality_evidence['low_issues']} low, "
                f"and "
                f"{quality_evidence['blocking_issue_count']} "
                "blocking."
            ),
            evidence=quality_evidence,
        )

    if status == "REJECTED":
        _add_finding(
            findings,
            code="VALIDATION_REJECTED",
            category="VALIDATION",
            severity="HIGH",
            message=(
                "The latest dataset version "
                "was rejected by the Validation Gate."
            ),
            evidence={
                "version_id": version_id,
                "validation_status": status,
                "validation_id": record.get(
                    "validation_id"
                ),
                "blocking_issue_count": (
                    record.get(
                        "blocking_issue_count"
                    )
                ),
            },
        )

        _add_action(
            actions,
            code="REMEDIATE_VALIDATION",
            priority=10,
            action=(
                "Inspect blocking validation issues "
                "for the latest dataset version."
            ),
            reason=(
                "A rejected Validation Gate prevents "
                "the version from progressing safely."
            ),
        )

        return

    if status == "ACCEPTED":
        _add_finding(
            findings,
            code="VALIDATION_ACCEPTED",
            category="VALIDATION",
            severity="INFO",
            message=(
                "The latest dataset version "
                "passed the Validation Gate."
            ),
            evidence={
                "version_id": version_id,
                "validation_status": status,
            },
        )

        return

    _add_finding(
        findings,
        code="VALIDATION_EVIDENCE_MISSING",
        category="VALIDATION",
        severity="WARNING",
        message=(
            "No validation evidence was found "
            "for the latest dataset version."
        ),
        evidence={
            "version_id": version_id,
        },
    )

    _add_action(
        actions,
        code="RUN_VALIDATION",
        priority=20,
        action=(
            "Run validation for the latest "
            "dataset version."
        ),
        reason=(
            "The assistant cannot confirm the "
            "version's validation state."
        ),
    )


def _evaluate_governance(
    *,
    governance: dict[str, Any],
    version_id: int | None,
    findings: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> None:
    record = _mapping(
        governance.get("latest_version")
    )

    decision = _status(
        record,
        "decision",
        "governance_decision",
    )

    raw_trust_score = record.get(
        "trust_score"
    )

    if raw_trust_score is not None:
        try:
            trust_score = float(
                raw_trust_score
            )
        except (
            TypeError,
            ValueError,
        ):
            trust_score = None

        if trust_score is not None:
            _add_finding(
                findings,
                code="TRUST_SCORE_RECORDED",
                category="TRUST_SCORE",
                severity="INFO",
                message=(
                    "The latest dataset version "
                    "has persisted Data Trust Score "
                    f"{trust_score:.2f}."
                ),
                evidence={
                    "version_id": version_id,
                    "governance_id": record.get(
                        "governance_id"
                    ),
                    "trust_score": trust_score,
                },
            )

    privacy_status = _status(
        record,
        "privacy_status",
    )

    if privacy_status is not None:
        _add_finding(
            findings,
            code="PRIVACY_STATUS_RECORDED",
            category="PRIVACY",
            severity="INFO",
            message=(
                "The latest dataset version "
                "has persisted privacy status "
                f"{privacy_status}."
            ),
            evidence={
                "version_id": version_id,
                "governance_id": record.get(
                    "governance_id"
                ),
                "privacy_status": (
                    privacy_status
                ),
            },
        )

    if decision == "REJECTED":
        _add_finding(
            findings,
            code="GOVERNANCE_REJECTED",
            category="GOVERNANCE",
            severity="HIGH",
            message=(
                "Governance rejected the latest "
                "dataset version."
            ),
            evidence={
                "version_id": version_id,
                "decision": decision,
                "governance_id": record.get(
                    "governance_id"
                ),
            },
        )

        _add_action(
            actions,
            code="RESOLVE_GOVERNANCE",
            priority=30,
            action=(
                "Review the governance rejection "
                "and its supporting evidence."
            ),
            reason=(
                "A rejected governance decision "
                "prevents trusted promotion."
            ),
        )

        return

    if decision == "REVIEW_REQUIRED":
        _add_finding(
            findings,
            code="GOVERNANCE_REVIEW_REQUIRED",
            category="GOVERNANCE",
            severity="WARNING",
            message=(
                "The latest dataset version "
                "requires governance review."
            ),
            evidence={
                "version_id": version_id,
                "decision": decision,
            },
        )

        _add_action(
            actions,
            code="REVIEW_GOVERNANCE",
            priority=30,
            action=(
                "Review the governance evidence "
                "before promotion."
            ),
            reason=(
                "The current decision requires "
                "human review."
            ),
        )

        return

    if decision == "APPROVED":
        _add_finding(
            findings,
            code="GOVERNANCE_APPROVED",
            category="GOVERNANCE",
            severity="INFO",
            message=(
                "Governance approved the latest "
                "dataset version."
            ),
            evidence={
                "version_id": version_id,
                "decision": decision,
            },
        )

        return

    _add_finding(
        findings,
        code="GOVERNANCE_EVIDENCE_MISSING",
        category="GOVERNANCE",
        severity="WARNING",
        message=(
            "No governance decision was found "
            "for the latest dataset version."
        ),
        evidence={
            "version_id": version_id,
        },
    )

    _add_action(
        actions,
        code="RUN_GOVERNANCE",
        priority=40,
        action=(
            "Evaluate governance for the latest "
            "dataset version."
        ),
        reason=(
            "Promotion eligibility cannot be "
            "confirmed without governance evidence."
        ),
    )


def _evaluate_lifecycle(
    *,
    context: dict[str, Any],
    version_id: int | None,
    findings: list[dict[str, Any]],
) -> None:
    state = _lifecycle_state(
        context,
        version_id,
    )

    if state == "QUARANTINED":
        _add_finding(
            findings,
            code="LIFECYCLE_QUARANTINED",
            category="LIFECYCLE",
            severity="HIGH",
            message=(
                "The latest dataset version "
                "is currently quarantined."
            ),
            evidence={
                "version_id": version_id,
                "lifecycle_state": state,
            },
        )

        return

    if state == "NEW":
        _add_finding(
            findings,
            code="LIFECYCLE_NEW",
            category="LIFECYCLE",
            severity="WARNING",
            message=(
                "The latest dataset version "
                "has not completed the governed "
                "lifecycle yet."
            ),
            evidence={
                "version_id": version_id,
                "lifecycle_state": state,
            },
        )

        return

    if state in {
        "VALIDATED",
        "ACTIVE",
        "SUPERSEDED",
    }:
        _add_finding(
            findings,
            code=f"LIFECYCLE_{state}",
            category="LIFECYCLE",
            severity="INFO",
            message=(
                "The latest dataset version "
                f"is in lifecycle state {state}."
            ),
            evidence={
                "version_id": version_id,
                "lifecycle_state": state,
            },
        )


def _evaluate_freshness(
    *,
    observability: dict[str, Any],
    findings: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> None:
    freshness = _mapping(
        observability.get("freshness")
    )

    record = _mapping(
        freshness.get("latest")
    )

    status = _status(
        record,
        "freshness_status",
        "status",
    )

    if status == "STALE":
        _add_finding(
            findings,
            code="FRESHNESS_STALE",
            category="FRESHNESS",
            severity="WARNING",
            message=(
                "The dataset is currently stale "
                "relative to its freshness policy."
            ),
            evidence={
                "freshness_status": status,
                "age_minutes": record.get(
                    "age_minutes"
                ),
                "max_age_minutes": record.get(
                    "max_age_minutes"
                ),
                "checked_at": record.get(
                    "checked_at"
                ),
            },
        )

        _add_action(
            actions,
            code="INVESTIGATE_FRESHNESS",
            priority=50,
            action=(
                "Investigate why no sufficiently "
                "recent ingestion has arrived."
            ),
            reason=(
                "The latest freshness check "
                "exceeded the configured SLA."
            ),
        )

        return

    if status == "NO_DATA":
        _add_finding(
            findings,
            code="FRESHNESS_NO_DATA",
            category="FRESHNESS",
            severity="WARNING",
            message=(
                "Freshness monitoring cannot find "
                "an ingestion to evaluate."
            ),
            evidence={
                "freshness_status": status,
            },
        )

        _add_action(
            actions,
            code="INVESTIGATE_MISSING_INGESTION",
            priority=50,
            action=(
                "Verify that the dataset has a "
                "valid ingestion history."
            ),
            reason=(
                "Freshness cannot be evaluated "
                "without ingestion data."
            ),
        )

        return

    if status == "FRESH":
        _add_finding(
            findings,
            code="FRESHNESS_FRESH",
            category="FRESHNESS",
            severity="INFO",
            message=(
                "The dataset is within its "
                "configured freshness SLA."
            ),
            evidence={
                "freshness_status": status,
            },
        )


def _evaluate_volume(
    *,
    observability: dict[str, Any],
    findings: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> None:
    volume = _mapping(
        observability.get("volume")
    )

    record = _mapping(
        volume.get("latest")
    )

    status = _status(
        record,
        "volume_status",
        "status",
    )

    if status in {"DROP", "SPIKE"}:
        _add_finding(
            findings,
            code=f"VOLUME_{status}",
            category="VOLUME",
            severity="WARNING",
            message=(
                "The latest ingestion breached "
                f"the configured volume {status.lower()} "
                "threshold."
            ),
            evidence={
                "volume_status": status,
                "baseline_row_count": record.get(
                    "baseline_row_count"
                ),
                "current_row_count": record.get(
                    "current_row_count"
                ),
                "row_change_pct": record.get(
                    "row_change_pct"
                ),
            },
        )

        _add_action(
            actions,
            code="INVESTIGATE_VOLUME",
            priority=60,
            action=(
                "Inspect the latest ingestion and "
                "its upstream row-count change."
            ),
            reason=(
                "The configured dataset volume "
                "threshold was breached."
            ),
        )

        return

    if status == "NORMAL":
        _add_finding(
            findings,
            code="VOLUME_NORMAL",
            category="VOLUME",
            severity="INFO",
            message=(
                "The latest ingestion volume is "
                "within configured thresholds."
            ),
            evidence={
                "volume_status": status,
            },
        )

        return

    if status == "NO_BASELINE":
        _add_finding(
            findings,
            code="VOLUME_NO_BASELINE",
            category="VOLUME",
            severity="INFO",
            message=(
                "Volume monitoring does not yet "
                "have a baseline ingestion."
            ),
            evidence={
                "volume_status": status,
            },
        )


def _evaluate_pipeline(
    *,
    operations: dict[str, Any],
    findings: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> None:
    pipeline_runs = _records(
        operations.get("pipeline_runs")
    )

    if not pipeline_runs:
        return

    latest_run = pipeline_runs[0]

    status = _status(
        latest_run,
        "run_status",
        "status",
    )

    run_id = latest_run.get(
        "pipeline_run_id"
    )

    if status == "FAILED":
        _add_finding(
            findings,
            code="PIPELINE_FAILED",
            category="PIPELINE",
            severity="HIGH",
            message=(
                "The latest recorded pipeline run "
                "failed."
            ),
            evidence={
                "pipeline_run_id": run_id,
                "run_status": status,
            },
        )

        _add_action(
            actions,
            code="INVESTIGATE_PIPELINE_FAILURE",
            priority=20,
            action=(
                "Inspect the latest failed pipeline "
                "run and its failure details."
            ),
            reason=(
                "A failed pipeline can prevent "
                "new trusted data from arriving."
            ),
        )

        return

    if status == "SUCCESS":
        _add_finding(
            findings,
            code="PIPELINE_SUCCESS",
            category="PIPELINE",
            severity="INFO",
            message=(
                "The latest recorded pipeline run "
                "completed successfully."
            ),
            evidence={
                "pipeline_run_id": run_id,
                "run_status": status,
            },
        )

        return

    if status in {
        "RUNNING",
        "QUEUED",
        "PENDING",
    }:
        _add_finding(
            findings,
            code=f"PIPELINE_{status}",
            category="PIPELINE",
            severity="INFO",
            message=(
                "The latest pipeline run "
                f"is currently {status.lower()}."
            ),
            evidence={
                "pipeline_run_id": run_id,
                "run_status": status,
            },
        )


def _overall_state(
    findings: list[dict[str, Any]],
) -> str:
    if not findings:
        return "UNKNOWN"

    highest_rank = max(
        SEVERITY_RANK.get(
            str(
                finding.get(
                    "severity",
                    "INFO",
                )
            ).upper(),
            0,
        )
        for finding in findings
    )

    if highest_rank >= SEVERITY_RANK["HIGH"]:
        return "ACTION_REQUIRED"

    if highest_rank >= SEVERITY_RANK["WARNING"]:
        return "ATTENTION"

    return "HEALTHY"


def reason_about_platform_context(
    context: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(context, dict):
        raise ValueError(
            "context must be a dictionary."
        )

    catalog_id = context.get(
        "catalog_id"
    )

    if (
        not isinstance(catalog_id, int)
        or isinstance(catalog_id, bool)
        or catalog_id <= 0
    ):
        raise ValueError(
            "context.catalog_id must be "
            "a positive integer."
        )

    dataset = _mapping(
        context.get("dataset")
    )

    latest_version_id = dataset.get(
        "latest_version_id"
    )

    if latest_version_id is None:
        return {
            "catalog_id": catalog_id,
            "latest_version_id": None,
            "overall_state": "UNKNOWN",
            "findings": [
                {
                    "code": (
                        "DATASET_VERSION_MISSING"
                    ),
                    "category": "DATASET",
                    "severity": "WARNING",
                    "message": (
                        "No dataset version evidence "
                        "is available for this catalog."
                    ),
                    "evidence": {},
                }
            ],
            "recommended_actions": [
                {
                    "code": (
                        "VERIFY_DATASET_INGESTION"
                    ),
                    "priority": 10,
                    "action": (
                        "Verify that the dataset has "
                        "been ingested and registered."
                    ),
                    "reason": (
                        "Platform reasoning requires "
                        "a dataset version."
                    ),
                }
            ],
            "summary": {
                "finding_count": 1,
                "high_count": 0,
                "warning_count": 1,
                "info_count": 0,
                "action_count": 1,
            },
        }

    try:
        normalized_version_id = int(
            latest_version_id
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "dataset.latest_version_id must "
            "be an integer."
        ) from exc

    findings: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []

    validation = _mapping(
        context.get("validation")
    )

    governance = _mapping(
        context.get("governance")
    )

    observability = _mapping(
        context.get("observability")
    )

    operations = _mapping(
        context.get("operations")
    )

    _evaluate_validation(
        validation=validation,
        version_id=normalized_version_id,
        findings=findings,
        actions=actions,
    )

    _evaluate_governance(
        governance=governance,
        version_id=normalized_version_id,
        findings=findings,
        actions=actions,
    )

    _evaluate_lifecycle(
        context=context,
        version_id=normalized_version_id,
        findings=findings,
    )

    _evaluate_freshness(
        observability=observability,
        findings=findings,
        actions=actions,
    )

    _evaluate_volume(
        observability=observability,
        findings=findings,
        actions=actions,
    )

    _evaluate_pipeline(
        operations=operations,
        findings=findings,
        actions=actions,
    )

    actions.sort(
        key=lambda item: int(
            item["priority"]
        )
    )

    high_count = sum(
        1
        for finding in findings
        if finding["severity"]
        in {"HIGH", "CRITICAL"}
    )

    warning_count = sum(
        1
        for finding in findings
        if finding["severity"] == "WARNING"
    )

    info_count = sum(
        1
        for finding in findings
        if finding["severity"] == "INFO"
    )

    return {
        "catalog_id": catalog_id,
        "latest_version_id": (
            normalized_version_id
        ),
        "overall_state": _overall_state(
            findings
        ),
        "findings": findings,
        "recommended_actions": actions,
        "summary": {
            "finding_count": len(findings),
            "high_count": high_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "action_count": len(actions),
        },
    }