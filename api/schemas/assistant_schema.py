from typing import Any, Dict, Literal

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


class AssistantPlatformExplanationResponse(
    BaseModel
):
    catalog_id: int
    grounded: bool = True
    version: str = "2.6"

    latest_version_id: int | None = None
    overall_state: str

    headline: str
    summary: str
    explanation: str

    source_finding_codes: list[str] = Field(
        default_factory=list
    )

    source_action_codes: list[str] = Field(
        default_factory=list
    )


class AssistantPlatformEnhancedExplanationResponse(
    BaseModel
):
    catalog_id: int
    grounded: bool = True
    version: str = "2.6"

    latest_version_id: int | None = None
    overall_state: str

    headline: str
    summary: str

    explanation: str
    enhanced_explanation: str

    source_finding_codes: list[str] = Field(
        default_factory=list
    )

    source_action_codes: list[str] = Field(
        default_factory=list
    )

    provider: str
    model: str | None = None
    used_llm: bool

    fallback_reason: str | None = None
    error_type: str | None = None


class AssistantCopilotHistoryMessage(BaseModel):
    role: Literal[
        "user",
        "assistant",
    ]

    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


class AssistantCopilotRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    history: list[
        AssistantCopilotHistoryMessage
    ] = Field(
        default_factory=list,
        max_length=10,
    )


class AssistantAgentRunSummaryResponse(
    BaseModel
):
    round_count: int = Field(
        ...,
        ge=0,
    )

    stop_reason: Literal[
        "NO_TOOL_REQUESTS",
        "NO_UNATTEMPTED_REQUESTED_TOOLS",
        "MAX_ROUNDS_REACHED",
    ]

    attempted_tool_count: int = Field(
        ...,
        ge=0,
    )

    accepted_evidence_count: int = Field(
        ...,
        ge=0,
    )

    failed_tool_count: int = Field(
        ...,
        ge=0,
    )


AssistantControlledEvidenceType = Literal[
    "version_lineage",
    "freshness_history",
    "volume_history",
    "pipeline_run_history",
    "operational_event_history",
]


class AssistantAgentEvidenceCoverageResponse(
    BaseModel
):
    requested_evidence: list[
        AssistantControlledEvidenceType
    ] = Field(
        default_factory=list
    )

    attempted_evidence: list[
        AssistantControlledEvidenceType
    ] = Field(
        default_factory=list
    )

    accepted_evidence: list[
        AssistantControlledEvidenceType
    ] = Field(
        default_factory=list
    )

    missing_evidence: list[
        AssistantControlledEvidenceType
    ] = Field(
        default_factory=list
    )

    coverage_status: Literal[
        "COMPLETE",
        "PARTIAL",
        "NONE",
        "NOT_APPLICABLE",
    ]


class AssistantCopilotResponse(BaseModel):
    catalog_id: int
    grounded: bool = True
    version: str = "2.6"

    latest_version_id: int | None = None
    overall_state: str

    answer: str

    source_finding_codes: list[str] = Field(
        default_factory=list
    )

    source_action_codes: list[str] = Field(
        default_factory=list
    )

    provider: str
    model: str | None = None
    used_llm: bool

    fallback_reason: str | None = None
    error_type: str | None = None

    tool_execution_trace: list[
        Dict[str, Any]
    ] = Field(
        default_factory=list
    )

    agent_run_summary: (
        AssistantAgentRunSummaryResponse
        | None
    ) = None

    agent_evidence_coverage: (
        AssistantAgentEvidenceCoverageResponse
        | None
    ) = None
