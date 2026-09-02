from __future__ import annotations

from pydantic import BaseModel


class DatasetPromotionResponse(BaseModel):
    version_id: int
    catalog_id: int
    previous_state: str
    lifecycle_state: str
    changed: bool
    governance_decision: str | None = None
    message: str