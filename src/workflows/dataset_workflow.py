from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from database.repositories.catalog_repository import (
    register_ingestion,
)
from database.repositories.data_contract_repository import (
    get_active_data_contract,
    save_contract_validation,
)
from database.repositories.governance_repository import (
    register_governance_decision,
)
from database.repositories.validation_repository import (
    register_validation,
)
from database.repositories.version_repository import (
    apply_validation_lifecycle,
)
from src.data_contracts.contract_engine import (
    validate_contract,
)
from src.governance.governance_service import (
    evaluate_dataset_governance,
)
from src.ingestion.contracts import IngestionResult
from src.ingestion.ingestion_service import ingest_dataset
from src.profiling.profiler import profile_dataset
from src.validation.validation_gate import (
    validate_and_route_dataset,
)
from src.workflows.contracts import (
    DatasetWorkflowError,
    DatasetWorkflowResult,
)


def _to_dict(
    value: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())

    return dict(value)


def _raise_stage_error(
    *,
    stage: str,
    exc: Exception,
) -> None:
    if isinstance(
        exc,
        DatasetWorkflowError,
    ):
        raise exc

    raise DatasetWorkflowError(
        stage=stage,
        cause=exc,
    ) from exc


def continue_dataset_workflow(
    ingestion_result: IngestionResult,
) -> DatasetWorkflowResult:
    """
    Continue the platform workflow after raw ingestion.

    Pipeline:

        IngestionResult
            -> Profile
            -> Catalog registration
            -> Validation Gate
            -> Validation persistence
            -> Governance evaluation
            -> Governance persistence
            -> Validation-driven lifecycle state

    Promotion to ACTIVE is deliberately NOT performed here.
    Promotion remains an explicit governed action.
    """

    try:
        dataframe = ingestion_result.dataframe

        if dataframe.empty:
            raise ValueError(
                "Không thể chạy workflow với dataset rỗng."
            )

        ingestion_metadata = (
            ingestion_result.metadata.to_dict()
        )

    except Exception as exc:
        _raise_stage_error(
            stage="INGESTION_RESULT",
            exc=exc,
        )

    try:
        profile = profile_dataset(
            dataframe
        )

    except Exception as exc:
        _raise_stage_error(
            stage="PROFILING",
            exc=exc,
        )

    try:
        catalog_registration = (
            register_ingestion(
                ingestion_metadata
            )
        )

    except Exception as exc:
        _raise_stage_error(
            stage="CATALOG_REGISTRATION",
            exc=exc,
        )

    data_contract = None
    contract_validation = None

    try:
        data_contract = (
            get_active_data_contract(
                int(
                    catalog_registration[
                        "catalog_id"
                    ]
                )
            )
        )

    except Exception as exc:
        _raise_stage_error(
            stage="DATA_CONTRACT_LOOKUP",
            exc=exc,
        )

    if data_contract is not None:
        try:
            contract_result = (
                validate_contract(
                    dataframe,
                    data_contract[
                        "columns"
                    ],
                )
            )

            contract_result_dict = (
                _to_dict(
                    contract_result
                )
            )

        except Exception as exc:
            _raise_stage_error(
                stage="DATA_CONTRACT_VALIDATION",
                exc=exc,
            )

        try:
            contract_validation = (
                save_contract_validation(
                    contract_id=int(
                        data_contract[
                            "contract_id"
                        ]
                    ),
                    catalog_id=int(
                        catalog_registration[
                            "catalog_id"
                        ]
                    ),
                    version_id=int(
                        catalog_registration[
                            "version_id"
                        ]
                    ),
                    validation=(
                        contract_result_dict
                    ),
                )
            )

        except Exception as exc:
            _raise_stage_error(
                stage="DATA_CONTRACT_PERSISTENCE",
                exc=exc,
            )

        contract_status = str(
            contract_result_dict[
                "status"
            ]
        ).upper()

        enforcement_mode = str(
            data_contract[
                "enforcement_mode"
            ]
        ).upper()

        if (
            contract_status == "BREAKING"
            and enforcement_mode == "BLOCK"
        ):
            violation_count = int(
                contract_result_dict[
                    "violation_count"
                ]
            )

            _raise_stage_error(
                stage="DATA_CONTRACT_GATE",
                exc=ValueError(
                    "Dataset violates active "
                    "Data Contract "
                    f"v{data_contract['contract_version']} "
                    "under BLOCK enforcement "
                    f"with {violation_count} "
                    "violation(s)."
                ),
            )

    try:
        gate_result = (
            validate_and_route_dataset(
                df=dataframe,
                ingestion_metadata=(
                    ingestion_metadata
                ),
            )
        )

        validation_result = _to_dict(
            gate_result
        )

    except Exception as exc:
        _raise_stage_error(
            stage="VALIDATION_GATE",
            exc=exc,
        )

    try:
        validation_registration = (
            register_validation(
                validation_result,
                catalog_registration,
            )
        )

    except Exception as exc:
        _raise_stage_error(
            stage="VALIDATION_PERSISTENCE",
            exc=exc,
        )

    try:
        governance_bundle = (
            evaluate_dataset_governance(
                df=dataframe,
                validation_result=(
                    validation_result
                ),
            )
        )

        governance_result = _to_dict(
            governance_bundle[
                "governance_result"
            ]
        )

        quality_report = dict(
            governance_bundle[
                "quality_report"
            ]
        )

        trust_score_report = dict(
            governance_bundle[
                "trust_score_report"
            ]
        )

        privacy_report = dict(
            governance_bundle[
                "privacy_report"
            ]
        )

    except Exception as exc:
        _raise_stage_error(
            stage="GOVERNANCE_EVALUATION",
            exc=exc,
        )

    try:
        governance_registration = (
            register_governance_decision(
                governance_result=(
                    governance_result
                ),
                catalog_registration=(
                    catalog_registration
                ),
                validation_registration=(
                    validation_registration
                ),
            )
        )

    except Exception as exc:
        _raise_stage_error(
            stage="GOVERNANCE_PERSISTENCE",
            exc=exc,
        )

    try:
        lifecycle_result = (
            apply_validation_lifecycle(
                catalog_registration,
                validation_result,
            )
        )

    except Exception as exc:
        _raise_stage_error(
            stage="LIFECYCLE_SYNC",
            exc=exc,
        )

    return DatasetWorkflowResult(
        dataframe=dataframe,
        profile=profile,
        ingestion_metadata=(
            ingestion_metadata
        ),
        catalog_registration=(
            catalog_registration
        ),
        validation_result=(
            validation_result
        ),
        validation_registration=(
            validation_registration
        ),
        governance_result=(
            governance_result
        ),
        governance_registration=(
            governance_registration
        ),
        lifecycle_result=(
            lifecycle_result
        ),
        quality_report=(
            quality_report
        ),
        trust_score_report=(
            trust_score_report
        ),
        privacy_report=(
            privacy_report
        ),
        data_contract=(
            data_contract
        ),
        contract_validation=(
            contract_validation
        ),
    )


def run_dataset_workflow(
    source: Any,
    *,
    persist_raw: bool = True,
    raw_root: str | Path | None = None,
) -> DatasetWorkflowResult:
    """
    Full dataset-platform orchestration entrypoint.

    This is the function future callers should use:

    - Streamlit
    - FastAPI
    - Airflow
    - CLI/batch jobs

    It deliberately stops before ACTIVE promotion.
    """

    try:
        if raw_root is None:
            ingestion_result = (
                ingest_dataset(
                    source,
                    persist_raw=persist_raw,
                )
            )

        else:
            ingestion_result = (
                ingest_dataset(
                    source,
                    persist_raw=persist_raw,
                    raw_root=raw_root,
                )
            )

    except Exception as exc:
        _raise_stage_error(
            stage="INGESTION",
            exc=exc,
        )

    return continue_dataset_workflow(
        ingestion_result
    )