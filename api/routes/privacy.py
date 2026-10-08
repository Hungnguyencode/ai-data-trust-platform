from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schemas.privacy_schema import (
    PrivacyScanRequest,
    PrivacyScanResponse,
)
from src.privacy.pii_detector import run_privacy_scan

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


@router.post(
    "/scan",
    response_model=PrivacyScanResponse,
)
def scan_privacy(
    payload: PrivacyScanRequest,
) -> PrivacyScanResponse:
    if not payload.records:
        raise HTTPException(
            status_code=400,
            detail="records must not be empty",
        )

    dataframe = pd.DataFrame(
        payload.records
    )

    result = run_privacy_scan(
        dataframe
    )

    return PrivacyScanResponse(
        summary=result["summary"],
        findings_records=_frame_records(
            result["findings_df"]
        ),
    )