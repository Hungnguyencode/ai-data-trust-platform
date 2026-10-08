from __future__ import annotations

import os

import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

DATASET_PARSE_URL = (
    f"{API_BASE_URL}/api/datasets/parse"
)


class DatasetParseApiError(RuntimeError):
    pass


def parse_dataset(
    uploaded_file,
) -> dict:
    try:
        response = requests.post(
            DATASET_PARSE_URL,
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                ),
            },
            timeout=15,
        )

        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetParseApiError(
            "Unable to parse dataset."
        ) from exc

    return response.json()