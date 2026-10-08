from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PrivacyScanRequest(BaseModel):
    records: list[dict[str, Any]]


class PrivacyScanResponse(BaseModel):
    summary: dict[str, Any]
    findings_records: list[dict[str, Any]]