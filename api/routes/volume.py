from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
)

from api.schemas.volume_schema import (
    VolumeCheckRunResponse,
    VolumeHistoryResponse,
    VolumePolicyResponse,
    VolumePolicyUpdateRequest,
)
from database.repositories.volume_repository import (
    get_volume_history as load_volume_history,
)
from database.repositories.volume_repository import (
    get_volume_policy as load_volume_policy,
)
from database.repositories.volume_repository import (
    upsert_volume_policy,
)
from src.observability.volume_monitor import (
    check_dataset_volume,
)

router = APIRouter()


def _frame_records(
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    if frame.empty:
        return []

    normalized = (
        frame.astype(object)
        .where(
            pd.notna(frame),
            None,
        )
    )

    return normalized.to_dict(
        orient="records"
    )


@router.get(
    "/catalog/{catalog_id}/policy",
    response_model=VolumePolicyResponse,
)
def get_catalog_volume_policy(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        policy = load_volume_policy(
            catalog_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "volume policy."
            ),
        ) from exc

    if policy is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No volume policy for "
                f"catalog_id={catalog_id}."
            ),
        )

    return VolumePolicyResponse(
        **policy
    )


@router.put(
    "/catalog/{catalog_id}/policy",
    response_model=VolumePolicyResponse,
)
def update_catalog_volume_policy(
    payload: VolumePolicyUpdateRequest,
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        policy = upsert_volume_policy(
            catalog_id=catalog_id,
            drop_threshold_pct=(
                payload.drop_threshold_pct
            ),
            spike_threshold_pct=(
                payload.spike_threshold_pct
            ),
            is_enabled=(
                payload.is_enabled
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save "
                "volume policy."
            ),
        ) from exc

    return VolumePolicyResponse(
        **policy
    )


@router.get(
    "/catalog/{catalog_id}/history",
    response_model=VolumeHistoryResponse,
)
def get_catalog_volume_history(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=1000,
    ),
):
    try:
        history = load_volume_history(
            catalog_id,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "volume history."
            ),
        ) from exc

    records = _frame_records(
        history
    )

    return VolumeHistoryResponse(
        catalog_id=catalog_id,
        limit=limit,
        count=len(records),
        items=records,
    )


@router.post(
    "/catalog/{catalog_id}/check",
    response_model=VolumeCheckRunResponse,
)
def run_catalog_volume_check(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        result = check_dataset_volume(
            catalog_id
        )
    except ValueError as exc:
        message = str(exc)

        status_code = (
            404
            if message.startswith(
                "No volume policy"
            )
            else 409
        )

        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to run "
                "volume check."
            ),
        ) from exc

    return VolumeCheckRunResponse(
        **result
    )