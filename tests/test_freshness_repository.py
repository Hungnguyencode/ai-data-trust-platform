from __future__ import annotations

from contextlib import nullcontext
from datetime import UTC, datetime
from typing import Any

import pandas as pd
import pytest

import database.repositories.freshness_repository as repository


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


def test_get_freshness_policy_returns_policy(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                row={
                    "freshness_policy_id": 10,
                    "catalog_id": 1,
                    "max_age_minutes": 1440,
                    "is_enabled": 1,
                }
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
        repository.get_freshness_policy(
            1
        )
    )

    assert result is not None
    assert (
        result["freshness_policy_id"]
        == 10
    )
    assert result["catalog_id"] == 1
    assert (
        result["max_age_minutes"]
        == 1440
    )
    assert result["is_enabled"] is True

    _, params = connection.calls[0]

    assert params == {
        "catalog_id": 1,
    }


def test_get_freshness_policy_returns_none(
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
        repository.get_freshness_policy(
            1
        )
        is None
    )


def test_get_freshness_policy_rejects_invalid_catalog_id():
    with pytest.raises(
        ValueError,
        match="catalog_id",
    ):
        repository.get_freshness_policy(
            0
        )


def test_upsert_freshness_policy_inserts_new_policy(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                row=None
            ),
            FakeResult(),
        ]
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    saved_policy = {
        "freshness_policy_id": 11,
        "catalog_id": 1,
        "max_age_minutes": 60,
        "is_enabled": True,
    }

    monkeypatch.setattr(
        repository,
        "get_freshness_policy",
        lambda catalog_id: (
            saved_policy
        ),
    )

    result = (
        repository.upsert_freshness_policy(
            catalog_id=1,
            max_age_minutes=60,
            is_enabled=True,
        )
    )

    assert result == saved_policy
    assert len(connection.calls) == 2

    find_sql, find_params = (
        connection.calls[0]
    )

    assert "UPDLOCK" in find_sql
    assert find_params == {
        "catalog_id": 1,
    }

    insert_sql, insert_params = (
        connection.calls[1]
    )

    assert (
        "INSERT INTO "
        "dbo.dataset_freshness_policies"
        in insert_sql
    )

    assert insert_params == {
        "catalog_id": 1,
        "max_age_minutes": 60,
        "is_enabled": 1,
    }


def test_upsert_freshness_policy_updates_existing_policy(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                row={
                    "freshness_policy_id": 11,
                }
            ),
            FakeResult(),
        ]
    )

    monkeypatch.setattr(
        repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    saved_policy = {
        "freshness_policy_id": 11,
        "catalog_id": 1,
        "max_age_minutes": 120,
        "is_enabled": False,
    }

    monkeypatch.setattr(
        repository,
        "get_freshness_policy",
        lambda catalog_id: (
            saved_policy
        ),
    )

    result = (
        repository.upsert_freshness_policy(
            catalog_id=1,
            max_age_minutes=120,
            is_enabled=False,
        )
    )

    assert result == saved_policy
    assert len(connection.calls) == 2

    update_sql, update_params = (
        connection.calls[1]
    )

    assert (
        "UPDATE "
        "dbo.dataset_freshness_policies"
        in update_sql
    )

    assert update_params == {
        "catalog_id": 1,
        "max_age_minutes": 120,
        "is_enabled": 0,
    }


def test_upsert_freshness_policy_rejects_invalid_max_age():
    with pytest.raises(
        ValueError,
        match="max_age_minutes",
    ):
        repository.upsert_freshness_policy(
            catalog_id=1,
            max_age_minutes=0,
        )


def test_upsert_freshness_policy_raises_when_reload_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                row=None
            ),
            FakeResult(),
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
        "get_freshness_policy",
        lambda catalog_id: None,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "Freshness policy was saved"
        ),
    ):
        repository.upsert_freshness_policy(
            catalog_id=1,
            max_age_minutes=60,
        )


def test_get_enabled_freshness_policies(
    monkeypatch: pytest.MonkeyPatch,
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
                "freshness_policy_id": 1,
                "catalog_id": 1,
                "dataset_key": (
                    "sample_customers.csv"
                ),
                "display_name": (
                    "sample_customers.csv"
                ),
                "max_age_minutes": 1440,
                "is_enabled": True,
            }
        ]
    )

    captured = {}

    def fake_read_sql_query(
        query,
        sql_connection,
        params=None,
    ):
        captured["query"] = str(query)
        captured[
            "connection"
        ] = sql_connection
        captured["params"] = params

        return expected

    monkeypatch.setattr(
        repository.pd,
        "read_sql_query",
        fake_read_sql_query,
    )

    result = (
        repository
        .get_enabled_freshness_policies()
    )

    pd.testing.assert_frame_equal(
        result,
        expected,
    )

    assert (
        "WHERE p.is_enabled = 1"
        in captured["query"]
    )
    assert (
        captured["connection"]
        is connection
    )


def test_get_latest_ingestion_for_catalog_returns_row(
    monkeypatch: pytest.MonkeyPatch,
):
    ingested_at = datetime(
        2026,
        9,
        15,
        6,
        35,
        tzinfo=UTC,
    )

    row = {
        "ingestion_event_id": 20005,
        "ingestion_id": "abc",
        "catalog_id": 1,
        "version_id": 3,
        "version_number": 3,
        "source_type": "FILE",
        "ingested_at": ingested_at,
        "raw_path": "/app/data/raw/file.csv",
    }

    connection = FakeConnection(
        [
            FakeResult(
                row=row
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
        repository
        .get_latest_ingestion_for_catalog(
            1
        )
    )

    assert result == row

    sql, params = connection.calls[0]

    assert (
        "ORDER BY"
        in sql
    )
    assert (
        "ih.ingested_at DESC"
        in sql
    )
    assert params == {
        "catalog_id": 1,
    }


def test_get_latest_ingestion_for_catalog_returns_none(
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
        repository
        .get_latest_ingestion_for_catalog(
            1
        )
        is None
    )


def test_create_freshness_check_inserts_and_reloads(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                scalar=501
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

    checked_at = datetime(
        2026,
        9,
        15,
        12,
        0,
    )

    latest_ingested_at = datetime(
        2026,
        9,
        15,
        10,
        0,
        tzinfo=UTC,
    )

    created = {
        "freshness_check_id": 501,
        "catalog_id": 1,
        "ingestion_event_id": 20,
        "version_id": 3,
        "max_age_minutes": 60,
        "age_minutes": 120,
        "freshness_status": "STALE",
    }

    loaded_ids = []

    def fake_get_freshness_check(
        freshness_check_id: int,
    ):
        loaded_ids.append(
            freshness_check_id
        )
        return created

    monkeypatch.setattr(
        repository,
        "get_freshness_check",
        fake_get_freshness_check,
    )

    result = (
        repository.create_freshness_check(
            catalog_id=1,
            ingestion_event_id=20,
            version_id=3,
            max_age_minutes=60,
            age_minutes=120,
            freshness_status=" stale ",
            latest_ingested_at=(
                latest_ingested_at
            ),
            checked_at=checked_at,
        )
    )

    assert result == created
    assert loaded_ids == [501]

    _, params = connection.calls[0]

    assert params == {
        "catalog_id": 1,
        "ingestion_event_id": 20,
        "version_id": 3,
        "max_age_minutes": 60,
        "age_minutes": 120,
        "freshness_status": "STALE",
        "latest_ingested_at": (
            latest_ingested_at
        ),
        "checked_at": checked_at,
    }


def test_create_freshness_check_allows_no_data(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                scalar=502
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

    created = {
        "freshness_check_id": 502,
        "catalog_id": 1,
        "ingestion_event_id": None,
        "version_id": None,
        "max_age_minutes": 60,
        "age_minutes": None,
        "freshness_status": "NO_DATA",
    }

    monkeypatch.setattr(
        repository,
        "get_freshness_check",
        lambda freshness_check_id: (
            created
        ),
    )

    result = (
        repository.create_freshness_check(
            catalog_id=1,
            max_age_minutes=60,
            freshness_status="NO_DATA",
        )
    )

    assert result == created

    _, params = connection.calls[0]

    assert params[
        "age_minutes"
    ] is None
    assert params[
        "ingestion_event_id"
    ] is None
    assert params[
        "version_id"
    ] is None


def test_create_freshness_check_rejects_invalid_status():
    with pytest.raises(
        ValueError,
        match=(
            "Unsupported freshness status"
        ),
    ):
        repository.create_freshness_check(
            catalog_id=1,
            max_age_minutes=60,
            freshness_status="BROKEN",
        )


def test_create_freshness_check_rejects_negative_age():
    with pytest.raises(
        ValueError,
        match="age_minutes",
    ):
        repository.create_freshness_check(
            catalog_id=1,
            max_age_minutes=60,
            freshness_status="STALE",
            age_minutes=-1,
        )


def test_create_freshness_check_requires_age_for_fresh_or_stale():
    with pytest.raises(
        ValueError,
        match=(
            "age_minutes is required"
        ),
    ):
        repository.create_freshness_check(
            catalog_id=1,
            max_age_minutes=60,
            freshness_status="FRESH",
            age_minutes=None,
        )


def test_create_freshness_check_raises_when_reload_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    connection = FakeConnection(
        [
            FakeResult(
                scalar=503
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

    monkeypatch.setattr(
        repository,
        "get_freshness_check",
        lambda freshness_check_id: None,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "Freshness check was created"
        ),
    ):
        repository.create_freshness_check(
            catalog_id=1,
            max_age_minutes=60,
            freshness_status="FRESH",
            age_minutes=10,
        )


def test_get_freshness_check_returns_row(
    monkeypatch: pytest.MonkeyPatch,
):
    row = {
        "freshness_check_id": 501,
        "catalog_id": 1,
        "freshness_status": "FRESH",
    }

    connection = FakeConnection(
        [
            FakeResult(
                row=row
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
        repository.get_freshness_check(
            501
        )
    )

    assert result == row

    _, params = connection.calls[0]

    assert params == {
        "freshness_check_id": 501,
    }


def test_get_freshness_check_returns_none(
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
        repository.get_freshness_check(
            501
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
def test_get_freshness_history_clamps_limit(
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
                "freshness_check_id": 1,
                "catalog_id": 1,
            }
        ]
    )

    captured = {}

    def fake_read_sql_query(
        query,
        sql_connection,
        params=None,
    ):
        captured["query"] = str(query)
        captured["params"] = params

        return expected

    monkeypatch.setattr(
        repository.pd,
        "read_sql_query",
        fake_read_sql_query,
    )

    result = (
        repository.get_freshness_history(
            1,
            limit=requested_limit,
        )
    )

    pd.testing.assert_frame_equal(
        result,
        expected,
    )

    assert (
        f"SELECT TOP {expected_limit}"
        in captured["query"]
    )

    assert captured["params"] == {
        "catalog_id": 1,
    }