from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

import pandas as pd

from src.ingestion.schema_infer import (
    infer_column_types,
)

CONTRACT_TYPES = {
    "NUMERIC",
    "CATEGORICAL",
    "DATETIME",
    "BOOLEAN",
    "TEXT",
}

VIOLATION_TYPES = {
    "MISSING_REQUIRED_COLUMN",
    "UNEXPECTED_COLUMN",
    "TYPE_MISMATCH",
    "NULLABILITY_VIOLATION",
}


@dataclass(frozen=True)
class ContractViolation:
    violation_type: str
    column_name: str | None
    expected_value: str | None
    actual_value: str | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContractValidationResult:
    status: str

    missing_required_count: int
    unexpected_column_count: int
    type_mismatch_count: int
    nullability_violation_count: int
    violation_count: int

    violations: tuple[
        ContractViolation,
        ...,
    ]

    @property
    def is_compatible(self) -> bool:
        return self.status == "COMPATIBLE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "is_compatible": self.is_compatible,
            "missing_required_count": (
                self.missing_required_count
            ),
            "unexpected_column_count": (
                self.unexpected_column_count
            ),
            "type_mismatch_count": (
                self.type_mismatch_count
            ),
            "nullability_violation_count": (
                self.nullability_violation_count
            ),
            "violation_count": (
                self.violation_count
            ),
            "violations": [
                violation.to_dict()
                for violation
                in self.violations
            ],
        }


def _coerce_bool(
    value: Any,
    *,
    field_name: str,
) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        if value in {0, 1}:
            return bool(value)

    if isinstance(value, str):
        normalized = (
            value.strip().lower()
        )

        if normalized in {
            "1",
            "true",
            "yes",
        }:
            return True

        if normalized in {
            "0",
            "false",
            "no",
        }:
            return False

    raise ValueError(
        f"{field_name} must be boolean-compatible."
    )


def _normalize_contract_columns(
    contract_columns: Iterable[
        Mapping[str, Any]
    ],
) -> dict[str, dict[str, Any]]:
    normalized: dict[
        str,
        dict[str, Any],
    ] = {}

    for raw_column in contract_columns:
        column_name = str(
            raw_column.get(
                "column_name",
                "",
            )
        ).strip()

        if not column_name:
            raise ValueError(
                "Contract column_name "
                "must not be empty."
            )

        if column_name in normalized:
            raise ValueError(
                "Duplicate contract column: "
                f"{column_name}"
            )

        expected_type = str(
            raw_column.get(
                "expected_type",
                "",
            )
        ).strip().upper()

        if expected_type not in CONTRACT_TYPES:
            raise ValueError(
                "Unsupported contract type "
                f"for '{column_name}': "
                f"{expected_type}"
            )

        is_required = _coerce_bool(
            raw_column.get(
                "is_required",
                True,
            ),
            field_name=(
                f"{column_name}.is_required"
            ),
        )

        is_nullable = _coerce_bool(
            raw_column.get(
                "is_nullable",
                True,
            ),
            field_name=(
                f"{column_name}.is_nullable"
            ),
        )

        normalized[column_name] = {
            "column_name": column_name,
            "expected_type": expected_type,
            "is_required": is_required,
            "is_nullable": is_nullable,
        }

    return normalized


def infer_contract_types(
    df: pd.DataFrame,
) -> dict[str, str]:
    """
    Convert the platform's existing column-type
    inference into Data Contract semantic types.
    """
    inferred = infer_column_types(
        df
    )

    type_groups = {
        "NUMERIC": inferred[
            "numeric_columns"
        ],
        "CATEGORICAL": inferred[
            "categorical_columns"
        ],
        "DATETIME": inferred[
            "datetime_columns"
        ],
        "BOOLEAN": inferred[
            "boolean_columns"
        ],
        "TEXT": inferred[
            "text_columns"
        ],
    }

    result: dict[str, str] = {}

    for contract_type, columns in (
        type_groups.items()
    ):
        for column in columns:
            column_name = str(column)

            if column_name in result:
                raise RuntimeError(
                    "Column was classified "
                    "more than once: "
                    f"{column_name}"
                )

            result[
                column_name
            ] = contract_type

    actual_names = {
        str(column)
        for column in df.columns
    }

    missing_classifications = (
        actual_names
        - set(result)
    )

    if missing_classifications:
        missing_text = ", ".join(
            sorted(
                missing_classifications
            )
        )

        raise RuntimeError(
            "Unable to classify columns: "
            f"{missing_text}"
        )

    return result


class DataContractEngine:
    """
    Evaluate one DataFrame against a versioned
    Data Contract schema.

    Compatibility v1 treats every persisted
    contract violation as BREAKING.

    Workflow enforcement such as BLOCK versus
    WARN is deliberately handled outside this
    engine.
    """

    def validate(
        self,
        df: pd.DataFrame,
        contract_columns: Iterable[
            Mapping[str, Any]
        ],
    ) -> ContractValidationResult:
        if not isinstance(
            df,
            pd.DataFrame,
        ):
            raise TypeError(
                "df must be a pandas DataFrame."
            )

        expected = (
            _normalize_contract_columns(
                contract_columns
            )
        )

        actual_types = (
            infer_contract_types(
                df
            )
        )

        actual_columns = {
            str(column): column
            for column in df.columns
        }

        violations: list[
            ContractViolation
        ] = []

        for (
            column_name,
            specification,
        ) in expected.items():
            actual_column = (
                actual_columns.get(
                    column_name
                )
            )

            if actual_column is None:
                if specification[
                    "is_required"
                ]:
                    violations.append(
                        ContractViolation(
                            violation_type=(
                                "MISSING_REQUIRED_COLUMN"
                            ),
                            column_name=(
                                column_name
                            ),
                            expected_value=(
                                "present"
                            ),
                            actual_value=(
                                "missing"
                            ),
                            message=(
                                "Required column "
                                f"'{column_name}' "
                                "is missing."
                            ),
                        )
                    )

                continue

            expected_type = str(
                specification[
                    "expected_type"
                ]
            )

            actual_type = (
                actual_types[
                    column_name
                ]
            )

            if (
                actual_type
                != expected_type
            ):
                violations.append(
                    ContractViolation(
                        violation_type=(
                            "TYPE_MISMATCH"
                        ),
                        column_name=(
                            column_name
                        ),
                        expected_value=(
                            expected_type
                        ),
                        actual_value=(
                            actual_type
                        ),
                        message=(
                            "Column "
                            f"'{column_name}' "
                            "expected type "
                            f"{expected_type} "
                            "but received "
                            f"{actual_type}."
                        ),
                    )
                )

            if not specification[
                "is_nullable"
            ]:
                null_count = int(
                    df[
                        actual_column
                    ]
                    .isna()
                    .sum()
                )

                if null_count > 0:
                    violations.append(
                        ContractViolation(
                            violation_type=(
                                "NULLABILITY_VIOLATION"
                            ),
                            column_name=(
                                column_name
                            ),
                            expected_value=(
                                "non-null"
                            ),
                            actual_value=(
                                f"{null_count} null"
                                if null_count == 1
                                else (
                                    f"{null_count} "
                                    "nulls"
                                )
                            ),
                            message=(
                                "Non-nullable column "
                                f"'{column_name}' "
                                f"contains "
                                f"{null_count} "
                                "null value(s)."
                            ),
                        )
                    )

        unexpected_columns = sorted(
            set(actual_columns)
            - set(expected)
        )

        for column_name in (
            unexpected_columns
        ):
            violations.append(
                ContractViolation(
                    violation_type=(
                        "UNEXPECTED_COLUMN"
                    ),
                    column_name=column_name,
                    expected_value=(
                        "not defined"
                    ),
                    actual_value=(
                        actual_types[
                            column_name
                        ]
                    ),
                    message=(
                        "Column "
                        f"'{column_name}' "
                        "is not defined "
                        "in the contract."
                    ),
                )
            )

        missing_required_count = sum(
            violation.violation_type
            == "MISSING_REQUIRED_COLUMN"
            for violation in violations
        )

        unexpected_column_count = sum(
            violation.violation_type
            == "UNEXPECTED_COLUMN"
            for violation in violations
        )

        type_mismatch_count = sum(
            violation.violation_type
            == "TYPE_MISMATCH"
            for violation in violations
        )

        nullability_violation_count = (
            sum(
                violation.violation_type
                == (
                    "NULLABILITY_VIOLATION"
                )
                for violation
                in violations
            )
        )

        violation_count = len(
            violations
        )

        status = (
            "COMPATIBLE"
            if violation_count == 0
            else "BREAKING"
        )

        return ContractValidationResult(
            status=status,
            missing_required_count=(
                missing_required_count
            ),
            unexpected_column_count=(
                unexpected_column_count
            ),
            type_mismatch_count=(
                type_mismatch_count
            ),
            nullability_violation_count=(
                nullability_violation_count
            ),
            violation_count=(
                violation_count
            ),
            violations=tuple(
                violations
            ),
        )


def validate_contract(
    df: pd.DataFrame,
    contract_columns: Iterable[
        Mapping[str, Any]
    ],
) -> ContractValidationResult:
    return DataContractEngine().validate(
        df,
        contract_columns,
    )