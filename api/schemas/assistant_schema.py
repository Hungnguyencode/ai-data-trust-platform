from typing import Any, Dict

from pydantic import BaseModel, Field


class AssistantAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)


class AssistantAskResponse(BaseModel):
    answer: str
    grounded: bool
    version: str = "2.6"


class AssistantContextResponse(BaseModel):
    available_results: int
    missing_results: int
    context_summary: Dict[str, Any]


class AssistantPlatformContextResponse(BaseModel):
    catalog_id: int
    grounded: bool = True
    version: str = "2.6"
    evidence_summary: Dict[str, Any] = Field(
        default_factory=dict
    )
    context: Dict[str, Any] = Field(
        default_factory=dict
    )


class AssistantFindingResponse(BaseModel):
    code: str
    category: str
    severity: str
    message: str
    evidence: Dict[str, Any] = Field(
        default_factory=dict
    )


class AssistantRecommendedActionResponse(
    BaseModel
):
    code: str
    priority: int
    action: str
    reason: str


class AssistantReasoningSummaryResponse(
    BaseModel
):
    finding_count: int
    high_count: int
    warning_count: int
    info_count: int
    action_count: int


class AssistantPlatformDiagnosisResponse(
    BaseModel
):
    catalog_id: int
    grounded: bool = True
    version: str = "2.6"

    latest_version_id: int | None = None
    overall_state: str

    findings: list[
        AssistantFindingResponse
    ] = Field(
        default_factory=list
    )

    recommended_actions: list[
        AssistantRecommendedActionResponse
    ] = Field(
        default_factory=list
    )

    summary: (
        AssistantReasoningSummaryResponse
    )