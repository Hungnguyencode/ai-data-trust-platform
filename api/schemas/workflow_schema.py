from __future__ import annotations

from typing import Any

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

    records: list[dict[str, Any]]
    profile: dict[str, Any]

    ingestion_metadata: dict[str, Any]
    catalog_registration: dict[str, Any]

    validation_result: dict[str, Any]
    validation_registration: dict[str, Any]

    governance_result: dict[str, Any]
    governance_registration: dict[str, Any]

    lifecycle_result: dict[str, Any]

    quality_report: dict[str, Any]
    trust_score_report: dict[str, Any]
    privacy_report: dict[str, Any]

    data_contract: dict[str, Any] | None = None
    contract_validation: dict[str, Any] | None = None

    contract_id: int | None = None
    contract_version: int | None = None
    contract_enforcement_mode: str | None = None
    contract_validation_id: int | None = None
    contract_validation_status: str | None = None

    lineage_url: str


class IngestionMetadataRequest(BaseModel):
    ingestion_id: str
    source_type: str
    file_name: str
    file_type: str
    extension: str
    content_sha256: str
    byte_size: int
    row_count: int
    column_count: int
    ingested_at: str
    raw_path: str | None = None


class ContinueDatasetWorkflowRequest(BaseModel):
    records: list[dict[str, Any]]
    ingestion_metadata: IngestionMetadataRequest


class DatasetIngestionResponse(BaseModel):
    records: list[dict[str, Any]]
    ingestion_metadata: dict[str, Any]