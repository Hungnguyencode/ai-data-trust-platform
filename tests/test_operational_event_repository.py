from __future__ import annotations

import json
from contextlib import nullcontext
from typing import Any

import pandas as pd
import pytest

import database.repositories.operational_event_repository as repository


class FakeMappings:
    def __init__(
        self,
        row: dict[str, Any] | None,
    ) -> None:
        self.row = row

    def first(
        self,
    ) -> dict[str, Any] | None:
        return self.row


class FakeResult:
    def __init__(
        self,
        *,
        row: dict[str, Any] | None = None,
        scalar: Any = None,
    ) -> None:
        self.row = row
        self.scalar = scalar

    def mappings(
        self,
    ) -> FakeMappings:
        return FakeMappings(
            self.row
        )

    def scalar_one(
        self,
    ) -> Any:
        return self.scalar


class FakeConnection:
    def __init__(
        self,
        results: list[FakeResult],
    ) -> None:
        self.results = list(
            results
        )
        self.calls: list[
            tuple[
                str,
                dict[str, Any] | None,
            ]
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

        return self.results.pop(
            0
        )


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


def test_create_operational_event_returns_existing_event(
    monkeypatch: pytest.MonkeyPatch,
):
    existing = {
        "operational_event_id": 7,
        "event_key": (
            "pipeline-run:10:failed"
        ),
        "event_type": "PIPELINE_FAILED",
        "severity": "CRITICAL",
        "event_source": "AIRFLOW",
    }

    connection = FakeConnection(
        [
            FakeResult(
                row=existing
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
        repository.create_operational_event(
            event_key=(
                "pipeline-run:10:failed"
            ),
            event_type="PIPELINE_FAILED",
            severity="CRITICAL",
            event_source="AIRFLOW",
            message="Pipeline failed.",
        )
    )

    assert result == existing

    assert len(
        connection.calls
    ) == 1

    _, params = connection.calls[0]

    assert params == {
        "event_key": (
            "pipeline-run:10:failed"
        ),
    }


def test_create_operational_event_inserts_and_reloads(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                row=None
            ),
            FakeResult(
                scalar=42
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
        "operational_event_id": 42,
        "event_key": (
            "contract-validation:8:breaking"
        ),
        "event_type": (
            "DATA_CONTRACT_BREAKING"
        ),
        "severity": "ERROR",
        "event_source": (
            "DATASET_WORKFLOW"
        ),
    }

    loaded_ids: list[int] = []

    def fake_get_operational_event(
        operational_event_id: int,
    ):
        loaded_ids.append(
            operational_event_id
        )

        return created

    monkeypatch.setattr(
        repository,
        "get_operational_event",
        fake_get_operational_event,
    )

    result = (
        repository.create_operational_event(
            event_key=(
                "contract-validation:8:breaking"
            ),
            event_type=(
                "data_contract_breaking"
            ),
            severity="error",
            event_source=(
                "dataset_workflow"
            ),
            event_stage=(
                "data_contract_gate"
            ),
            catalog_id=1,
            version_id=2,
            reference_id=8,
            message=(
                "Dataset violates contract."
            ),
            detail={
                "violation_count": 1,
                "enforcement_mode": "BLOCK",
            },
        )
    )

    assert result == created
    assert loaded_ids == [42]

    assert len(
        connection.calls
    ) == 2

    insert_sql, params = (
        connection.calls[1]
    )

    assert (
        "INSERT INTO dbo.operational_events"
        in insert_sql
    )

    assert params[
        "event_type"
    ] == "DATA_CONTRACT_BREAKING"

    assert params[
        "severity"
    ] == "ERROR"

    assert params[
        "event_source"
    ] == "DATASET_WORKFLOW"

    assert params[
        "event_stage"
    ] == "DATA_CONTRACT_GATE"

    assert params[
        "catalog_id"
    ] == 1

    assert params[
        "version_id"
    ] == 2

    assert params[
        "reference_id"
    ] == 8

    assert json.loads(
        params["detail_json"]
    ) == {
        "enforcement_mode": "BLOCK",
        "violation_count": 1,
    }


def test_create_operational_event_raises_when_reload_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                row=None
            ),
            FakeResult(
                scalar=99
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
        "get_operational_event",
        lambda operational_event_id: None,
    )

    with pytest.raises(
        RuntimeError,
        match="could not be loaded",
    ):
        repository.create_operational_event(
            event_key="test:99",
            event_type="TEST_EVENT",
            severity="INFO",
            event_source="TEST",
            message="Test event.",
        )


def test_invalid_severity_is_rejected():
    with pytest.raises(
        ValueError,
        match="Unsupported operational event severity",
    ):
        repository.create_operational_event(
            event_key="test:invalid",
            event_type="TEST_EVENT",
            severity="HIGH",
            event_source="TEST",
            message="Invalid severity.",
        )


def test_get_operational_event_returns_row(
    monkeypatch: pytest.MonkeyPatch,
):
    expected = {
        "operational_event_id": 31,
        "event_key": "validation:31:rejected",
        "event_type": "VALIDATION_REJECTED",
        "severity": "ERROR",
    }

    connection = FakeConnection(
        [
            FakeResult(
                row=expected
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
        repository.get_operational_event(
            31
        )
    )

    assert result == expected

    _, params = connection.calls[0]

    assert params == {
        "operational_event_id": 31,
    }


def test_get_operational_event_returns_none_when_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                row=None
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

    assert (
        repository.get_operational_event(
            999
        )
        is None
    )


@pytest.mark.parametrize(
    (
        "requested_limit",
        "expected_limit",
    ),
    [
        (0, 1),
        (25, 25),
        (5000, 1000),
    ],
)
def test_operational_event_history_clamps_limit(
    monkeypatch: pytest.MonkeyPatch,
    requested_limit: int,
    expected_limit: int,
):
    connection = FakeConnection(
        []
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    expected = pd.DataFrame(
        [
            {
                "operational_event_id": 1,
            }
        ]
    )

    captured: dict[
        str,
        Any,
    ] = {}

    def fake_read_sql_query(
        query,
        connection_arg,
    ):
        captured["sql"] = str(
            query
        )
        captured[
            "connection"
        ] = connection_arg

        return expected

    monkeypatch.setattr(
        repository.pd,
        "read_sql_query",
        fake_read_sql_query,
    )

    result = (
        repository.get_operational_event_history(
            requested_limit
        )
    )

    assert result.equals(
        expected
    )

    assert (
        f"SELECT TOP {expected_limit}"
        in captured["sql"]
    )

    assert (
        captured["connection"]
        is connection
    )