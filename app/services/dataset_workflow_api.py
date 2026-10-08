from __future__ import annotations

import hashlib
import os

import pandas as pd
import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

DATASET_WORKFLOW_URL = (
    f"{API_BASE_URL}/api/workflows/run"
)

DATASET_WORKFLOW_CONTINUE_URL = (
    f"{API_BASE_URL}/api/workflows/continue"
)

DATASET_WORKFLOW_INGEST_URL = (
    f"{API_BASE_URL}/api/workflows/ingest"
)


def calculate_sha256(
    content: bytes,
) -> str:
    return hashlib.sha256(
        content
    ).hexdigest()


class DatasetWorkflowApiError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        stage: str | None = None,
    ) -> None:
        super().__init__(message)
        self.stage = stage


def run_dataset_workflow(
    uploaded_file,
) -> dict:
    try:
        response = requests.post(
            DATASET_WORKFLOW_URL,
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                ),
            },
            timeout=60,
        )

        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetWorkflowApiError(
            "Unable to run dataset workflow."
        ) from exc

    return _deserialize_workflow_payload(
        response.json()
    )


def _deserialize_workflow_payload(
    payload: dict,
) -> dict:
    result = dict(payload)

    result["dataframe"] = pd.DataFrame(
        payload["records"]
    )

    profile = dict(
        payload["profile"]
    )

    for key in (
        "schema_summary",
        "missing_summary",
        "numeric_summary",
        "categorical_summary",
    ):
        profile[key] = pd.DataFrame(
            profile.get(key, [])
        )

    result["profile"] = profile

    return result


def continue_dataset_workflow(
    *,
    dataframe: pd.DataFrame,
    ingestion_metadata: dict,
) -> dict:
    try:
        response = requests.post(
            DATASET_WORKFLOW_CONTINUE_URL,
            json={
                "records": _dataframe_records(
                    dataframe
                ),
                "ingestion_metadata": ingestion_metadata,
            },
            timeout=60,
        )

        response.raise_for_status()
    except requests.RequestException as exc:
        response = getattr(
            exc,
            "response",
            None,
        )

        if response is not None:
            try:
                detail = response.json().get(
                    "detail",
                    {}
                )
            except ValueError:
                detail = {}

            if isinstance(detail, dict):
                stage = detail.get("stage")
                message = detail.get("message")

                if message:
                    raise DatasetWorkflowApiError(
                        str(message),
                        stage=(
                            str(stage)
                            if stage is not None
                            else None
                        ),
                    ) from exc

        raise DatasetWorkflowApiError(
            "Unable to continue dataset workflow."
        ) from exc

    return _deserialize_workflow_payload(
        response.json()
    )


def ingest_dataset(
    uploaded_file,
) -> dict:
    try:
        response = requests.post(
            DATASET_WORKFLOW_INGEST_URL,
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                ),
            },
            timeout=60,
        )

        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetWorkflowApiError(
            "Unable to ingest dataset."
        ) from exc

    payload = response.json()

    return {
        **payload,
        "dataframe": pd.DataFrame(
            payload["records"]
        ),
    }


def _dataframe_records(
    dataframe: pd.DataFrame,
) -> list[dict]:
    normalized = (
        dataframe.astype(object)
        .where(pd.notna(dataframe), None)
    )

    return normalized.to_dict(
        orient="records"
    )