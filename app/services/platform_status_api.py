from __future__ import annotations

import os

import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)
READINESS_URL = f"{API_BASE_URL}/ready"


def check_database_connection() -> tuple[bool, str]:
    try:
        response = requests.get(
            READINESS_URL,
            timeout=3,
        )
    except requests.RequestException:
        return (
            False,
            "Kết nối SQL Server không khả dụng.",
        )

    if response.status_code == 200:
        payload = response.json()

        if (
            payload.get("status") == "ready"
            and payload.get(
                "dependencies",
                {},
            ).get("sqlserver")
            == "ok"
        ):
            return (
                True,
                "Kết nối SQL Server thành công.",
            )

    return (
        False,
        "Kết nối SQL Server không khả dụng.",
    )