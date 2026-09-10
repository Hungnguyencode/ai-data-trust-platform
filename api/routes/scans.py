from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Path, Query

from api.schemas.scan_schema import (
    ScanDetailResponse,
    ScanHistoryResponse,
)
from database.repositories.scan_repository import (
    get_quality_issues_by_scan as load_quality_issues_by_scan,
)
from database.repositories.scan_repository import (
    get_scan_by_id as load_scan_by_id,
)
from database.repositories.scan_repository import (
    get_scan_history as load_scan_history,
)

router = APIRouter()


def _frame_records(
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Convert repository DataFrames into API-safe records.

    Object conversion is intentional so SQL NULL / pandas NaN
    values become Python None before Pydantic serialization.
    """

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


def _build_scan_detail(
    scan_record: dict[str, Any],
    issues_frame: pd.DataFrame,
) -> ScanDetailResponse:
    issue_records = _frame_records(
        issues_frame
    )

    return ScanDetailResponse(
        scan=scan_record,
        quality_issue_count=len(
            issue_records
        ),
        quality_issues=issue_records,
    )


@router.get(
    "/history",
    response_model=ScanHistoryResponse,
)
def get_scan_history(
    limit: int = Query(
        default=50,
        ge=1,
        le=1000,
    ),
):
    """
    Return persisted SQL Server scan history.
    """

    try:
        history_frame = load_scan_history(
            limit=limit
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load scan history."
            ),
        ) from exc

    records = _frame_records(
        history_frame
    )

    return ScanHistoryResponse(
        limit=limit,
        count=len(records),
        items=records,
    )


@router.get(
    "/latest",
    response_model=ScanDetailResponse,
)
def get_latest_scan():
    """
    Return the most recent persisted scan,
    including its quality issues.
    """

    try:
        history_frame = load_scan_history(
            limit=1
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load latest scan."
            ),
        ) from exc

    scan_records = _frame_records(
        history_frame
    )

    if not scan_records:
        raise HTTPException(
            status_code=404,
            detail=(
                "No persisted scans found."
            ),
        )

    scan_record = scan_records[0]
    scan_id = int(
        scan_record["scan_id"]
    )

    try:
        issues_frame = (
            load_quality_issues_by_scan(
                scan_id
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load quality issues "
                "for latest scan."
            ),
        ) from exc

    return _build_scan_detail(
        scan_record,
        issues_frame,
    )


@router.get(
    "/{scan_id}",
    response_model=ScanDetailResponse,
)
def get_scan_detail(
    scan_id: int = Path(
        ...,
        gt=0,
    ),
):
    """
    Return one persisted scan and its quality issues.
    """

    try:
        scan_frame = load_scan_by_id(
            scan_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load scan."
            ),
        ) from exc

    scan_records = _frame_records(
        scan_frame
    )

    if not scan_records:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Scan {scan_id} was not found."
            ),
        )

    try:
        issues_frame = (
            load_quality_issues_by_scan(
                scan_id
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load quality issues "
                "for scan."
            ),
        ) from exc

    return _build_scan_detail(
        scan_records[0],
        issues_frame,
    )