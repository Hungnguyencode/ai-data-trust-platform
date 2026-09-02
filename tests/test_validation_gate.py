from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.validation.validation_gate import (
    get_validation_status,
    validate_and_route_dataset,
)


def build_metadata(
    *,
    file_name: str = "customers.csv",
    sha256: str = "a" * 64,
) -> dict:
    return {
        "ingestion_id": "test-ingestion-001",
        "content_sha256": sha256,
        "file_name": file_name,
    }


def test_clean_dataset_is_accepted(
    tmp_path,
):
    df = pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
                3,
                4,
            ],
            "age": [
                21,
                30,
                42,
                55,
            ],
            "churn": [
                0,
                1,
                0,
                1,
            ],
        }
    )

    result = validate_and_route_dataset(
        df=df,
        ingestion_metadata=build_metadata(),
        processed_root=(
            tmp_path / "processed"
        ),
        quarantine_root=(
            tmp_path / "quarantine"
        ),
    )

    assert result.status == "ACCEPTED"
    assert result.blocking_issue_count == 0

    artifact_path = Path(
        result.artifact_path
    )

    assert artifact_path.exists()

    assert (
        tmp_path / "processed"
    ) in artifact_path.parents

    assert not (
        tmp_path / "quarantine"
    ).exists()


def test_high_issue_is_rejected_to_quarantine(
    tmp_path,
):
    df = pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
                3,
                4,
            ],
            "age": [
                20,
                None,
                None,
                40,
            ],
        }
    )

    result = validate_and_route_dataset(
        df=df,
        ingestion_metadata=build_metadata(
            sha256="b" * 64
        ),
        processed_root=(
            tmp_path / "processed"
        ),
        quarantine_root=(
            tmp_path / "quarantine"
        ),
    )

    assert result.status == "REJECTED"
    assert result.blocking_issue_count >= 1
    assert result.high_issues >= 1

    artifact_path = Path(
        result.artifact_path
    )

    assert artifact_path.exists()

    assert (
        tmp_path / "quarantine"
    ) in artifact_path.parents

    assert not (
        tmp_path / "processed"
    ).exists()


def test_medium_issue_does_not_block_dataset(
    tmp_path,
):
    ages = list(
        range(
            20,
            40,
        )
    )

    ages[0] = None

    df = pd.DataFrame(
        {
            "customer_id": list(
                range(
                    1,
                    21,
                )
            ),
            "age": ages,
        }
    )

    result = validate_and_route_dataset(
        df=df,
        ingestion_metadata=build_metadata(
            sha256="c" * 64
        ),
        processed_root=(
            tmp_path / "processed"
        ),
        quarantine_root=(
            tmp_path / "quarantine"
        ),
    )

    assert result.medium_issues >= 1
    assert result.high_issues == 0
    assert result.status == "ACCEPTED"


def test_rejection_metadata_contains_reason(
    tmp_path,
):
    df = pd.DataFrame(
        {
            "age": [
                None,
                None,
                25,
                30,
            ]
        }
    )

    result = validate_and_route_dataset(
        df=df,
        ingestion_metadata=build_metadata(
            sha256="d" * 64
        ),
        processed_root=(
            tmp_path / "processed"
        ),
        quarantine_root=(
            tmp_path / "quarantine"
        ),
    )

    metadata_path = Path(
        result.validation_metadata_path
    )

    assert metadata_path.exists()

    payload = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["status"] == "REJECTED"

    assert (
        payload["blocking_issue_count"]
        >= 1
    )

    assert payload["blocking_issues"]

    assert (
        payload["blocking_issues"][0][
            "severity"
        ]
        == "High"
    )


def test_same_content_uses_deterministic_location(
    tmp_path,
):
    df = pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
                3,
                4,
            ],
            "age": [
                20,
                30,
                40,
                50,
            ],
        }
    )

    metadata = build_metadata(
        sha256="e" * 64
    )

    first = validate_and_route_dataset(
        df=df,
        ingestion_metadata=metadata,
        processed_root=(
            tmp_path / "processed"
        ),
        quarantine_root=(
            tmp_path / "quarantine"
        ),
    )

    second = validate_and_route_dataset(
        df=df,
        ingestion_metadata=metadata,
        processed_root=(
            tmp_path / "processed"
        ),
        quarantine_root=(
            tmp_path / "quarantine"
        ),
    )

    assert (
        first.artifact_path
        == second.artifact_path
    )

    assert (
        first.validation_metadata_path
        == second.validation_metadata_path
    )


def test_validation_status_helper():
    accepted_report = {
        "issues": [
            {
                "severity": "Medium",
            }
        ]
    }

    rejected_report = {
        "issues": [
            {
                "severity": "High",
            }
        ]
    }

    assert (
        get_validation_status(
            accepted_report
        )
        == "ACCEPTED"
    )

    assert (
        get_validation_status(
            rejected_report
        )
        == "REJECTED"
    )