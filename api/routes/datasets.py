from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Path

from api.schemas.dataset_schema import (
    DatasetOverviewResponse,
    DatasetPreviewResponse,
    DatasetRecordsRequest,
)
from api.schemas.lineage_schema import DatasetLineageResponse
from api.schemas.promotion_schema import DatasetPromotionResponse
from database.repositories.lineage_repository import get_version_lineage
from database.repositories.version_repository import promote_version

router = APIRouter()


@router.post(
    "/overview",
    response_model=DatasetOverviewResponse,
)
def get_dataset_overview(
    payload: DatasetRecordsRequest,
):
    if not payload.records:
        raise HTTPException(
            status_code=400,
            detail="records must not be empty",
        )

    df = pd.DataFrame(
        payload.records
    )

    return DatasetOverviewResponse(
        file_name=payload.file_name,
        file_type=payload.file_type,
        total_rows=int(
            df.shape[0]
        ),
        total_columns=int(
            df.shape[1]
        ),
        total_cells=int(
            df.shape[0]
            * df.shape[1]
        ),
        missing_cells=int(
            df.isna()
            .sum()
            .sum()
        ),
        duplicate_rows=int(
            df.duplicated()
            .sum()
        ),
        columns=list(
            df.columns
        ),
    )


@router.post(
    "/preview",
    response_model=DatasetPreviewResponse,
)
def get_dataset_preview(
    payload: DatasetRecordsRequest,
):
    if not payload.records:
        raise HTTPException(
            status_code=400,
            detail="records must not be empty",
        )

    df = pd.DataFrame(
        payload.records
    )

    return DatasetPreviewResponse(
        file_name=payload.file_name,
        preview_rows=(
            df.head(10)
            .where(
                pd.notnull(df),
                None,
            )
            .to_dict(
                orient="records"
            )
        ),
        total_rows=int(
            df.shape[0]
        ),
    )


@router.get(
    "/{version_id}/lineage",
    response_model=DatasetLineageResponse,
)
def get_dataset_lineage(
    version_id: int = Path(
        ...,
        gt=0,
    ),
):
    """
    Return end-to-end lineage for one dataset version.

    FastAPI acts only as the transport layer.
    The lineage repository remains the source of truth.
    """

    try:
        return get_version_lineage(
            version_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "dataset lineage."
            ),
        ) from exc


@router.post(
    "/{version_id}/promote",
    response_model=DatasetPromotionResponse,
)
def promote_dataset_version(
    version_id: int = Path(
        ...,
        gt=0,
    ),
):
    """
    Promote one governed dataset version to ACTIVE.

    The API does not implement promotion policy itself.
    Governance and lifecycle enforcement remain inside
    the version repository.
    """

    try:
        before_lineage = get_version_lineage(
            version_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load dataset version "
                "before promotion."
            ),
        ) from exc

    before_summary = before_lineage[
        "summary"
    ]

    catalog_id = int(
        before_summary[
            "catalog_id"
        ]
    )

    previous_state = str(
        before_summary[
            "lifecycle_state"
        ]
    )

    try:
        promotion_result = promote_version(
            catalog_id=catalog_id,
            version_id=version_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to promote "
                "dataset version."
            ),
        ) from exc

    try:
        after_lineage = get_version_lineage(
            version_id
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Dataset was promoted but "
                "the updated lineage could not be loaded."
            ),
        ) from exc

    after_summary = after_lineage[
        "summary"
    ]

    changed = bool(
        promotion_result.get(
            "changed",
            True,
        )
    )

    return DatasetPromotionResponse(
        version_id=version_id,
        catalog_id=catalog_id,
        previous_state=previous_state,
        lifecycle_state=str(
            after_summary[
                "lifecycle_state"
            ]
        ),
        changed=changed,
        governance_decision=(
            after_summary.get(
                "latest_governance_decision"
            )
        ),
        message=(
            "Dataset version promoted "
            "to ACTIVE successfully."
            if changed
            else (
                "Dataset version is already ACTIVE; "
                "no changes were applied."
            )
        ),
    )