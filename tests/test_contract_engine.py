from __future__ import annotations

import pandas as pd
import pytest

from src.data_contracts.contract_engine import (
    DataContractEngine,
    infer_contract_types,
    validate_contract,
)


def test_infer_contract_types():
    df = pd.DataFrame(
        {
            "age": [20, 30, 40, 50],
            "segment": [
                "A",
                "A",
                "B",
                "B",
            ],
            "event_date": pd.to_datetime(
                [
                    "2026-01-01",
                    "2026-01-02",
                    "2026-01-03",
                    "2026-01-04",
                ]
            ),
            "is_active": [
                True,
                False,
                True,
                False,
            ],
            "note": [
                "alpha note",
                "beta note",
                "gamma note",
                "delta note",
            ],
        }
    )

    result = infer_contract_types(
        df
    )

    assert result == {
        "age": "NUMERIC",
        "segment": "CATEGORICAL",
        "event_date": "DATETIME",
        "is_active": "BOOLEAN",
        "note": "TEXT",
    }


def test_compatible_contract():
    df = pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
                3,
            ],
            "is_active": [
                True,
                False,
                True,
            ],
        }
    )

    contract = [
        {
            "column_name": "customer_id",
            "expected_type": "NUMERIC",
            "is_required": True,
            "is_nullable": False,
        },
        {
            "column_name": "is_active",
            "expected_type": "BOOLEAN",
            "is_required": True,
            "is_nullable": False,
        },
    ]

    result = validate_contract(
        df,
        contract,
    )

    assert result.status == "COMPATIBLE"
    assert result.is_compatible is True
    assert result.violation_count == 0
    assert result.violations == ()


def test_missing_required_column_is_breaking():
    df = pd.DataFrame(
        {
            "name": [
                "Alice",
                "Bob",
            ],
        }
    )

    contract = [
        {
            "column_name": "name",
            "expected_type": "TEXT",
            "is_required": True,
            "is_nullable": False,
        },
        {
            "column_name": "customer_id",
            "expected_type": "NUMERIC",
            "is_required": True,
            "is_nullable": False,
        },
    ]

    result = validate_contract(
        df,
        contract,
    )

    assert result.status == "BREAKING"
    assert result.missing_required_count == 1
    assert result.violation_count == 1

    violation = result.violations[0]

    assert (
        violation.violation_type
        == "MISSING_REQUIRED_COLUMN"
    )

    assert (
        violation.column_name
        == "customer_id"
    )


def test_missing_optional_column_is_allowed():
    df = pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
            ],
        }
    )

    contract = [
        {
            "column_name": "customer_id",
            "expected_type": "NUMERIC",
            "is_required": True,
            "is_nullable": False,
        },
        {
            "column_name": "nickname",
            "expected_type": "TEXT",
            "is_required": False,
            "is_nullable": True,
        },
    ]

    result = validate_contract(
        df,
        contract,
    )

    assert result.status == "COMPATIBLE"
    assert result.violation_count == 0


def test_unexpected_column_is_breaking():
    df = pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
            ],
            "new_field": [
                "x",
                "y",
            ],
        }
    )

    contract = [
        {
            "column_name": "customer_id",
            "expected_type": "NUMERIC",
            "is_required": True,
            "is_nullable": False,
        },
    ]

    result = validate_contract(
        df,
        contract,
    )

    assert result.status == "BREAKING"
    assert result.unexpected_column_count == 1

    assert (
        result.violations[0]
        .violation_type
        == "UNEXPECTED_COLUMN"
    )


def test_type_mismatch_is_breaking():
    df = pd.DataFrame(
        {
            "customer_id": [
                "A-1",
                "B-2",
                "C-3",
            ],
        }
    )

    contract = [
        {
            "column_name": "customer_id",
            "expected_type": "NUMERIC",
            "is_required": True,
            "is_nullable": False,
        },
    ]

    result = validate_contract(
        df,
        contract,
    )

    assert result.status == "BREAKING"
    assert result.type_mismatch_count == 1

    violation = result.violations[0]

    assert (
        violation.violation_type
        == "TYPE_MISMATCH"
    )
    assert (
        violation.expected_value
        == "NUMERIC"
    )
    assert (
        violation.actual_value
        == "TEXT"
    )


def test_nullability_violation_is_breaking():
    df = pd.DataFrame(
        {
            "customer_id": [
                1.0,
                None,
                3.0,
            ],
        }
    )

    contract = [
        {
            "column_name": "customer_id",
            "expected_type": "NUMERIC",
            "is_required": True,
            "is_nullable": False,
        },
    ]

    result = validate_contract(
        df,
        contract,
    )

    assert result.status == "BREAKING"
    assert (
        result.nullability_violation_count
        == 1
    )

    violation = result.violations[0]

    assert (
        violation.violation_type
        == "NULLABILITY_VIOLATION"
    )


def test_nullable_column_accepts_nulls():
    df = pd.DataFrame(
        {
            "score": [
                10.0,
                None,
                20.0,
            ],
        }
    )

    contract = [
        {
            "column_name": "score",
            "expected_type": "NUMERIC",
            "is_required": True,
            "is_nullable": True,
        },
    ]

    result = validate_contract(
        df,
        contract,
    )

    assert result.status == "COMPATIBLE"
    assert result.violation_count == 0


def test_multiple_violation_counts():
    df = pd.DataFrame(
        {
            "customer_id": [
                "A",
                "B",
            ],
            "extra": [
                1,
                2,
            ],
        }
    )

    contract = [
        {
            "column_name": "customer_id",
            "expected_type": "NUMERIC",
            "is_required": True,
            "is_nullable": False,
        },
        {
            "column_name": "email",
            "expected_type": "TEXT",
            "is_required": True,
            "is_nullable": True,
        },
    ]

    result = validate_contract(
        df,
        contract,
    )

    assert result.status == "BREAKING"
    assert result.missing_required_count == 1
    assert result.unexpected_column_count == 1
    assert result.type_mismatch_count == 1
    assert result.violation_count == 3


def test_repository_boolean_values_are_supported():
    df = pd.DataFrame(
        {
            "customer_id": [
                1,
                2,
            ],
        }
    )

    contract = [
        {
            "column_name": "customer_id",
            "expected_type": "numeric",
            "is_required": 1,
            "is_nullable": 0,
        },
    ]

    result = validate_contract(
        df,
        contract,
    )

    assert result.status == "COMPATIBLE"


def test_duplicate_contract_column_is_rejected():
    df = pd.DataFrame(
        {
            "customer_id": [1],
        }
    )

    contract = [
        {
            "column_name": "customer_id",
            "expected_type": "NUMERIC",
        },
        {
            "column_name": "customer_id",
            "expected_type": "NUMERIC",
        },
    ]

    with pytest.raises(
        ValueError,
        match="Duplicate contract column",
    ):
        validate_contract(
            df,
            contract,
        )


def test_invalid_contract_type_is_rejected():
    df = pd.DataFrame(
        {
            "customer_id": [1],
        }
    )

    contract = [
        {
            "column_name": "customer_id",
            "expected_type": "MAGIC",
        },
    ]

    with pytest.raises(
        ValueError,
        match="Unsupported contract type",
    ):
        DataContractEngine().validate(
            df,
            contract,
        )


def test_result_to_dict_is_serializable_shape():
    df = pd.DataFrame(
        {
            "customer_id": [1],
        }
    )

    result = validate_contract(
        df,
        [
            {
                "column_name": "customer_id",
                "expected_type": "NUMERIC",
                "is_required": True,
                "is_nullable": False,
            }
        ],
    )

    payload = result.to_dict()

    assert payload[
        "status"
    ] == "COMPATIBLE"

    assert payload[
        "is_compatible"
    ] is True

    assert payload[
        "violations"
    ] == []