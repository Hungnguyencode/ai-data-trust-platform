from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from src.ingestion.raw_storage import sanitize_file_name
from src.validation.rule_engine import run_quality_checks

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed"
DEFAULT_QUARANTINE_ROOT = PROJECT_ROOT / "data" / "quarantine"

VALIDATION_POLICY_VERSION = "1.0"

BLOCKING_SEVERITIES = {
    "High",
}


@dataclass
class ValidationResult:
    ingestion_id: str
    content_sha256: str
    file_name: str

    status: str
    policy_version: str
    validated_at: str

    total_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int

    blocking_issue_count: int
    blocking_issues: list[dict[str, Any]]

    artifact_path: str
    validation_metadata_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _metadata_to_dict(
    metadata: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    if hasattr(metadata, "to_dict"):
        return dict(metadata.to_dict())

    return dict(metadata)


def _validate_required_metadata(
    metadata: Mapping[str, Any],
) -> None:
    required_fields = {
        "ingestion_id",
        "content_sha256",
        "file_name",
    }

    missing_fields = sorted(
        field
        for field in required_fields
        if metadata.get(field) in {None, ""}
    )

    if missing_fields:
        raise ValueError(
            "Validation metadata thiếu field bắt buộc: "
            + ", ".join(missing_fields)
        )


def get_blocking_issues(
    quality_report: Mapping[str, Any],
) -> list[dict[str, Any]]:
    issues = quality_report.get("issues", [])

    if not isinstance(issues, list):
        return []

    return [
        dict(issue)
        for issue in issues
        if isinstance(issue, dict)
        and str(issue.get("severity")) in BLOCKING_SEVERITIES
    ]


def get_validation_status(
    quality_report: Mapping[str, Any],
) -> str:
    blocking_issues = get_blocking_issues(
        quality_report
    )

    if blocking_issues:
        return "REJECTED"

    return "ACCEPTED"


def _build_artifact_directory(
    *,
    root: Path,
    content_sha256: str,
) -> Path:
    return (
        root
        / content_sha256[:2]
        / content_sha256
    )


def _write_dataset_artifact(
    *,
    df: pd.DataFrame,
    destination_root: Path,
    file_name: str,
    content_sha256: str,
) -> Path:
    safe_name = sanitize_file_name(
        file_name
    )

    file_stem = (
        Path(safe_name).stem
        or "dataset"
    )

    artifact_dir = _build_artifact_directory(
        root=destination_root,
        content_sha256=content_sha256,
    )

    artifact_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact_path = (
        artifact_dir
        / f"{file_stem}.csv"
    )

    df.to_csv(
        artifact_path,
        index=False,
        encoding="utf-8",
    )

    return artifact_path.resolve()


def _write_validation_metadata(
    *,
    destination_root: Path,
    file_name: str,
    content_sha256: str,
    payload: Mapping[str, Any],
) -> Path:
    safe_name = sanitize_file_name(
        file_name
    )

    file_stem = (
        Path(safe_name).stem
        or "dataset"
    )

    artifact_dir = _build_artifact_directory(
        root=destination_root,
        content_sha256=content_sha256,
    )

    artifact_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata_path = (
        artifact_dir
        / f"{file_stem}.validation.json"
    )

    metadata_path.write_text(
        json.dumps(
            dict(payload),
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    return metadata_path.resolve()


def validate_and_route_dataset(
    *,
    df: pd.DataFrame,
    ingestion_metadata: Mapping[str, Any] | Any,
    processed_root: str | Path | None = None,
    quarantine_root: str | Path | None = None,
) -> ValidationResult:
    """
    Validate one ingested dataset and route it to Silver or Quarantine.

    Policy v1:
    - No High issue  -> ACCEPTED -> data/processed
    - Any High issue -> REJECTED -> data/quarantine

    Medium/Low issues are recorded but do not block the dataset.
    """

    if df is None or df.empty:
        raise ValueError(
            "Không thể validation dataset rỗng."
        )

    metadata = _metadata_to_dict(
        ingestion_metadata
    )

    _validate_required_metadata(
        metadata
    )

    ingestion_id = str(
        metadata["ingestion_id"]
    )

    content_sha256 = str(
        metadata["content_sha256"]
    ).lower()

    file_name = str(
        metadata["file_name"]
    )

    if len(content_sha256) != 64:
        raise ValueError(
            "content_sha256 không hợp lệ."
        )

    quality_report = run_quality_checks(
        df
    )

    summary = quality_report[
        "summary"
    ]

    blocking_issues = get_blocking_issues(
        quality_report
    )

    status = get_validation_status(
        quality_report
    )

    validated_at = datetime.now(
        timezone.utc
    ).isoformat()

    processed_path = Path(
        processed_root
        if processed_root is not None
        else DEFAULT_PROCESSED_ROOT
    )

    quarantine_path = Path(
        quarantine_root
        if quarantine_root is not None
        else DEFAULT_QUARANTINE_ROOT
    )

    destination_root = (
        processed_path
        if status == "ACCEPTED"
        else quarantine_path
    )

    artifact_path = _write_dataset_artifact(
        df=df,
        destination_root=destination_root,
        file_name=file_name,
        content_sha256=content_sha256,
    )

    validation_payload = {
        "ingestion_id": ingestion_id,
        "content_sha256": content_sha256,
        "file_name": file_name,
        "status": status,
        "policy_version": (
            VALIDATION_POLICY_VERSION
        ),
        "validated_at": validated_at,
        "summary": {
            "total_issues": int(
                summary["total_issues"]
            ),
            "high_issues": int(
                summary["high_issues"]
            ),
            "medium_issues": int(
                summary["medium_issues"]
            ),
            "low_issues": int(
                summary["low_issues"]
            ),
        },
        "blocking_issue_count": len(
            blocking_issues
        ),
        "blocking_issues": blocking_issues,
        "artifact_path": str(
            artifact_path
        ),
    }

    validation_metadata_path = (
        _write_validation_metadata(
            destination_root=destination_root,
            file_name=file_name,
            content_sha256=content_sha256,
            payload=validation_payload,
        )
    )

    return ValidationResult(
        ingestion_id=ingestion_id,
        content_sha256=content_sha256,
        file_name=file_name,
        status=status,
        policy_version=(
            VALIDATION_POLICY_VERSION
        ),
        validated_at=validated_at,
        total_issues=int(
            summary["total_issues"]
        ),
        high_issues=int(
            summary["high_issues"]
        ),
        medium_issues=int(
            summary["medium_issues"]
        ),
        low_issues=int(
            summary["low_issues"]
        ),
        blocking_issue_count=len(
            blocking_issues
        ),
        blocking_issues=blocking_issues,
        artifact_path=str(
            artifact_path
        ),
        validation_metadata_path=str(
            validation_metadata_path
        ),
    )