from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ContractType = Literal[
    "NUMERIC",
    "CATEGORICAL",
    "DATETIME",
    "BOOLEAN",
    "TEXT",
]

EnforcementMode = Literal[
    "BLOCK",
    "WARN",
]


class DataContractColumnCreate(BaseModel):
    column_name: str = Field(
        ...,
        min_length=1,
    )
    expected_type: ContractType
    is_required: bool = True
    is_nullable: bool = True


class DataContractCreateRequest(BaseModel):
    catalog_id: int = Field(
        ...,
        gt=0,
    )
    contract_name: str = Field(
        ...,
        min_length=1,
    )
    enforcement_mode: EnforcementMode = (
        "BLOCK"
    )
    activate: bool = True
    columns: list[
        DataContractColumnCreate
    ] = Field(
        ...,
        min_length=1,
    )


class DataContractColumnResponse(BaseModel):
    contract_column_id: int
    contract_id: int
    column_name: str
    expected_type: str
    is_required: bool
    is_nullable: bool
    created_at: datetime | None = None


class DataContractResponse(BaseModel):
    contract_id: int
    catalog_id: int
    contract_version: int
    contract_name: str
    enforcement_mode: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    columns: list[
        DataContractColumnResponse
    ]


class DataContractHistoryResponse(
    BaseModel
):
    catalog_id: int
    count: int
    items: list[
        DataContractResponse
    ]