from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from sqlalchemy import text

from database.db import get_engine

CONTRACT_TYPES = {
    "NUMERIC",
    "CATEGORICAL",
    "DATETIME",
    "BOOLEAN",
    "TEXT",
}

ENFORCEMENT_MODES = {
    "BLOCK",
    "WARN",
}

VALIDATION_STATUSES = {
    "COMPATIBLE",
    "BREAKING",
}

VIOLATION_TYPES = {
    "MISSING_REQUIRED_COLUMN",
    "UNEXPECTED_COLUMN",
    "TYPE_MISMATCH",
    "NULLABILITY_VIOLATION",
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
        normalized = value.strip().lower()

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
    columns: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for raw_column in columns:
        column_name = str(
            raw_column.get(
                "column_name",
                "",
            )
        ).strip()

        if not column_name:
            raise ValueError(
                "Contract column_name must not be empty."
            )

        if column_name in seen_names:
            raise ValueError(
                "Duplicate contract column: "
                f"{column_name}"
            )

        seen_names.add(column_name)

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

        normalized.append(
            {
                "column_name": column_name,
                "expected_type": expected_type,
                "is_required": int(
                    _coerce_bool(
                        raw_column.get(
                            "is_required",
                            True,
                        ),
                        field_name=(
                            f"{column_name}.is_required"
                        ),
                    )
                ),
                "is_nullable": int(
                    _coerce_bool(
                        raw_column.get(
                            "is_nullable",
                            True,
                        ),
                        field_name=(
                            f"{column_name}.is_nullable"
                        ),
                    )
                ),
            }
        )

    if not normalized:
        raise ValueError(
            "A data contract must define "
            "at least one column."
        )

    return normalized


def _normalize_enforcement_mode(
    enforcement_mode: str,
) -> str:
    normalized = str(
        enforcement_mode
    ).strip().upper()

    if normalized not in ENFORCEMENT_MODES:
        raise ValueError(
            "Unsupported enforcement mode: "
            f"{enforcement_mode}"
        )

    return normalized


def _build_contract_record(
    contract_row: Mapping[str, Any],
    column_rows: Iterable[
        Mapping[str, Any]
    ],
) -> dict[str, Any]:
    contract = dict(contract_row)

    contract["is_active"] = bool(
        contract["is_active"]
    )

    columns: list[dict[str, Any]] = []

    for raw_column in column_rows:
        column = dict(raw_column)

        column["is_required"] = bool(
            column["is_required"]
        )
        column["is_nullable"] = bool(
            column["is_nullable"]
        )

        columns.append(column)

    contract["columns"] = columns

    return contract


def create_data_contract(
    *,
    catalog_id: int,
    contract_name: str,
    columns: Iterable[
        Mapping[str, Any]
    ],
    enforcement_mode: str = "BLOCK",
    activate: bool = True,
) -> dict[str, Any]:
    normalized_name = str(
        contract_name
    ).strip()

    if not normalized_name:
        raise ValueError(
            "contract_name must not be empty."
        )

    normalized_mode = (
        _normalize_enforcement_mode(
            enforcement_mode
        )
    )

    normalized_columns = (
        _normalize_contract_columns(
            columns
        )
    )

    next_version_query = text(
        """
        SELECT
            COALESCE(
                MAX(contract_version),
                0
            ) + 1
        FROM dbo.data_contracts
            WITH (
                UPDLOCK,
                HOLDLOCK
            )
        WHERE catalog_id = :catalog_id;
        """
    )

    deactivate_query = text(
        """
        UPDATE dbo.data_contracts
        SET
            is_active = 0,
            updated_at = SYSUTCDATETIME()
        WHERE catalog_id = :catalog_id
          AND is_active = 1;
        """
    )

    insert_contract_query = text(
        """
        INSERT INTO dbo.data_contracts (
            catalog_id,
            contract_version,
            contract_name,
            enforcement_mode,
            is_active
        )
        OUTPUT INSERTED.contract_id
        VALUES (
            :catalog_id,
            :contract_version,
            :contract_name,
            :enforcement_mode,
            :is_active
        );
        """
    )

    insert_column_query = text(
        """
        INSERT INTO dbo.data_contract_columns (
            contract_id,
            column_name,
            expected_type,
            is_required,
            is_nullable
        )
        VALUES (
            :contract_id,
            :column_name,
            :expected_type,
            :is_required,
            :is_nullable
        );
        """
    )

    engine = get_engine()

    with engine.begin() as connection:
        contract_version = int(
            connection.execute(
                next_version_query,
                {
                    "catalog_id": int(
                        catalog_id
                    ),
                },
            ).scalar_one()
        )

        if activate:
            connection.execute(
                deactivate_query,
                {
                    "catalog_id": int(
                        catalog_id
                    ),
                },
            )

        contract_id = int(
            connection.execute(
                insert_contract_query,
                {
                    "catalog_id": int(
                        catalog_id
                    ),
                    "contract_version": (
                        contract_version
                    ),
                    "contract_name": (
                        normalized_name
                    ),
                    "enforcement_mode": (
                        normalized_mode
                    ),
                    "is_active": int(
                        bool(activate)
                    ),
                },
            ).scalar_one()
        )

        column_params = [
            {
                "contract_id": contract_id,
                **column,
            }
            for column in normalized_columns
        ]

        connection.execute(
            insert_column_query,
            column_params,
        )

    created_contract = get_data_contract(
        contract_id
    )

    if created_contract is None:
        raise RuntimeError(
            "Data contract was created but "
            "could not be loaded."
        )

    return created_contract


def get_data_contract(
    contract_id: int,
) -> dict[str, Any] | None:
    contract_query = text(
        """
        SELECT
            contract_id,
            catalog_id,
            contract_version,
            contract_name,
            enforcement_mode,
            is_active,
            created_at,
            updated_at
        FROM dbo.data_contracts
        WHERE contract_id = :contract_id;
        """
    )

    columns_query = text(
        """
        SELECT
            contract_column_id,
            contract_id,
            column_name,
            expected_type,
            is_required,
            is_nullable,
            created_at
        FROM dbo.data_contract_columns
        WHERE contract_id = :contract_id
        ORDER BY contract_column_id;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        contract_row = connection.execute(
            contract_query,
            {
                "contract_id": int(
                    contract_id
                ),
            },
        ).mappings().first()

        if contract_row is None:
            return None

        column_rows = connection.execute(
            columns_query,
            {
                "contract_id": int(
                    contract_id
                ),
            },
        ).mappings().all()

    return _build_contract_record(
        contract_row,
        column_rows,
    )


def get_data_contract_history(
    catalog_id: int,
) -> list[dict[str, Any]]:
    contract_query = text(
        """
        SELECT
            contract_id,
            catalog_id,
            contract_version,
            contract_name,
            enforcement_mode,
            is_active,
            created_at,
            updated_at
        FROM dbo.data_contracts
        WHERE catalog_id = :catalog_id
        ORDER BY contract_version DESC;
        """
    )

    columns_query = text(
        """
        SELECT
            dcc.contract_column_id,
            dcc.contract_id,
            dcc.column_name,
            dcc.expected_type,
            dcc.is_required,
            dcc.is_nullable,
            dcc.created_at
        FROM dbo.data_contract_columns AS dcc
        INNER JOIN dbo.data_contracts AS dc
            ON dc.contract_id = dcc.contract_id
        WHERE dc.catalog_id = :catalog_id
        ORDER BY
            dc.contract_version DESC,
            dcc.contract_column_id;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        contract_rows = connection.execute(
            contract_query,
            {
                "catalog_id": int(
                    catalog_id
                ),
            },
        ).mappings().all()

        if not contract_rows:
            return []

        column_rows = connection.execute(
            columns_query,
            {
                "catalog_id": int(
                    catalog_id
                ),
            },
        ).mappings().all()

    columns_by_contract: dict[
        int,
        list[dict[str, Any]],
    ] = {}

    for row in column_rows:
        contract_id = int(
            row["contract_id"]
        )

        columns_by_contract.setdefault(
            contract_id,
            [],
        ).append(
            dict(row)
        )

    return [
        _build_contract_record(
            contract_row,
            columns_by_contract.get(
                int(
                    contract_row[
                        "contract_id"
                    ]
                ),
                [],
            ),
        )
        for contract_row in contract_rows
    ]


def get_active_data_contract(
    catalog_id: int,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT TOP 1
            contract_id
        FROM dbo.data_contracts
        WHERE catalog_id = :catalog_id
          AND is_active = 1
        ORDER BY contract_version DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "catalog_id": int(
                    catalog_id
                ),
            },
        ).mappings().first()

    if row is None:
        return None

    return get_data_contract(
        int(row["contract_id"])
    )


def activate_data_contract(
    contract_id: int,
) -> dict[str, Any]:
    load_query = text(
        """
        SELECT
            contract_id,
            catalog_id
        FROM dbo.data_contracts
            WITH (
                UPDLOCK,
                HOLDLOCK
            )
        WHERE contract_id = :contract_id;
        """
    )

    deactivate_query = text(
        """
        UPDATE dbo.data_contracts
        SET
            is_active = 0,
            updated_at = SYSUTCDATETIME()
        WHERE catalog_id = :catalog_id
          AND is_active = 1;
        """
    )

    activate_query = text(
        """
        UPDATE dbo.data_contracts
        SET
            is_active = 1,
            updated_at = SYSUTCDATETIME()
        WHERE contract_id = :contract_id;
        """
    )

    engine = get_engine()

    with engine.begin() as connection:
        contract = connection.execute(
            load_query,
            {
                "contract_id": int(
                    contract_id
                ),
            },
        ).mappings().first()

        if contract is None:
            raise ValueError(
                "Data contract not found: "
                f"{contract_id}"
            )

        catalog_id = int(
            contract["catalog_id"]
        )

        connection.execute(
            deactivate_query,
            {
                "catalog_id": catalog_id,
            },
        )

        result = connection.execute(
            activate_query,
            {
                "contract_id": int(
                    contract_id
                ),
            },
        )

        if result.rowcount != 1:
            raise ValueError(
                "Data contract not found: "
                f"{contract_id}"
            )

    activated = get_data_contract(
        contract_id
    )

    if activated is None:
        raise RuntimeError(
            "Data contract was activated but "
            "could not be loaded."
        )

    return activated


def _normalize_validation_payload(
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    status = str(
        validation.get(
            "status",
            "",
        )
    ).strip().upper()

    if status not in VALIDATION_STATUSES:
        raise ValueError(
            "Unsupported contract "
            f"validation status: {status}"
        )

    count_names = (
        "missing_required_count",
        "unexpected_column_count",
        "type_mismatch_count",
        "nullability_violation_count",
    )

    counts: dict[str, int] = {}

    for count_name in count_names:
        count = int(
            validation.get(
                count_name,
                0,
            )
        )

        if count < 0:
            raise ValueError(
                f"{count_name} must be >= 0."
            )

        counts[count_name] = count

    raw_violations = validation.get(
        "violations",
        [],
    )

    violations: list[
        dict[str, Any]
    ] = []

    for raw_violation in raw_violations:
        violation_type = str(
            raw_violation.get(
                "violation_type",
                "",
            )
        ).strip().upper()

        if (
            violation_type
            not in VIOLATION_TYPES
        ):
            raise ValueError(
                "Unsupported contract "
                "violation type: "
                f"{violation_type}"
            )

        message = str(
            raw_violation.get(
                "message",
                "",
            )
        ).strip()

        if not message:
            raise ValueError(
                "Contract violation message "
                "must not be empty."
            )

        violations.append(
            {
                "column_name": (
                    raw_violation.get(
                        "column_name"
                    )
                ),
                "violation_type": (
                    violation_type
                ),
                "expected_value": (
                    raw_violation.get(
                        "expected_value"
                    )
                ),
                "actual_value": (
                    raw_violation.get(
                        "actual_value"
                    )
                ),
                "message": message,
            }
        )

    violation_count = int(
        validation.get(
            "violation_count",
            len(violations),
        )
    )

    if violation_count != len(
        violations
    ):
        raise ValueError(
            "violation_count does not match "
            "the number of violations."
        )

    categorized_count = sum(
        counts.values()
    )

    if categorized_count != (
        violation_count
    ):
        raise ValueError(
            "Contract violation category "
            "counts do not match "
            "violation_count."
        )

    if (
        status == "COMPATIBLE"
        and violation_count != 0
    ):
        raise ValueError(
            "COMPATIBLE validation cannot "
            "contain violations."
        )

    if (
        status == "BREAKING"
        and violation_count == 0
    ):
        raise ValueError(
            "BREAKING validation must "
            "contain at least one violation."
        )

    return {
        "status": status,
        **counts,
        "violation_count": (
            violation_count
        ),
        "violations": violations,
    }


def save_contract_validation(
    *,
    contract_id: int,
    catalog_id: int,
    version_id: int,
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = (
        _normalize_validation_payload(
            validation
        )
    )

    relationship_query = text(
        """
        SELECT TOP 1
            c.contract_id
        FROM dbo.data_contracts AS c
        INNER JOIN dbo.dataset_versions AS v
            ON v.version_id = :version_id
           AND v.catalog_id = :catalog_id
        WHERE c.contract_id = :contract_id
          AND c.catalog_id = :catalog_id;
        """
    )

    insert_validation_query = text(
        """
        INSERT INTO dbo.contract_validation_history (
            contract_id,
            catalog_id,
            version_id,
            validation_status,
            missing_required_count,
            unexpected_column_count,
            type_mismatch_count,
            nullability_violation_count,
            violation_count
        )
        OUTPUT
            INSERTED.contract_validation_id
        VALUES (
            :contract_id,
            :catalog_id,
            :version_id,
            :validation_status,
            :missing_required_count,
            :unexpected_column_count,
            :type_mismatch_count,
            :nullability_violation_count,
            :violation_count
        );
        """
    )

    insert_violation_query = text(
        """
        INSERT INTO dbo.contract_violations (
            contract_validation_id,
            column_name,
            violation_type,
            expected_value,
            actual_value,
            message
        )
        VALUES (
            :contract_validation_id,
            :column_name,
            :violation_type,
            :expected_value,
            :actual_value,
            :message
        );
        """
    )

    engine = get_engine()

    with engine.begin() as connection:
        relationship = connection.execute(
            relationship_query,
            {
                "contract_id": int(
                    contract_id
                ),
                "catalog_id": int(
                    catalog_id
                ),
                "version_id": int(
                    version_id
                ),
            },
        ).mappings().first()

        if relationship is None:
            raise ValueError(
                "Contract, catalog and "
                "dataset version do not "
                "belong to the same dataset."
            )

        contract_validation_id = int(
            connection.execute(
                insert_validation_query,
                {
                    "contract_id": int(
                        contract_id
                    ),
                    "catalog_id": int(
                        catalog_id
                    ),
                    "version_id": int(
                        version_id
                    ),
                    "validation_status": (
                        normalized["status"]
                    ),
                    "missing_required_count": (
                        normalized[
                            "missing_required_count"
                        ]
                    ),
                    "unexpected_column_count": (
                        normalized[
                            "unexpected_column_count"
                        ]
                    ),
                    "type_mismatch_count": (
                        normalized[
                            "type_mismatch_count"
                        ]
                    ),
                    "nullability_violation_count": (
                        normalized[
                            "nullability_violation_count"
                        ]
                    ),
                    "violation_count": (
                        normalized[
                            "violation_count"
                        ]
                    ),
                },
            ).scalar_one()
        )

        violations = normalized[
            "violations"
        ]

        if violations:
            violation_params = [
                {
                    "contract_validation_id": (
                        contract_validation_id
                    ),
                    **violation,
                }
                for violation in violations
            ]

            connection.execute(
                insert_violation_query,
                violation_params,
            )

    saved_validation = (
        get_contract_validation(
            contract_validation_id
        )
    )

    if saved_validation is None:
        raise RuntimeError(
            "Contract validation was saved "
            "but could not be loaded."
        )

    return saved_validation


def get_contract_validation(
    contract_validation_id: int,
) -> dict[str, Any] | None:
    validation_query = text(
        """
        SELECT
            contract_validation_id,
            contract_id,
            catalog_id,
            version_id,
            validation_status,
            missing_required_count,
            unexpected_column_count,
            type_mismatch_count,
            nullability_violation_count,
            violation_count,
            validated_at
        FROM dbo.contract_validation_history
        WHERE contract_validation_id =
            :contract_validation_id;
        """
    )

    violations_query = text(
        """
        SELECT
            violation_id,
            contract_validation_id,
            column_name,
            violation_type,
            expected_value,
            actual_value,
            message,
            created_at
        FROM dbo.contract_violations
        WHERE contract_validation_id =
            :contract_validation_id
        ORDER BY violation_id;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        validation_row = connection.execute(
            validation_query,
            {
                "contract_validation_id": int(
                    contract_validation_id
                ),
            },
        ).mappings().first()

        if validation_row is None:
            return None

        violation_rows = connection.execute(
            violations_query,
            {
                "contract_validation_id": int(
                    contract_validation_id
                ),
            },
        ).mappings().all()

    result = dict(validation_row)

    result["violations"] = [
        dict(row)
        for row in violation_rows
    ]

    return result