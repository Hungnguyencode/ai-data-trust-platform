from __future__ import annotations

from contextlib import nullcontext
from typing import Any

import pandas as pd
import pytest

import database.repositories.pipeline_run_repository as repository


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
        rowcount: int = 1,
    ) -> None:
        self.row = row
        self.scalar = scalar
        self.rowcount = rowcount

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
        self.results = list(results)
        self.calls: list[
            tuple[str, dict[str, Any] | None]
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


def test_create_pipeline_run_returns_existing_run(
    monkeypatch: pytest.MonkeyPatch,
):
    existing = {
        "pipeline_run_id": 7,
        "dag_id": "ai_data_trust_pipeline",
        "airflow_run_id": "manual__001",
        "source_path": "/app/data/test.csv",
        "run_status": "RUNNING",
        "attempt_count": 1,
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

    result = repository.create_pipeline_run(
        dag_id="ai_data_trust_pipeline",
        airflow_run_id="manual__001",
        source_path="/app/data/test.csv",
    )

    assert result == existing

    assert len(
        connection.calls
    ) == 1

    _, params = connection.calls[0]

    assert params == {
        "dag_id": "ai_data_trust_pipeline",
        "airflow_run_id": "manual__001",
    }


def test_create_pipeline_run_inserts_and_reloads(
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
        "pipeline_run_id": 42,
        "dag_id": "ai_data_trust_pipeline",
        "airflow_run_id": "manual__002",
        "source_path": "/app/data/test.csv",
        "run_status": "RUNNING",
        "attempt_count": 0,
    }

    loaded_ids: list[int] = []

    def fake_get_pipeline_run(
        pipeline_run_id: int,
    ):
        loaded_ids.append(
            pipeline_run_id
        )

        return created

    monkeypatch.setattr(
        repository,
        "get_pipeline_run",
        fake_get_pipeline_run,
    )

    result = repository.create_pipeline_run(
        dag_id="ai_data_trust_pipeline",
        airflow_run_id="manual__002",
        source_path="/app/data/test.csv",
    )

    assert result == created
    assert loaded_ids == [42]

    assert len(
        connection.calls
    ) == 2

    insert_sql, insert_params = (
        connection.calls[1]
    )

    assert (
        "INSERT INTO dbo.pipeline_runs"
        in insert_sql
    )

    assert insert_params == {
        "dag_id": "ai_data_trust_pipeline",
        "airflow_run_id": "manual__002",
        "source_path": "/app/data/test.csv",
    }


def test_create_pipeline_run_raises_when_reload_fails(
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
        "get_pipeline_run",
        lambda pipeline_run_id: None,
    )

    with pytest.raises(
        RuntimeError,
        match="could not be loaded",
    ):
        repository.create_pipeline_run(
            dag_id="ai_data_trust_pipeline",
            airflow_run_id="manual__003",
            source_path="/app/data/test.csv",
        )


def test_mark_pipeline_run_running_updates_attempt(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                rowcount=1
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

    repository.mark_pipeline_run_running(
        15
    )

    sql, params = connection.calls[0]

    assert (
        "attempt_count = attempt_count + 1"
        in sql
    )

    assert (
        "run_status = 'RUNNING'"
        in sql
    )

    assert params == {
        "pipeline_run_id": 15,
    }


def test_mark_pipeline_run_running_rejects_missing_run(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                rowcount=0
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
        match="Pipeline run not found: 404",
    ):
        repository.mark_pipeline_run_running(
            404
        )


def test_complete_pipeline_run_persists_summary(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                rowcount=1
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

    repository.complete_pipeline_run(
        pipeline_run_id=21,
        summary={
            "catalog_id": 3,
            "version_id": 8,
            "validation_status": "ACCEPTED",
            "governance_decision": "APPROVED",
            "trust_score": 96.5,
            "lifecycle_state": "VALIDATED",
        },
    )

    sql, params = connection.calls[0]

    assert (
        "run_status = 'SUCCESS'"
        in sql
    )

    assert params == {
        "pipeline_run_id": 21,
        "catalog_id": 3,
        "version_id": 8,
        "validation_status": "ACCEPTED",
        "governance_decision": "APPROVED",
        "trust_score": 96.5,
        "lifecycle_state": "VALIDATED",
    }


def test_fail_pipeline_run_persists_error(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                rowcount=1
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

    error = RuntimeError(
        "intentional failure"
    )

    repository.fail_pipeline_run(
        pipeline_run_id=22,
        error=error,
    )

    sql, params = connection.calls[0]

    assert (
        "run_status = 'FAILED'"
        in sql
    )

    assert params == {
        "pipeline_run_id": 22,
        "error_type": "RuntimeError",
        "error_message": (
            "intentional failure"
        ),
    }


def test_get_pipeline_run_returns_row(
    monkeypatch: pytest.MonkeyPatch,
):
    expected = {
        "pipeline_run_id": 31,
        "run_status": "SUCCESS",
        "attempt_count": 1,
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

    result = repository.get_pipeline_run(
        31
    )

    assert result == expected

    _, params = connection.calls[0]

    assert params == {
        "pipeline_run_id": 31,
    }


def test_get_pipeline_run_returns_none_when_missing(
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
        repository.get_pipeline_run(
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
def test_pipeline_run_history_clamps_limit(
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
                "pipeline_run_id": 1,
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
        captured["sql"] = str(query)
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
        repository.get_pipeline_run_history(
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