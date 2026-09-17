from __future__ import annotations

import os
from typing import Any

import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

OBSERVABILITY_URL = (
    f"{API_BASE_URL}/api/observability"
)


class ObservabilityApiError(RuntimeError):
    """Raised when the Observability API cannot be used."""


def load_observability_overview(
    *,
    event_limit: int = 100,
    run_limit: int = 100,
) -> dict[str, Any]:
    try:
        response = requests.get(
            f"{OBSERVABILITY_URL}/overview",
            params={
                "event_limit": event_limit,
                "run_limit": run_limit,
            },
            timeout=15,
        )

        response.raise_for_status()

        payload = response.json()

    except requests.RequestException as exc:
        raise ObservabilityApiError(
            "Unable to load Observability Overview API."
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise ObservabilityApiError(
            "Observability Overview API "
            "returned an invalid response."
        )

    return dict(payload)