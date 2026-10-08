from __future__ import annotations

import os
from typing import Any

import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

PIPELINE_RUNS_URL = (
    f"{API_BASE_URL}/api/pipeline-runs"
)

OPERATIONAL_EVENTS_URL = (
    f"{API_BASE_URL}/api/operational-events"
)

class PipelineOperationsApiError(RuntimeError):
    """Raised when the Pipeline Operations API cannot be used."""


def load_pipeline_runs(
    limit: int = 100,
) -> list[dict[str, Any]]:
    try:
        response = requests.get(
            PIPELINE_RUNS_URL,
            params={
                "limit": limit,
            },
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise PipelineOperationsApiError(
            "Unable to load Pipeline Runs."
        ) from exc

    payload = response.json()

    return list(
        payload.get(
            "items",
            [],
        )
    )


def load_pipeline_run(
    pipeline_run_id: int,
) -> dict[str, Any]:
    try:
        response = requests.get(
            (
                f"{PIPELINE_RUNS_URL}/"
                f"{pipeline_run_id}"
            ),
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise PipelineOperationsApiError(
            "Unable to load Pipeline Run."
        ) from exc

    return dict(
        response.json()
    )


def load_operational_events(
    limit: int = 200,
) -> list[dict[str, Any]]:
    try:
        response = requests.get(
            OPERATIONAL_EVENTS_URL,
            params={
                "limit": limit,
            },
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise PipelineOperationsApiError(
            "Unable to load Operational Events."
        ) from exc

    payload = response.json()

    return list(
        payload.get(
            "items",
            [],
        )
    )