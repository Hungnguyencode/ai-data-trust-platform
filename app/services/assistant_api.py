from __future__ import annotations

import os
from typing import Any

import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

ASSISTANT_URL = (
    f"{API_BASE_URL}/api/assistant"
)


class AssistantApiError(RuntimeError):
    """Raised when the Assistant API cannot be used."""


def _payload_dict(
    response: requests.Response,
) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise AssistantApiError(
            "Assistant API returned invalid JSON."
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise AssistantApiError(
            "Assistant API returned an invalid response."
        )

    return dict(payload)


def ask_catalog_copilot(
    *,
    catalog_id: int,
    question: str,
) -> dict[str, Any]:
    try:
        response = requests.post(
            (
                f"{ASSISTANT_URL}/catalog/"
                f"{catalog_id}/copilot"
            ),
            json={
                "question": question,
            },
            timeout=120,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise AssistantApiError(
            "Unable to answer Copilot question."
        ) from exc

    return _payload_dict(
        response
    )