from __future__ import annotations

from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas.workflow_schema import (
    ContinueDatasetWorkflowRequest,
    DatasetIngestionResponse,
    DatasetWorkflowResponse,
)
from src.ingestion.contracts import (
    IngestionMetadata,
    IngestionResult,
)
from src.ingestion.ingestion_service import ingest_dataset
from src.ingestion.raw_storage import sanitize_file_name
from src.workflows import (
    DatasetWorkflowError,
    continue_dataset_workflow,
    run_dataset_workflow,
)


def _dataframe_records(
    dataframe: pd.DataFrame,
) -> list[dict]:
    normalized = (
        dataframe.astype(object)
        .where(pd.notna(dataframe), None)
    )

    return normalized.to_dict(
        orient="records"
    )


def _serialize_profile(
    profile: dict,
) -> dict:
    serialized = dict(profile)

    for key in (
        "schema_summary",
        "missing_summary",
        "numeric_summary",
        "categorical_summary",
    ):
        value = serialized.get(key)

        if isinstance(value, pd.DataFrame):
            serialized[key] = (
                _dataframe_records(value)
            )

    return serialized


router = APIRouter()


def _build_upload_source(
    uploaded_file: UploadFile,
) -> BytesIO:
    """
    Convert FastAPI UploadFile into the generic binary source
    already supported by the ingestion layer.

    The API remains only a transport adapter.
    Dataset parsing and validation stay inside the core workflow.
    """

    try:
        file_name = sanitize_file_name(
            uploaded_file.filename or ""
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    uploaded_file.file.seek(0)
    content = uploaded_file.file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must not be empty.",
        )

    source = BytesIO(content)

    # read_source_bytes() already understands file-like
    # objects exposing the .name attribute.
    source.name = file_name

    return source


@router.post(
    "/ingest",
    response_model=DatasetIngestionResponse,
)
def ingest_dataset_upload(
    file: UploadFile = File(...),
):
    source = _build_upload_source(
        file
    )

    result = ingest_dataset(
        source,
        persist_raw=True,
    )

    return DatasetIngestionResponse(
        records=_dataframe_records(
            result.dataframe
        ),
        ingestion_metadata=(
            result.metadata.to_dict()
        ),
    )


@router.post(
    "/run",
    response_model=DatasetWorkflowResponse,
)
def run_governed_dataset_workflow(
    file: UploadFile = File(...),
):
    """
    Run the governed dataset workflow from a file upload.

    Pipeline:

        Upload
        -> Raw/Bronze ingestion
        -> Profiling
        -> Catalog/version registration
        -> Data Contract Gate
        -> Validation Gate
        -> Governance
        -> Lifecycle sync

    ACTIVE promotion is deliberately excluded.
    """

    source = _build_upload_source(
        file
    )

    try:
        result = run_dataset_workflow(
            source,
            persist_raw=True,
        )

    except DatasetWorkflowError as exc:
        if exc.stage in {
            "INGESTION",
            "INGESTION_RESULT",
        }:
            raise HTTPException(
                status_code=400,
                detail={
                    "stage": exc.stage,
                    "message": str(exc.cause),
                },
            ) from exc

        raise HTTPException(
            status_code=500,
            detail={
                "stage": exc.stage,
                "message": (
                    "Dataset workflow could not be completed."
                ),
            },
        ) from exc

    return _build_workflow_response(
        result
    )


@router.post(
    "/continue",
    response_model=DatasetWorkflowResponse,
)
def continue_governed_dataset_workflow(
    request: ContinueDatasetWorkflowRequest,
):
    ingestion_result = IngestionResult(
        dataframe=pd.DataFrame(
            request.records
        ),
        metadata=IngestionMetadata(
            **request.ingestion_metadata.model_dump()
        ),
    )

    try:
        result = continue_dataset_workflow(
            ingestion_result
        )

    except DatasetWorkflowError as exc:
        if exc.stage == "INGESTION_RESULT":
            raise HTTPException(
                status_code=400,
                detail={
                    "stage": exc.stage,
                    "message": str(exc.cause),
                },
            ) from exc

        raise HTTPException(
            status_code=500,
            detail={
                "stage": exc.stage,
                "message": (
                    "Dataset workflow could not "
                    "be completed."
                ),
            },
        ) from exc

    return _build_workflow_response(
        result
    )


def _build_workflow_response(
    result,
) -> DatasetWorkflowResponse:
    summary = result.summary()

    version_id = int(
        summary["version_id"]
    )

    return DatasetWorkflowResponse(
        ingestion_id=str(
            summary["ingestion_id"]
        ),
        catalog_id=int(
            summary["catalog_id"]
        ),
        version_id=version_id,
        version_number=int(
            summary["version_number"]
        ),
        validation_id=int(
            summary["validation_id"]
        ),
        validation_status=str(
            summary["validation_status"]
        ),
        governance_id=int(
            summary["governance_id"]
        ),
        governance_decision=str(
            summary["governance_decision"]
        ),
        trust_score=float(
            summary["trust_score"]
        ),
        privacy_status=str(
            summary["privacy_status"]
        ),
        lifecycle_state=str(
            summary["lifecycle_state"]
        ),
        promotion_eligible=bool(
            summary["promotion_eligible"]
        ),
        contract_id=(
            int(summary["contract_id"])
            if summary.get("contract_id")
            is not None
            else None
        ),
        contract_version=(
            int(summary["contract_version"])
            if summary.get("contract_version")
            is not None
            else None
        ),
        contract_enforcement_mode=(
            str(
                summary[
                    "contract_enforcement_mode"
                ]
            )
            if summary.get(
                "contract_enforcement_mode"
            )
            is not None
            else None
        ),
        contract_validation_id=(
            int(
                summary[
                    "contract_validation_id"
                ]
            )
            if summary.get(
                "contract_validation_id"
            )
            is not None
            else None
        ),
        contract_validation_status=(
            str(
                summary[
                    "contract_validation_status"
                ]
            )
            if summary.get(
                "contract_validation_status"
            )
            is not None
            else None
        ),
        records=_dataframe_records(
            result.dataframe
        ),
        profile=_serialize_profile(
            result.profile
        ),
        ingestion_metadata=result.ingestion_metadata,
        catalog_registration=result.catalog_registration,
        validation_result=result.validation_result,
        validation_registration=result.validation_registration,
        governance_result=result.governance_result,
        governance_registration=result.governance_registration,
        lifecycle_result=result.lifecycle_result,
        quality_report=result.quality_report,
        trust_score_report=result.trust_score_report,
        privacy_report=result.privacy_report,
        data_contract=result.data_contract,
        contract_validation=result.contract_validation,
        lineage_url=(
            f"/api/datasets/{version_id}/lineage"
        ),
    )