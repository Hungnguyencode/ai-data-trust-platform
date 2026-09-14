from __future__ import annotations

from pydantic import BaseModel


class DatasetWorkflowResponse(BaseModel):
    ingestion_id: str

    catalog_id: int
    version_id: int
    version_number: int

    validation_id: int
    validation_status: str

    governance_id: int
    governance_decision: str

    trust_score: float
    privacy_status: str

    lifecycle_state: str
    promotion_eligible: bool

    contract_id: int | None = None
    contract_version: int | None = None
    contract_enforcement_mode: str | None = None
    contract_validation_id: int | None = None
    contract_validation_status: str | None = None

    lineage_url: str