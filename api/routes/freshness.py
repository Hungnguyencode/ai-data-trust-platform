from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
)

from api.schemas.freshness_schema import (
    FreshnessCheckRunResponse,
    FreshnessHistoryResponse,
    FreshnessPolicyResponse,
    FreshnessPolicyUpdateRequest,
)
from database.repositories.freshness_repository import (
    get_freshness_history as load_freshness_history,
)
from database.repositories.freshness_repository import (
    get_freshness_policy as load_freshness_policy,
)
from database.repositories.freshness_repository import (
    upsert_freshness_policy,
)
from src.observability.freshness_monitor import (
    check_dataset_freshness,
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
    response_model=FreshnessPolicyResponse,
)
def get_catalog_freshness_policy(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        policy = load_freshness_policy(
            catalog_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "freshness policy."
            ),
        ) from exc

    if policy is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No freshness policy for "
                f"catalog_id={catalog_id}."
            ),
        )

    return FreshnessPolicyResponse(
        **policy
    )


@router.put(
    "/catalog/{catalog_id}/policy",
    response_model=FreshnessPolicyResponse,
)
def update_catalog_freshness_policy(
    payload: FreshnessPolicyUpdateRequest,
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        policy = upsert_freshness_policy(
            catalog_id=catalog_id,
            max_age_minutes=(
                payload.max_age_minutes
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
                "freshness policy."
            ),
        ) from exc

    return FreshnessPolicyResponse(
        **policy
    )


@router.get(
    "/catalog/{catalog_id}/history",
    response_model=FreshnessHistoryResponse,
)
def get_catalog_freshness_history(
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
        history = load_freshness_history(
            catalog_id,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "freshness history."
            ),
        ) from exc

    records = _frame_records(
        history
    )

    return FreshnessHistoryResponse(
        catalog_id=catalog_id,
        limit=limit,
        count=len(records),
        items=records,
    )


@router.post(
    "/catalog/{catalog_id}/check",
    response_model=FreshnessCheckRunResponse,
)
def run_catalog_freshness_check(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        result = check_dataset_freshness(
            catalog_id
        )
    except ValueError as exc:
        message = str(exc)

        status_code = (
            404
            if message.startswith(
                "No freshness policy"
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
                "freshness check."
            ),
        ) from exc

    return FreshnessCheckRunResponse(
        **result
    )