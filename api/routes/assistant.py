import time

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
)

from api.schemas.assistant_schema import (
    AssistantAskRequest,
    AssistantAskResponse,
    AssistantCopilotRequest,
    AssistantCopilotResponse,
    AssistantPlatformContextResponse,
    AssistantPlatformDiagnosisResponse,
    AssistantPlatformEnhancedExplanationResponse,
    AssistantPlatformExplanationResponse,
)
from src.assistant.controlled_tools import (
    build_controlled_evidence_answerability,
    build_controlled_evidence_coverage,
    build_controlled_evidence_sufficiency,
    execute_bounded_controlled_tool_rounds,
    execute_controlled_tool,
    plan_controlled_evidence_requirements,
    plan_controlled_tool_requests,
    select_controlled_tool_request,
)
from src.assistant.llm_provider import (
    LLMConfigurationError,
)
from src.assistant.platform_context import (
    build_platform_context,
)
from src.assistant.platform_copilot import (
    answer_copilot_question,
)
from src.assistant.platform_explanation import (
    explain_platform_diagnosis,
)
from src.assistant.platform_llm import (
    enhance_platform_explanation,
)
from src.assistant.platform_reasoning import (
    reason_about_platform_context,
)

try:
    from src.assistant.ai_explainer import answer_question
except Exception:
    answer_question = None

router = APIRouter()


@router.post("/ask", response_model=AssistantAskResponse)
def ask_assistant(payload: AssistantAskRequest):
    if answer_question is None:
        return AssistantAskResponse(
            answer=(
                "Assistant backend is running, but src.assistant.ai_explainer "
                "could not be imported. Please check your project path."
            ),
            grounded=True,
            version="2.6",
        )

    answer = answer_question(
        question=payload.question,
        context=payload.context,
    )

    return AssistantAskResponse(
        answer=answer,
        grounded=True,
        version="2.6",
    )


@router.get(
    "/catalog/{catalog_id}/context",
    response_model=AssistantPlatformContextResponse,
)
def get_catalog_assistant_context(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        context = build_platform_context(
            catalog_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to build assistant "
                "platform context."
            ),
        ) from exc

    evidence_summary = context.get(
        "evidence_summary",
        {},
    )

    if not isinstance(
        evidence_summary,
        dict,
    ):
        evidence_summary = {}

    return AssistantPlatformContextResponse(
        catalog_id=catalog_id,
        grounded=True,
        version="2.6",
        evidence_summary=evidence_summary,
        context=context,
    )


@router.get(
    "/catalog/{catalog_id}/diagnosis",
    response_model=(
        AssistantPlatformDiagnosisResponse
    ),
)
def get_catalog_assistant_diagnosis(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        context = build_platform_context(
            catalog_id
        )

        diagnosis = (
            reason_about_platform_context(
                context
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to build assistant "
                "platform diagnosis."
            ),
        ) from exc

    return AssistantPlatformDiagnosisResponse(
        **diagnosis,
        grounded=True,
        version="2.6",
    )


@router.get(
    "/catalog/{catalog_id}/explanation",
    response_model=(
        AssistantPlatformExplanationResponse
    ),
)
def get_catalog_assistant_explanation(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        context = build_platform_context(
            catalog_id
        )

        diagnosis = (
            reason_about_platform_context(
                context
            )
        )

        explanation = (
            explain_platform_diagnosis(
                diagnosis
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to build assistant "
                "platform explanation."
            ),
        ) from exc

    return AssistantPlatformExplanationResponse(
        **explanation,
        grounded=True,
        version="2.6",
    )


@router.get(
    "/catalog/{catalog_id}/enhanced-explanation",
    response_model=(
        AssistantPlatformEnhancedExplanationResponse
    ),
)
def get_catalog_assistant_enhanced_explanation(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        context = build_platform_context(
            catalog_id
        )

        diagnosis = (
            reason_about_platform_context(
                context
            )
        )

        explanation = (
            explain_platform_diagnosis(
                diagnosis
            )
        )

        enhanced = (
            enhance_platform_explanation(
                explanation
            )
        )

    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Assistant LLM configuration "
                "is invalid."
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to build assistant "
                "enhanced platform explanation."
            ),
        ) from exc

    return (
        AssistantPlatformEnhancedExplanationResponse(
            **enhanced,
            grounded=True,
            version="2.6",
        )
    )


@router.post(
    "/catalog/{catalog_id}/copilot",
    response_model=AssistantCopilotResponse,
)
def ask_catalog_copilot(
    payload: AssistantCopilotRequest,
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        context = build_platform_context(
            catalog_id
        )

        diagnosis = (
            reason_about_platform_context(
                context
            )
        )

        explanation = (
            explain_platform_diagnosis(
                diagnosis
            )
        )

        history = [
            message.model_dump()
            for message in payload.history
        ]

        controlled_tool_results = []
        tool_execution_trace = []
        agent_run_summary = None
        agent_evidence_coverage = None
        agent_evidence_sufficiency = None
        agent_evidence_answerability = None

        latest_version_id = diagnosis.get(
            "latest_version_id"
        )

        if (
            isinstance(
                latest_version_id,
                int,
            )
            and not isinstance(
                latest_version_id,
                bool,
            )
            and latest_version_id > 0
        ):
            tool_requests = (
                plan_controlled_tool_requests(
                    payload.question,
                    trusted_version_id=(
                        latest_version_id
                    ),
                    trusted_catalog_id=(
                        catalog_id
                    ),
                )
            )

            if len(tool_requests) <= 1:
                tool_request = (
                    select_controlled_tool_request(
                        payload.question,
                        trusted_version_id=(
                            latest_version_id
                        ),
                        trusted_catalog_id=(
                            catalog_id
                        ),
                    )
                )

                tool_requests = (
                    [tool_request]
                    if tool_request is not None
                    else []
                )

            if len(tool_requests) > 1:
                agent_run_summary = {}
                agent_evidence_coverage = {}
                agent_evidence_sufficiency = {}
                agent_evidence_answerability = {}

                controlled_tool_results.extend(
                    execute_bounded_controlled_tool_rounds(
                        payload.question,
                        trusted_version_id=(
                            latest_version_id
                        ),
                        trusted_catalog_id=(
                            catalog_id
                        ),
                        execution_trace=(
                            tool_execution_trace
                        ),
                        initial_tool_requests=(
                            tool_requests
                        ),
                        agent_run_summary=(
                            agent_run_summary
                        ),
                        agent_evidence_coverage=(
                            agent_evidence_coverage
                        ),
                        agent_evidence_sufficiency=(
                            agent_evidence_sufficiency
                        ),
                        agent_evidence_answerability=(
                            agent_evidence_answerability
                        ),
                    )
                )

            else:
                for step, tool_request in enumerate(
                    tool_requests,
                    start=1,
                ):
                    started_at = time.perf_counter()

                    tool_result = None
                    error_type = None

                    try:
                        tool_result = (
                            execute_controlled_tool(
                                tool_request["name"],
                                tool_request[
                                    "arguments"
                                ],
                            )
                        )

                    except Exception as exc:
                        error_type = type(
                            exc
                        ).__name__

                        tool_result = None

                    duration_ms = round(
                        (
                            time.perf_counter()
                            - started_at
                        )
                        * 1000,
                        3,
                    )

                    evidence_accepted = (
                        tool_result is not None
                    )

                    tool_execution_trace.append(
                        {
                            "step": step,
                            "tool_name": (
                                tool_request[
                                    "name"
                                ]
                            ),
                            "arguments": (
                                tool_request[
                                    "arguments"
                                ]
                            ),
                            "status": (
                                "SUCCEEDED"
                                if evidence_accepted
                                else "FAILED"
                            ),
                            "duration_ms": (
                                duration_ms
                            ),
                            "evidence_accepted": (
                                evidence_accepted
                            ),
                            "error_type": (
                                error_type
                            ),
                        }
                    )

                    if tool_result is not None:
                        controlled_tool_results.append(
                            tool_result
                        )

                attempted_tool_count = len(
                    tool_requests
                )

                accepted_evidence_count = len(
                    controlled_tool_results
                )

                agent_run_summary = {
                    "round_count": (
                        1
                        if attempted_tool_count > 0
                        else 0
                    ),
                    "stop_reason": (
                        "NO_UNATTEMPTED_REQUESTED_TOOLS"
                        if attempted_tool_count > 0
                        else "NO_TOOL_REQUESTS"
                    ),
                    "attempted_tool_count": (
                        attempted_tool_count
                    ),
                    "accepted_evidence_count": (
                        accepted_evidence_count
                    ),
                    "failed_tool_count": (
                        attempted_tool_count
                        - accepted_evidence_count
                    ),
                }

                requested_evidence = (
                    plan_controlled_evidence_requirements(
                        payload.question,
                        trusted_version_id=(
                            latest_version_id
                        ),
                        trusted_catalog_id=(
                            catalog_id
                        ),
                    )
                )

                agent_evidence_coverage = (
                    build_controlled_evidence_coverage(
                        requested_evidence=(
                            requested_evidence
                        ),
                        attempted_tool_names=[
                            str(
                                request["name"]
                            )
                            for request
                            in tool_requests
                        ],
                        accepted_tool_names=[
                            str(
                                result["name"]
                            )
                            for result
                            in controlled_tool_results
                        ],
                    )
                )

                agent_evidence_sufficiency = (
                    build_controlled_evidence_sufficiency(
                        requested_evidence=(
                            requested_evidence
                        ),
                        controlled_tool_results=(
                            controlled_tool_results
                        ),
                    )
                )

                agent_evidence_answerability = (
                    build_controlled_evidence_answerability(
                        question=payload.question,
                        evidence_sufficiency=(
                            agent_evidence_sufficiency
                        ),
                    )
                )

        if controlled_tool_results:
            copilot = answer_copilot_question(
                payload.question,
                diagnosis,
                explanation,
                history=history,
                controlled_tool_results=(
                    controlled_tool_results
                ),
                agent_evidence_answerability=(
                    agent_evidence_answerability
                ),
            )

        else:
            copilot = answer_copilot_question(
                payload.question,
                diagnosis,
                explanation,
                history=history,
                agent_evidence_answerability=(
                    agent_evidence_answerability
                ),
            )

    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Assistant LLM configuration "
                "is invalid."
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to answer assistant "
                "copilot question."
            ),
        ) from exc

    return AssistantCopilotResponse(
        **copilot,
        grounded=True,
        version="2.6",
        tool_execution_trace=(
            tool_execution_trace
        ),
        agent_run_summary=(
            agent_run_summary
        ),
        agent_evidence_coverage=(
            agent_evidence_coverage
        ),
        agent_evidence_sufficiency=(
            agent_evidence_sufficiency
        ),
        agent_evidence_answerability=(
            agent_evidence_answerability
        ),
    )


@router.get("/status")
def assistant_status():
    return {
        "status": "ok",
        "assistant_type": "rule-grounded",
        "version": "2.6",
        "principle": "Only answer from provided scan context.",
    }