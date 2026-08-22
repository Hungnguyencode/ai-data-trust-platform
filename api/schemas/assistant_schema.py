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