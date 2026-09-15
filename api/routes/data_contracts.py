from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
)

from api.schemas.data_contract_schema import (
    DataContractCreateRequest,
    DataContractHistoryResponse,
    DataContractResponse,
)
from database.repositories.data_contract_repository import (
    activate_data_contract,
    create_data_contract,
    get_active_data_contract,
    get_data_contract,
    get_data_contract_history,
)

router = APIRouter()


@router.post(
    "",
    response_model=DataContractResponse,
    status_code=201,
)
def create_contract(
    payload: DataContractCreateRequest,
):
    try:
        return create_data_contract(
            catalog_id=payload.catalog_id,
            contract_name=(
                payload.contract_name
            ),
            enforcement_mode=(
                payload.enforcement_mode
            ),
            activate=payload.activate,
            columns=[
                column.model_dump()
                for column
                in payload.columns
            ],
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
                "Unable to create "
                "Data Contract."
            ),
        ) from exc


@router.get(
    "/catalog/{catalog_id}",
    response_model=(
        DataContractHistoryResponse
    ),
)
def get_contract_history(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        items = (
            get_data_contract_history(
                catalog_id
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "Data Contract history."
            ),
        ) from exc

    return DataContractHistoryResponse(
        catalog_id=catalog_id,
        count=len(items),
        items=items,
    )


@router.get(
    "/catalog/{catalog_id}/active",
    response_model=DataContractResponse,
)
def get_active_contract(
    catalog_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        contract = (
            get_active_data_contract(
                catalog_id
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load active "
                "Data Contract."
            ),
        ) from exc

    if contract is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No active Data Contract "
                f"for catalog_id={catalog_id}."
            ),
        )

    return contract


@router.get(
    "/{contract_id}",
    response_model=DataContractResponse,
)
def get_contract(
    contract_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        contract = get_data_contract(
            contract_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load "
                "Data Contract."
            ),
        ) from exc

    if contract is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Data Contract not found: "
                f"{contract_id}"
            ),
        )

    return contract


@router.post(
    "/{contract_id}/activate",
    response_model=DataContractResponse,
)
def activate_contract(
    contract_id: int = Path(
        ...,
        gt=0,
    ),
):
    try:
        return activate_data_contract(
            contract_id
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
                "Unable to activate "
                "Data Contract."
            ),
        ) from exc