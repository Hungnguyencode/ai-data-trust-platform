from __future__ import annotations

from pathlib import Path as FilePath

import pandas as pd
from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Path,
    Query,
    UploadFile,
)

from api.schemas.dataset_schema import (
    DatasetCatalogLifecycleResponse,
    DatasetGovernanceHistoryResponse,
    DatasetIngestionHistoryResponse,
    DatasetLifecycleHistoryResponse,
    DatasetOverviewResponse,
    DatasetParseResponse,
    DatasetPreviewResponse,
    DatasetRecordsRequest,
    DatasetValidationHistoryResponse,
    DatasetVersionHistoryResponse,
)
from api.schemas.lineage_schema import (
    CatalogLineageResponse,
    DatasetLineageResponse,
)
from api.schemas.promotion_schema import DatasetPromotionResponse
from database.repositories.catalog_repository import (
    get_dataset_version_history,
    get_ingestion_history,
)
from database.repositories.governance_repository import (
    get_governance_history,
)
from database.repositories.lineage_repository import (
    get_catalog_lineage,
    get_version_lineage,
)
from database.repositories.validation_repository import (
    get_validation_history,
)
from database.repositories.version_repository import (
    get_catalog_lifecycle,
    get_lifecycle_history,
    promote_version,
)
from src.ingestion.file_loader import (
    load_dataset_from_bytes,
)
from src.validation.rule_engine import run_quality_checks

router = APIRouter()


@router.post(
    "/parse",
    response_model=DatasetParseResponse,
)
def parse_dataset(
    file: UploadFile = File(...),
) -> DatasetParseResponse:
    file_name = FilePath(
        file.filename or ""
    ).name

    try:
        content = file.file.read()

        df, file_type = (
            load_dataset_from_bytes(
                content=content,
                file_name=file_name,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    records = (
        df.where(
            pd.notnull(df),
            None,
        )
        .to_dict(
            orient="records"
        )
    )

    return DatasetParseResponse(
        file_name=file_name,
        file_type=file_type,
        total_rows=int(df.shape[0]),
        total_columns=int(df.shape[1]),
        records=records,
    )


@router.post(
    "/overview",
    response_model=DatasetOverviewResponse,
)
def get_dataset_overview(
    payload: DatasetRecordsRequest,
):
    if not payload.records:
        raise HTTPException(
            status_code=400,
            detail="records must not be empty",
        )

    df = pd.DataFrame(
        payload.records
    )

    return DatasetOverviewResponse(
        file_name=payload.file_name,
        file_type=payload.file_type,
        total_rows=int(
            df.shape[0]
        ),
        total_columns=int(
            df.shape[1]
        ),
        total_cells=int(
            df.shape[0]
            * df.shape[1]
        ),
        missing_cells=int(
            df.isna()
            .sum()
            .sum()
        ),
        duplicate_rows=int(
            df.duplicated()
            .sum()
        ),
        columns=list(
            df.columns
        ),
    )


@router.post(
    "/preview",
    response_model=DatasetPreviewResponse,
)
def get_dataset_preview(
    payload: DatasetRecordsRequest,
):
    if not payload.records:
        raise HTTPException(
            status_code=400,
            detail="records must not be empty",
        )

    df = pd.DataFrame(
        payload.records
    )

    return DatasetPreviewResponse(
        file_name=payload.file_name,
        preview_rows=(
            df.head(10)
            .where(
                pd.notnull(df),
                None,
            )
            .to_dict(
                orient="records"
            )
        ),
        total_rows=int(
            df.shape[0]
        ),
    )


@router.post("/quality")
def get_dataset_quality(
    payload: DatasetRecordsRequest,
):
    if not payload.records:
        raise HTTPException(
            status_code=400,
            detail="records must not be empty",
        )

    df = pd.DataFrame(payload.records)
    quality_report = run_quality_checks(df)

    return {
        "summary": quality_report["summary"],
        "issues": quality_report["issues"],
        "issue_records": (
            quality_report["issues_df"]
            .to_dict(
                orient="records",
            )
        ),
        "missing_records": (
            quality_report["missing_summary"]
            .to_dict(
                orient="records",
            )
        ),
        "duplicate_row_records": (
            quality_report["duplicate_rows_df"]
            .to_dict(
                orient="records",
            )
        ),
        "type_issue_records": (
            quality_report["type_issues_df"]
            .to_dict(
                orient="records",
            )
        ),
        "range_issue_records": (
            quality_report["range_issues_df"]
            .to_dict(
                orient="records",
            )
        ),
        "categorical_issue_records": (
            quality_report["categorical_issues_df"]
            .to_dict(
                orient="records",
            )
        ),
    }


@router.get(
    "/catalogs/{catalog_id}/lineage",
    response_model=CatalogLineageResponse,
)
def get_dataset_catalog_lineage(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
) -> CatalogLineageResponse:
    try:
        lineage_df = get_catalog_lineage(
            catalog_id
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "catalog lineage."
            ),
        ) from exc

    return CatalogLineageResponse(
        records=lineage_df.to_dict(
            orient="records",
        )
    )


@router.get(
    "/catalogs/{catalog_id}/versions",
    response_model=DatasetVersionHistoryResponse,
)
def get_catalog_dataset_versions(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
) -> DatasetVersionHistoryResponse:
    try:
        version_history = get_dataset_version_history(
            catalog_id
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "dataset version history."
            ),
        ) from exc

    normalized = (
        version_history.astype(object)
        .where(
            pd.notna(version_history),
            None,
        )
    )

    return DatasetVersionHistoryResponse(
        records=normalized.to_dict(
            orient="records",
        )
    )


@router.get(
    "/catalogs/{catalog_id}/ingestions",
    response_model=DatasetIngestionHistoryResponse,
)
def get_catalog_ingestion_history(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=1000,
    ),
) -> DatasetIngestionHistoryResponse:
    try:
        ingestion_history = get_ingestion_history(
            catalog_id,
            limit=limit,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "ingestion history."
            ),
        ) from exc

    normalized = (
        ingestion_history.astype(object)
        .where(
            pd.notna(ingestion_history),
            None,
        )
    )

    return DatasetIngestionHistoryResponse(
        records=normalized.to_dict(
            orient="records",
        )
    )


@router.get(
    "/catalogs/{catalog_id}/validations",
    response_model=DatasetValidationHistoryResponse,
)
def get_catalog_validation_history(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=1000,
    ),
) -> DatasetValidationHistoryResponse:
    try:
        validation_history = get_validation_history(
            catalog_id,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "validation history."
            ),
        ) from exc

    normalized = (
        validation_history.astype(object)
        .where(
            pd.notna(validation_history),
            None,
        )
    )

    return DatasetValidationHistoryResponse(
        records=normalized.to_dict(
            orient="records",
        )
    )


@router.get(
    "/catalogs/{catalog_id}/governance",
    response_model=DatasetGovernanceHistoryResponse,
)
def get_catalog_governance_history(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=1000,
    ),
) -> DatasetGovernanceHistoryResponse:
    try:
        governance_history = get_governance_history(
            catalog_id,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "governance history."
            ),
        ) from exc

    normalized = (
        governance_history.astype(object)
        .where(
            pd.notna(governance_history),
            None,
        )
    )

    return DatasetGovernanceHistoryResponse(
        records=normalized.to_dict(
            orient="records",
        )
    )


@router.get(
    "/catalogs/{catalog_id}/lifecycle",
    response_model=DatasetCatalogLifecycleResponse,
)
def get_dataset_catalog_lifecycle(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
) -> DatasetCatalogLifecycleResponse:
    try:
        lifecycle = get_catalog_lifecycle(
            catalog_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "catalog lifecycle."
            ),
        ) from exc

    normalized = (
        lifecycle.astype(object)
        .where(
            pd.notna(lifecycle),
            None,
        )
    )

    return DatasetCatalogLifecycleResponse(
        records=normalized.to_dict(
            orient="records",
        )
    )


@router.get(
    "/{version_id}/lifecycle",
    response_model=DatasetLifecycleHistoryResponse,
)
def get_dataset_lifecycle_history(
    version_id: int = Path(
        ...,
        gt=0,
    ),
) -> DatasetLifecycleHistoryResponse:
    try:
        lifecycle_history = get_lifecycle_history(
            version_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "lifecycle history."
            ),
        ) from exc

    normalized = (
        lifecycle_history.astype(object)
        .where(
            pd.notna(lifecycle_history),
            None,
        )
    )

    return DatasetLifecycleHistoryResponse(
        records=normalized.to_dict(
            orient="records",
        )
    )


@router.get(
    "/{version_id}/lineage",
    response_model=DatasetLineageResponse,
)
def get_dataset_lineage(
    version_id: int = Path(
        ...,
        gt=0,
    ),
):
    """
    Return end-to-end lineage for one dataset version.

    FastAPI acts only as the transport layer.
    The lineage repository remains the source of truth.
    """

    try:
        return get_version_lineage(
            version_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "dataset lineage."
            ),
        ) from exc


@router.post(
    "/{version_id}/promote",
    response_model=DatasetPromotionResponse,
)
def promote_dataset_version(
    version_id: int = Path(
        ...,
        gt=0,
    ),
):
    """
    Promote one governed dataset version to ACTIVE.

    The API does not implement promotion policy itself.
    Governance and lifecycle enforcement remain inside
    the version repository.
    """

    try:
        before_lineage = get_version_lineage(
            version_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load dataset version "
                "before promotion."
            ),
        ) from exc

    before_summary = before_lineage[
        "summary"
    ]

    catalog_id = int(
        before_summary[
            "catalog_id"
        ]
    )

    previous_state = str(
        before_summary[
            "lifecycle_state"
        ]
    )

    try:
        promotion_result = promote_version(
            catalog_id=catalog_id,
            version_id=version_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to promote "
                "dataset version."
            ),
        ) from exc

    try:
        after_lineage = get_version_lineage(
            version_id
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Dataset was promoted but "
                "the updated lineage could not be loaded."
            ),
        ) from exc

    after_summary = after_lineage[
        "summary"
    ]

    changed = bool(
        promotion_result.get(
            "changed",
            True,
        )
    )

    return DatasetPromotionResponse(
        version_id=version_id,
        catalog_id=catalog_id,
        previous_state=previous_state,
        lifecycle_state=str(
            after_summary[
                "lifecycle_state"
            ]
        ),
        changed=changed,
        governance_decision=(
            after_summary.get(
                "latest_governance_decision"
            )
        ),
        message=(
            "Dataset version promoted "
            "to ACTIVE successfully."
            if changed
            else (
                "Dataset version is already ACTIVE; "
                "no changes were applied."
            )
        ),
    )