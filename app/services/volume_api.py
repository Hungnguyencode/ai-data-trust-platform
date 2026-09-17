from __future__ import annotations

import os
from typing import Any

import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

VOLUME_URL = (
    f"{API_BASE_URL}/api/volume"
)


class VolumeApiError(RuntimeError):
    """Raised when the Dataset Volume API cannot be used."""


def _payload_dict(
    response: requests.Response,
) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise VolumeApiError(
            "Dataset Volume API returned invalid JSON."
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise VolumeApiError(
            "Dataset Volume API returned an invalid response."
        )

    return dict(payload)


def load_volume_policy(
    catalog_id: int,
) -> dict[str, Any] | None:
    try:
        response = requests.get(
            (
                f"{VOLUME_URL}/catalog/"
                f"{catalog_id}/policy"
            ),
            timeout=10,
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()

    except requests.RequestException as exc:
        raise VolumeApiError(
            "Unable to load Volume Policy."
        ) from exc

    return _payload_dict(
        response
    )


def save_volume_policy(
    *,
    catalog_id: int,
    drop_threshold_pct: float,
    spike_threshold_pct: float,
    is_enabled: bool,
) -> dict[str, Any]:
    try:
        response = requests.put(
            (
                f"{VOLUME_URL}/catalog/"
                f"{catalog_id}/policy"
            ),
            json={
                "drop_threshold_pct": (
                    drop_threshold_pct
                ),
                "spike_threshold_pct": (
                    spike_threshold_pct
                ),
                "is_enabled": is_enabled,
            },
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise VolumeApiError(
            "Unable to save Volume Policy."
        ) from exc

    return _payload_dict(
        response
    )


def load_volume_history(
    catalog_id: int,
    *,
    limit: int = 100,
) -> dict[str, Any]:
    try:
        response = requests.get(
            (
                f"{VOLUME_URL}/catalog/"
                f"{catalog_id}/history"
            ),
            params={
                "limit": limit,
            },
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise VolumeApiError(
            "Unable to load Volume History."
        ) from exc

    return _payload_dict(
        response
    )


def run_volume_check(
    catalog_id: int,
) -> dict[str, Any]:
    try:
        response = requests.post(
            (
                f"{VOLUME_URL}/catalog/"
                f"{catalog_id}/check"
            ),
            timeout=15,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise VolumeApiError(
            "Unable to run Volume Check."
        ) from exc

    return _payload_dict(
        response
    )