from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DatasetLineageResponse(BaseModel):
    summary: dict[str, Any]
    version: dict[str, Any]
    ingestions: list[dict[str, Any]]
    validations: list[dict[str, Any]]
    governance_decisions: list[dict[str, Any]]
    lifecycle_events: list[dict[str, Any]]
    timeline: list[dict[str, Any]]