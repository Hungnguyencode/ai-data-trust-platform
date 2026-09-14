from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas.workflow_schema import DatasetWorkflowResponse
from src.ingestion.raw_storage import sanitize_file_name
from src.workflows import (
    DatasetWorkflowError,
    run_dataset_workflow,
)

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
        lineage_url=(
            f"/api/datasets/{version_id}/lineage"
        ),
    )