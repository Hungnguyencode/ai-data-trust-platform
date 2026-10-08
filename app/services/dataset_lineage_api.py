from __future__ import annotations

import os

import pandas as pd
import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://localhost:8000",
)

DATASETS_URL = (
    f"{API_BASE_URL}/api/datasets"
)


class DatasetLineageApiError(RuntimeError):
    pass


def load_dataset_lineage(
    version_id: int,
) -> dict:
    try:
        response = requests.get(
            f"{DATASETS_URL}/{version_id}/lineage",
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetLineageApiError(
            "Unable to load dataset lineage."
        ) from exc

    return response.json()


def load_catalog_lineage(
    catalog_id: int,
) -> pd.DataFrame:
    try:
        response = requests.get(
            (
                f"{DATASETS_URL}"
                f"/catalogs/{catalog_id}/lineage"
            ),
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetLineageApiError(
            "Unable to load catalog lineage."
        ) from exc

    payload = response.json()

    return pd.DataFrame(
        payload["records"]
    )


def load_dataset_version_history(
    catalog_id: int,
) -> pd.DataFrame:
    try:
        response = requests.get(
            (
                f"{DATASETS_URL}"
                f"/catalogs/{catalog_id}/versions"
            ),
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetLineageApiError(
            "Unable to load dataset version history."
        ) from exc

    payload = response.json()

    return pd.DataFrame(
        payload["records"]
    )


def load_ingestion_history(
    catalog_id: int,
    limit: int = 50,
) -> pd.DataFrame:
    try:
        response = requests.get(
            (
                f"{DATASETS_URL}"
                f"/catalogs/{catalog_id}/ingestions"
            ),
            params={
                "limit": limit,
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetLineageApiError(
            "Unable to load ingestion history."
        ) from exc

    payload = response.json()

    return pd.DataFrame(
        payload["records"]
    )


def load_validation_history(
    catalog_id: int,
    limit: int = 50,
) -> pd.DataFrame:
    try:
        response = requests.get(
            (
                f"{DATASETS_URL}"
                f"/catalogs/{catalog_id}/validations"
            ),
            params={
                "limit": limit,
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetLineageApiError(
            "Unable to load validation history."
        ) from exc

    payload = response.json()

    return pd.DataFrame(
        payload["records"]
    )


def load_governance_history(
    catalog_id: int,
    limit: int = 50,
) -> pd.DataFrame:
    try:
        response = requests.get(
            (
                f"{DATASETS_URL}"
                f"/catalogs/{catalog_id}/governance"
            ),
            params={
                "limit": limit,
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetLineageApiError(
            "Unable to load governance history."
        ) from exc

    payload = response.json()

    return pd.DataFrame(
        payload["records"]
    )


def load_catalog_lifecycle(
    catalog_id: int,
) -> pd.DataFrame:
    try:
        response = requests.get(
            (
                f"{DATASETS_URL}"
                f"/catalogs/{catalog_id}/lifecycle"
            ),
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetLineageApiError(
            "Unable to load catalog lifecycle."
        ) from exc

    payload = response.json()

    return pd.DataFrame(
        payload["records"]
    )


def load_lifecycle_history(
    version_id: int,
) -> pd.DataFrame:
    try:
        response = requests.get(
            (
                f"{DATASETS_URL}"
                f"/{version_id}/lifecycle"
            ),
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetLineageApiError(
            "Unable to load lifecycle history."
        ) from exc

    payload = response.json()

    return pd.DataFrame(
        payload["records"]
    )


def promote_dataset_version(
    version_id: int,
) -> dict:
    try:
        response = requests.post(
            (
                f"{DATASETS_URL}"
                f"/{version_id}/promote"
            ),
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DatasetLineageApiError(
            "Unable to promote dataset version."
        ) from exc

    return response.json()