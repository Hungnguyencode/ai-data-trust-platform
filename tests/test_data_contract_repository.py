from __future__ import annotations

from contextlib import nullcontext
from typing import Any

import pytest

import database.repositories.data_contract_repository as repository


class FakeMappings:
    def __init__(
        self,
        *,
        first_row: dict[str, Any] | None = None,
        rows: list[dict[str, Any]] | None = None,
    ) -> None:
        self.first_row = first_row
        self.rows = rows or []

    def first(
        self,
    ) -> dict[str, Any] | None:
        return self.first_row

    def all(
        self,
    ) -> list[dict[str, Any]]:
        return self.rows


class FakeResult:
    def __init__(
        self,
        *,
        scalar: Any = None,
        first_row: dict[str, Any] | None = None,
        rows: list[dict[str, Any]] | None = None,
        rowcount: int = 1,
    ) -> None:
        self.scalar = scalar
        self.first_row = first_row
        self.rows = rows or []
        self.rowcount = rowcount

    def scalar_one(
        self,
    ) -> Any:
        return self.scalar

    def mappings(
        self,
    ) -> FakeMappings:
        return FakeMappings(
            first_row=self.first_row,
            rows=self.rows,
        )


class FakeConnection:
    def __init__(
        self,
        results: list[FakeResult],
    ) -> None:
        self.results = list(results)
        self.calls: list[
            tuple[str, Any]
        ] = []

    def execute(
        self,
        statement,
        params=None,
    ) -> FakeResult:
        self.calls.append(
            (
                str(statement),
                params,
            )
        )

        if not self.results:
            raise AssertionError(
                "Unexpected execute() call."
            )

        return self.results.pop(0)


class FakeEngine:
    def __init__(
        self,
        connection: FakeConnection,
    ) -> None:
        self.connection = connection

    def begin(
        self,
    ):
        return nullcontext(
            self.connection
        )

    def connect(
        self,
    ):
        return nullcontext(
            self.connection
        )


def sample_columns():
    return [
        {
            "column_name": "customer_id",
            "expected_type": "NUMERIC",
            "is_required": True,
            "is_nullable": False,
        },
        {
            "column_name": "name",
            "expected_type": "TEXT",
            "is_required": True,
            "is_nullable": True,
        },
    ]


def test_create_active_contract_versions_and_reloads(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                scalar=3
            ),
            FakeResult(
                rowcount=1
            ),
            FakeResult(
                scalar=42
            ),
            FakeResult(
                rowcount=2
            ),
        ]
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    created = {
        "contract_id": 42,
        "catalog_id": 7,
        "contract_version": 3,
        "contract_name": "customers",
        "enforcement_mode": "BLOCK",
        "is_active": True,
        "columns": [],
    }

    loaded_ids: list[int] = []

    def fake_get_data_contract(
        contract_id: int,
    ):
        loaded_ids.append(
            contract_id
        )
        return created

    monkeypatch.setattr(
        repository,
        "get_data_contract",
        fake_get_data_contract,
    )

    result = repository.create_data_contract(
        catalog_id=7,
        contract_name="customers",
        columns=sample_columns(),
    )

    assert result == created
    assert loaded_ids == [42]

    assert len(
        connection.calls
    ) == 4

    version_sql, _ = connection.calls[0]
    deactivate_sql, _ = connection.calls[1]
    insert_sql, insert_params = (
        connection.calls[2]
    )
    _, column_params = (
        connection.calls[3]
    )

    assert (
        "MAX(contract_version)"
        in version_sql
    )
    assert (
        "is_active = 0"
        in deactivate_sql
    )
    assert (
        "INSERT INTO dbo.data_contracts"
        in insert_sql
    )

    assert insert_params[
        "contract_version"
    ] == 3

    assert insert_params[
        "enforcement_mode"
    ] == "BLOCK"

    assert insert_params[
        "is_active"
    ] == 1

    assert len(
        column_params
    ) == 2

    assert column_params[0][
        "contract_id"
    ] == 42


def test_create_inactive_contract_does_not_deactivate(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                scalar=2
            ),
            FakeResult(
                scalar=50
            ),
            FakeResult(
                rowcount=2
            ),
        ]
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    monkeypatch.setattr(
        repository,
        "get_data_contract",
        lambda contract_id: {
            "contract_id": contract_id,
        },
    )

    repository.create_data_contract(
        catalog_id=8,
        contract_name="draft",
        columns=sample_columns(),
        enforcement_mode="WARN",
        activate=False,
    )

    assert len(
        connection.calls
    ) == 3

    insert_sql, insert_params = (
        connection.calls[1]
    )

    assert (
        "INSERT INTO dbo.data_contracts"
        in insert_sql
    )

    assert insert_params[
        "enforcement_mode"
    ] == "WARN"

    assert insert_params[
        "is_active"
    ] == 0


def test_invalid_enforcement_mode_is_rejected():
    with pytest.raises(
        ValueError,
        match="Unsupported enforcement mode",
    ):
        repository.create_data_contract(
            catalog_id=1,
            contract_name="test",
            columns=sample_columns(),
            enforcement_mode="DELETE",
        )


def test_empty_contract_columns_are_rejected():
    with pytest.raises(
        ValueError,
        match="at least one column",
    ):
        repository.create_data_contract(
            catalog_id=1,
            contract_name="test",
            columns=[],
        )


def test_duplicate_contract_columns_are_rejected():
    columns = sample_columns()

    columns.append(
        {
            "column_name": "customer_id",
            "expected_type": "NUMERIC",
        }
    )

    with pytest.raises(
        ValueError,
        match="Duplicate contract column",
    ):
        repository.create_data_contract(
            catalog_id=1,
            contract_name="test",
            columns=columns,
        )


def test_activate_missing_contract_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                first_row=None
            )
        ]
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    with pytest.raises(
        ValueError,
        match="Data contract not found",
    ):
        repository.activate_data_contract(
            404
        )


def test_activate_contract_switches_active_version(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                first_row={
                    "contract_id": 12,
                    "catalog_id": 5,
                }
            ),
            FakeResult(
                rowcount=1
            ),
            FakeResult(
                rowcount=1
            ),
        ]
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    monkeypatch.setattr(
        repository,
        "get_data_contract",
        lambda contract_id: {
            "contract_id": contract_id,
            "is_active": True,
        },
    )

    result = (
        repository.activate_data_contract(
            12
        )
    )

    assert result[
        "contract_id"
    ] == 12

    assert result[
        "is_active"
    ] is True

    deactivate_sql, deactivate_params = (
        connection.calls[1]
    )

    activate_sql, activate_params = (
        connection.calls[2]
    )

    assert (
        "is_active = 0"
        in deactivate_sql
    )

    assert deactivate_params == {
        "catalog_id": 5,
    }

    assert (
        "is_active = 1"
        in activate_sql
    )

    assert activate_params == {
        "contract_id": 12,
    }


def test_get_data_contract_loads_columns(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                first_row={
                    "contract_id": 3,
                    "catalog_id": 9,
                    "contract_version": 1,
                    "contract_name": "customers",
                    "enforcement_mode": "BLOCK",
                    "is_active": 1,
                    "created_at": None,
                    "updated_at": None,
                }
            ),
            FakeResult(
                rows=[
                    {
                        "contract_column_id": 10,
                        "contract_id": 3,
                        "column_name": "id",
                        "expected_type": "NUMERIC",
                        "is_required": 1,
                        "is_nullable": 0,
                        "created_at": None,
                    }
                ]
            ),
        ]
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    result = repository.get_data_contract(
        3
    )

    assert result is not None

    assert result[
        "is_active"
    ] is True

    assert result[
        "columns"
    ][0]["is_required"] is True

    assert result[
        "columns"
    ][0]["is_nullable"] is False


def test_get_active_contract_returns_none(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                first_row=None
            )
        ]
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    result = (
        repository.get_active_data_contract(
            9
        )
    )

    assert result is None


def test_save_breaking_validation_and_violations(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                first_row={
                    "contract_id": 4,
                }
            ),
            FakeResult(
                scalar=77
            ),
            FakeResult(
                rowcount=2
            ),
        ]
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    persisted = {
        "contract_validation_id": 77,
        "validation_status": "BREAKING",
    }

    monkeypatch.setattr(
        repository,
        "get_contract_validation",
        lambda validation_id: persisted,
    )

    validation = {
        "status": "BREAKING",
        "missing_required_count": 1,
        "unexpected_column_count": 1,
        "type_mismatch_count": 0,
        "nullability_violation_count": 0,
        "violation_count": 2,
        "violations": [
            {
                "violation_type": (
                    "MISSING_REQUIRED_COLUMN"
                ),
                "column_name": "email",
                "expected_value": "present",
                "actual_value": "missing",
                "message": (
                    "Required column is missing."
                ),
            },
            {
                "violation_type": (
                    "UNEXPECTED_COLUMN"
                ),
                "column_name": "legacy",
                "expected_value": "not defined",
                "actual_value": "TEXT",
                "message": (
                    "Unexpected column."
                ),
            },
        ],
    }

    result = (
        repository.save_contract_validation(
            contract_id=4,
            catalog_id=2,
            version_id=8,
            validation=validation,
        )
    )

    assert result == persisted

    assert len(
        connection.calls
    ) == 3

    relationship_sql, _ = (
        connection.calls[0]
    )

    assert (
        "INNER JOIN dbo.dataset_versions"
        in relationship_sql
    )

    insert_sql, insert_params = (
        connection.calls[1]
    )

    assert (
        "INSERT INTO dbo.contract_validation_history"
        in insert_sql
    )

    assert insert_params[
        "validation_status"
    ] == "BREAKING"

    _, violation_params = (
        connection.calls[2]
    )

    assert len(
        violation_params
    ) == 2

    assert violation_params[0][
        "contract_validation_id"
    ] == 77


def test_save_compatible_validation_without_violations(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                first_row={
                    "contract_id": 5,
                }
            ),
            FakeResult(
                scalar=88
            ),
        ]
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    monkeypatch.setattr(
        repository,
        "get_contract_validation",
        lambda validation_id: {
            "contract_validation_id": (
                validation_id
            ),
            "validation_status": (
                "COMPATIBLE"
            ),
        },
    )

    result = (
        repository.save_contract_validation(
            contract_id=5,
            catalog_id=2,
            version_id=9,
            validation={
                "status": "COMPATIBLE",
                "missing_required_count": 0,
                "unexpected_column_count": 0,
                "type_mismatch_count": 0,
                "nullability_violation_count": 0,
                "violation_count": 0,
                "violations": [],
            },
        )
    )

    assert result[
        "validation_status"
    ] == "COMPATIBLE"

    assert len(
        connection.calls
    ) == 2


def test_validation_count_mismatch_is_rejected():
    with pytest.raises(
        ValueError,
        match="violation_count does not match",
    ):
        repository.save_contract_validation(
            contract_id=1,
            catalog_id=1,
            version_id=1,
            validation={
                "status": "BREAKING",
                "missing_required_count": 1,
                "unexpected_column_count": 0,
                "type_mismatch_count": 0,
                "nullability_violation_count": 0,
                "violation_count": 2,
                "violations": [
                    {
                        "violation_type": (
                            "MISSING_REQUIRED_COLUMN"
                        ),
                        "column_name": "id",
                        "message": "Missing.",
                    }
                ],
            },
        )


def test_get_contract_validation_loads_violations(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                first_row={
                    "contract_validation_id": 20,
                    "contract_id": 4,
                    "catalog_id": 2,
                    "version_id": 8,
                    "validation_status": (
                        "BREAKING"
                    ),
                    "missing_required_count": 1,
                    "unexpected_column_count": 0,
                    "type_mismatch_count": 0,
                    "nullability_violation_count": 0,
                    "violation_count": 1,
                    "validated_at": None,
                }
            ),
            FakeResult(
                rows=[
                    {
                        "violation_id": 30,
                        "contract_validation_id": 20,
                        "column_name": "email",
                        "violation_type": (
                            "MISSING_REQUIRED_COLUMN"
                        ),
                        "expected_value": "present",
                        "actual_value": "missing",
                        "message": "Missing email.",
                        "created_at": None,
                    }
                ]
            ),
        ]
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    result = (
        repository.get_contract_validation(
            20
        )
    )

    assert result is not None

    assert result[
        "contract_validation_id"
    ] == 20

    assert len(
        result["violations"]
    ) == 1

    assert result[
        "violations"
    ][0]["violation_id"] == 30