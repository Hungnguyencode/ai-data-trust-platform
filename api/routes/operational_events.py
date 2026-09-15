from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
)

from api.schemas.operational_event_schema import (
    OperationalEventHistoryResponse,
    OperationalEventResponse,
)
from database.repositories.operational_event_repository import (
    get_operational_event as load_operational_event,
)
from database.repositories.operational_event_repository import (
    get_operational_event_history as load_operational_event_history,
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
    "",
    response_model=OperationalEventHistoryResponse,
)
def get_operational_events(
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
):
    try:
        history_frame = (
            load_operational_event_history(
                limit=limit
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "operational event history."
            ),
        ) from exc

    records = _frame_records(
        history_frame
    )

    return OperationalEventHistoryResponse(
        limit=limit,
        count=len(records),
        items=records,
    )


@router.get(
    "/{operational_event_id}",
    response_model=OperationalEventResponse,
)
def get_operational_event_detail(
    operational_event_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        event = load_operational_event(
            operational_event_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "operational event."
            ),
        ) from exc

    if event is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Operational event "
                f"{operational_event_id} "
                "was not found."
            ),
        )

    return OperationalEventResponse(
        **event
    )