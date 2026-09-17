from __future__ import annotations

import os
from typing import Any

import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

FRESHNESS_URL = (
    f"{API_BASE_URL}/api/freshness"
)


class FreshnessApiError(RuntimeError):
    """Raised when the Dataset Freshness API cannot be used."""


def _payload_dict(
    response: requests.Response,
) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise FreshnessApiError(
            "Dataset Freshness API returned invalid JSON."
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise FreshnessApiError(
            "Dataset Freshness API returned an invalid response."
        )

    return dict(payload)


def load_freshness_policy(
    catalog_id: int,
) -> dict[str, Any] | None:
    try:
        response = requests.get(
            (
                f"{FRESHNESS_URL}/catalog/"
                f"{catalog_id}/policy"
            ),
            timeout=10,
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()

    except requests.RequestException as exc:
        raise FreshnessApiError(
            "Unable to load Freshness Policy."
        ) from exc

    return _payload_dict(
        response
    )


def save_freshness_policy(
    *,
    catalog_id: int,
    max_age_minutes: int,
    is_enabled: bool,
) -> dict[str, Any]:
    try:
        response = requests.put(
            (
                f"{FRESHNESS_URL}/catalog/"
                f"{catalog_id}/policy"
            ),
            json={
                "max_age_minutes": max_age_minutes,
                "is_enabled": is_enabled,
            },
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise FreshnessApiError(
            "Unable to save Freshness Policy."
        ) from exc

    return _payload_dict(
        response
    )


def load_freshness_history(
    catalog_id: int,
    *,
    limit: int = 100,
) -> dict[str, Any]:
    try:
        response = requests.get(
            (
                f"{FRESHNESS_URL}/catalog/"
                f"{catalog_id}/history"
            ),
            params={
                "limit": limit,
            },
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise FreshnessApiError(
            "Unable to load Freshness History."
        ) from exc

    return _payload_dict(
        response
    )


def run_freshness_check(
    catalog_id: int,
) -> dict[str, Any]:
    try:
        response = requests.post(
            (
                f"{FRESHNESS_URL}/catalog/"
                f"{catalog_id}/check"
            ),
            timeout=15,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise FreshnessApiError(
            "Unable to run Freshness Check."
        ) from exc

    return _payload_dict(
        response
    )