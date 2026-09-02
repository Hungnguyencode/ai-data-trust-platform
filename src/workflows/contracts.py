from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


class DatasetWorkflowError(RuntimeError):
    """
    Raised when one stage of the dataset workflow fails.

    The stage name makes errors easier to diagnose from
    Streamlit, FastAPI, Airflow, CLI, or tests.
    """

    def __init__(
        self,
        *,
        stage: str,
        cause: Exception,
    ) -> None:
        self.stage = str(stage)
        self.cause = cause

        super().__init__(
            f"Dataset workflow failed at stage "
            f"'{self.stage}': {cause}"
        )


@dataclass
class DatasetWorkflowResult:
    """
    Complete successful result of one dataset workflow run.

    This contract is intentionally UI-agnostic.
    Streamlit, FastAPI and future Airflow jobs can consume
    the same result without duplicating business logic.
    """

    dataframe: pd.DataFrame
    profile: dict[str, Any]

    ingestion_metadata: dict[str, Any]
    catalog_registration: dict[str, Any]

    validation_result: dict[str, Any]
    validation_registration: dict[str, Any]

    governance_result: dict[str, Any]
    governance_registration: dict[str, Any]

    lifecycle_result: dict[str, Any]

    quality_report: dict[str, Any]
    trust_score_report: dict[str, Any]
    privacy_report: dict[str, Any]

    def summary(self) -> dict[str, Any]:
        return {
            "ingestion_id": self.ingestion_metadata.get(
                "ingestion_id"
            ),
            "catalog_id": self.catalog_registration.get(
                "catalog_id"
            ),
            "version_id": self.catalog_registration.get(
                "version_id"
            ),
            "version_number": self.catalog_registration.get(
                "version_number"
            ),
            "validation_id": self.validation_registration.get(
                "validation_id"
            ),
            "validation_status": self.validation_result.get(
                "status"
            ),
            "governance_id": self.governance_registration.get(
                "governance_id"
            ),
            "governance_decision": self.governance_result.get(
                "decision"
            ),
            "trust_score": self.governance_result.get(
                "trust_score"
            ),
            "privacy_status": self.governance_result.get(
                "privacy_status"
            ),
            "lifecycle_state": self.lifecycle_result.get(
                "lifecycle_state"
            ),
            "promotion_eligible": self.governance_result.get(
                "promotion_eligible"
            ),
        }