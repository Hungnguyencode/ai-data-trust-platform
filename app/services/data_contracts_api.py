from __future__ import annotations

import os
from typing import Any

import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

DATA_CONTRACTS_URL = (
    f"{API_BASE_URL}/api/data-contracts"
)

class DataContractsApiError(RuntimeError):
    """Raised when the Data Contracts API cannot be used."""


def load_contract_history(
    catalog_id: int,
) -> dict[str, Any]:
    try:
        response = requests.get(
            (
                f"{DATA_CONTRACTS_URL}/"
                f"catalog/{catalog_id}"
            ),
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise DataContractsApiError(
            "Unable to load Data Contract History."
        ) from exc

    return dict(
        response.json()
    )


def load_active_contract(
    catalog_id: int,
) -> dict[str, Any] | None:
    try:
        response = requests.get(
            (
                f"{DATA_CONTRACTS_URL}/"
                f"catalog/{catalog_id}/active"
            ),
            timeout=10,
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()

    except requests.RequestException as exc:
        raise DataContractsApiError(
            "Unable to load Active Data Contract."
        ) from exc

    return dict(
        response.json()
    )


def activate_contract(
    contract_id: int,
) -> dict[str, Any]:
    try:
        response = requests.post(
            (
                f"{DATA_CONTRACTS_URL}/"
                f"{contract_id}/activate"
            ),
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise DataContractsApiError(
            "Unable to activate Data Contract."
        ) from exc

    return dict(
        response.json()
    )


def create_contract(
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        response = requests.post(
            DATA_CONTRACTS_URL,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise DataContractsApiError(
            "Unable to create Data Contract."
        ) from exc

    return dict(
        response.json()
    )