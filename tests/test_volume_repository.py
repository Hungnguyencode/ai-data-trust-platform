from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

import database.repositories.volume_repository as volume_repository


class FakeResult:
    def __init__(
        self,
        row: dict[str, Any] | None = None,
        *,
        scalar_value: Any = None,
    ) -> None:
        self.row = row
        self.scalar_value = scalar_value

    def mappings(self) -> FakeResult:
        return self

    def first(
        self,
    ) -> dict[str, Any] | None:
        return self.row

    def scalar_one(
        self,
    ) -> Any:
        if self.scalar_value is None:
            raise AssertionError(
                "scalar_one() called without "
                "a scalar value"
            )

        return self.scalar_value


class FakeConnection:
    def __init__(
        self,
        *,
        select_rows: list[
            dict[str, Any] | None
        ]
        | None = None,
        scalar_values: list[Any]
        | None = None,
    ) -> None:
        self.select_rows = list(
            select_rows or []
        )
        self.scalar_values = list(
            scalar_values or []
        )
        self.calls: list[
            tuple[str, dict[str, Any] | None]
        ] = []

    def __enter__(
        self,
    ) -> FakeConnection:
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc: Any,
        traceback: Any,
    ) -> None:
        return None

    def execute(
        self,
        statement: Any,
        params: dict[str, Any] | None = None,
    ) -> FakeResult:
        sql = str(statement)

        self.calls.append(
            (
                sql,
                params,
            )
        )

        if "SELECT TOP 1" in sql:
            row = (
                self.select_rows.pop(0)
                if self.select_rows
                else None
            )

            return FakeResult(
                row
            )

        if (
            "OUTPUT INSERTED.volume_check_id"
            in sql
        ):
            scalar_value = (
                self.scalar_values.pop(0)
                if self.scalar_values
                else None
            )

            return FakeResult(
                scalar_value=scalar_value
            )

        return FakeResult()


class FakeEngine:
    def __init__(
        self,
        connection: FakeConnection,
    ) -> None:
        self.connection = connection

    def connect(
        self,
    ) -> FakeConnection:
        return self.connection

    def begin(
        self,
    ) -> FakeConnection:
        return self.connection


def test_get_volume_policy_rejects_invalid_catalog_before_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_get_engine() -> None:
        raise AssertionError(
            "database access must not occur"
        )

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        fail_get_engine,
    )

    with pytest.raises(
        ValueError,
        match="catalog_id",
    ):
        volume_repository.get_volume_policy(
            0
        )


def test_get_volume_policy_returns_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(
        select_rows=[
            {
                "volume_policy_id": 11,
                "catalog_id": 3,
                "drop_threshold_pct": 25.0,
                "spike_threshold_pct": 50.0,
                "is_enabled": 1,
                "created_at": None,
                "updated_at": None,
            }
        ]
    )

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    result = (
        volume_repository
        .get_volume_policy(
            3
        )
    )

    assert result is not None
    assert result[
        "volume_policy_id"
    ] == 11
    assert result[
        "catalog_id"
    ] == 3
    assert result[
        "is_enabled"
    ] is True

    assert len(
        connection.calls
    ) == 1

    sql, params = (
        connection.calls[0]
    )

    assert (
        "dataset_volume_policies"
        in sql
    )

    assert params == {
        "catalog_id": 3,
    }


def test_get_volume_policy_returns_none_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(
        select_rows=[
            None
        ]
    )

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    result = (
        volume_repository
        .get_volume_policy(
            99
        )
    )

    assert result is None


@pytest.mark.parametrize(
    (
        "drop_threshold_pct",
        "spike_threshold_pct",
    ),
    [
        (0, 50),
        (-1, 50),
        (101, 50),
        (25, 0),
        (25, -1),
        (float("nan"), 50),
        (25, float("inf")),
    ],
)
def test_upsert_volume_policy_rejects_invalid_thresholds_before_database(
    monkeypatch: pytest.MonkeyPatch,
    drop_threshold_pct: float,
    spike_threshold_pct: float,
) -> None:
    def fail_get_engine() -> None:
        raise AssertionError(
            "database access must not occur"
        )

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        fail_get_engine,
    )

    with pytest.raises(
        ValueError
    ):
        (
            volume_repository
            .upsert_volume_policy(
                catalog_id=1,
                drop_threshold_pct=(
                    drop_threshold_pct
                ),
                spike_threshold_pct=(
                    spike_threshold_pct
                ),
            )
        )


def test_upsert_volume_policy_inserts_new_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(
        select_rows=[
            None
        ]
    )

    engine = FakeEngine(
        connection
    )

    expected_policy = {
        "volume_policy_id": 12,
        "catalog_id": 4,
        "drop_threshold_pct": 20.0,
        "spike_threshold_pct": 60.0,
        "is_enabled": True,
        "created_at": None,
        "updated_at": None,
    }

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        lambda: engine,
    )

    monkeypatch.setattr(
        volume_repository,
        "get_volume_policy",
        lambda catalog_id: (
            expected_policy
            if catalog_id == 4
            else None
        ),
    )

    result = (
        volume_repository
        .upsert_volume_policy(
            catalog_id=4,
            drop_threshold_pct=20,
            spike_threshold_pct=60,
            is_enabled=True,
        )
    )

    assert result == expected_policy

    assert len(
        connection.calls
    ) == 2

    assert (
        "SELECT TOP 1"
        in connection.calls[0][0]
    )

    assert (
        "INSERT INTO"
        in connection.calls[1][0]
    )

    insert_params = (
        connection.calls[1][1]
    )

    assert insert_params is not None

    assert insert_params[
        "catalog_id"
    ] == 4

    assert insert_params[
        "drop_threshold_pct"
    ] == 20.0

    assert insert_params[
        "spike_threshold_pct"
    ] == 60.0

    assert insert_params[
        "is_enabled"
    ] == 1


def test_upsert_volume_policy_updates_existing_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(
        select_rows=[
            {
                "volume_policy_id": 13,
            }
        ]
    )

    expected_policy = {
        "volume_policy_id": 13,
        "catalog_id": 5,
        "drop_threshold_pct": 30.0,
        "spike_threshold_pct": 80.0,
        "is_enabled": False,
        "created_at": None,
        "updated_at": None,
    }

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    monkeypatch.setattr(
        volume_repository,
        "get_volume_policy",
        lambda catalog_id: (
            expected_policy
            if catalog_id == 5
            else None
        ),
    )

    result = (
        volume_repository
        .upsert_volume_policy(
            catalog_id=5,
            drop_threshold_pct=30,
            spike_threshold_pct=80,
            is_enabled=False,
        )
    )

    assert result == expected_policy

    assert len(
        connection.calls
    ) == 2

    assert (
        "UPDATE dbo.dataset_volume_policies"
        in connection.calls[1][0]
    )

    update_params = (
        connection.calls[1][1]
    )

    assert update_params is not None
    assert update_params[
        "is_enabled"
    ] == 0


def test_get_enabled_volume_policies_returns_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection()

    expected = pd.DataFrame(
        [
            {
                "volume_policy_id": 1,
                "catalog_id": 2,
                "dataset_key": "customers",
                "display_name": "Customers",
                "drop_threshold_pct": 25.0,
                "spike_threshold_pct": 50.0,
                "is_enabled": True,
            }
        ]
    )

    captured: dict[
        str,
        Any,
    ] = {}

    def fake_read_sql_query(
        query: Any,
        sql_connection: Any,
        **kwargs: Any,
    ) -> pd.DataFrame:
        captured["sql"] = str(
            query
        )
        captured[
            "connection"
        ] = sql_connection
        captured[
            "kwargs"
        ] = kwargs

        return expected

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    monkeypatch.setattr(
        volume_repository.pd,
        "read_sql_query",
        fake_read_sql_query,
    )

    result = (
        volume_repository
        .get_enabled_volume_policies()
    )

    pd.testing.assert_frame_equal(
        result,
        expected,
    )

    assert (
        "WHERE p.is_enabled = 1"
        in captured["sql"]
    )


@pytest.mark.parametrize(
    (
        "requested_limit",
        "expected_limit",
    ),
    [
        (0, 1),
        (2, 2),
        (5000, 1000),
    ],
)
def test_get_recent_ingestions_clamps_limit(
    monkeypatch: pytest.MonkeyPatch,
    requested_limit: int,
    expected_limit: int,
) -> None:
    connection = FakeConnection()

    captured: dict[
        str,
        Any,
    ] = {}

    expected = pd.DataFrame()

    def fake_read_sql_query(
        query: Any,
        sql_connection: Any,
        **kwargs: Any,
    ) -> pd.DataFrame:
        captured["sql"] = str(
            query
        )
        captured[
            "connection"
        ] = sql_connection
        captured[
            "kwargs"
        ] = kwargs

        return expected

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    monkeypatch.setattr(
        volume_repository.pd,
        "read_sql_query",
        fake_read_sql_query,
    )

    result = (
        volume_repository
        .get_recent_ingestions_for_catalog(
            7,
            limit=requested_limit,
        )
    )

    pd.testing.assert_frame_equal(
        result,
        expected,
    )

    assert (
        f"SELECT TOP {expected_limit}"
        in captured["sql"]
    )

    assert captured[
        "kwargs"
    ][
        "params"
    ] == {
        "catalog_id": 7,
    }


def test_get_recent_ingestions_rejects_invalid_catalog_before_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_get_engine() -> None:
        raise AssertionError(
            "database access must not occur"
        )

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        fail_get_engine,
    )

    with pytest.raises(
        ValueError,
        match="catalog_id",
    ):
        (
            volume_repository
            .get_recent_ingestions_for_catalog(
                -1
            )
        )


def test_create_volume_check_rejects_invalid_status_before_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_get_engine() -> None:
        raise AssertionError(
            "database access must not occur"
        )

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        fail_get_engine,
    )

    with pytest.raises(
        ValueError,
        match="volume_status",
    ):
        volume_repository.create_volume_check(
            volume_policy_id=1,
            catalog_id=2,
            ingestion_event_id=3,
            version_id=4,
            current_row_count=100,
            drop_threshold_pct=25,
            spike_threshold_pct=50,
            volume_status="INVALID",
        )


def test_create_volume_check_rejects_negative_current_rows_before_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_get_engine() -> None:
        raise AssertionError(
            "database access must not occur"
        )

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        fail_get_engine,
    )

    with pytest.raises(
        ValueError,
        match="current_row_count",
    ):
        volume_repository.create_volume_check(
            volume_policy_id=1,
            catalog_id=2,
            ingestion_event_id=3,
            version_id=4,
            current_row_count=-1,
            drop_threshold_pct=25,
            spike_threshold_pct=50,
            volume_status="NORMAL",
        )


def test_create_volume_check_reuses_existing_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(
        select_rows=[
            {
                "volume_check_id": 40,
            }
        ]
    )

    expected = {
        "volume_check_id": 40,
        "volume_status": "NORMAL",
    }

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    monkeypatch.setattr(
        volume_repository,
        "get_volume_check",
        lambda volume_check_id: (
            expected
            if volume_check_id == 40
            else None
        ),
    )

    result = (
        volume_repository
        .create_volume_check(
            volume_policy_id=10,
            catalog_id=2,
            ingestion_event_id=30,
            version_id=3,
            current_row_count=100,
            drop_threshold_pct=25,
            spike_threshold_pct=50,
            volume_status="NORMAL",
        )
    )

    assert result == expected

    assert len(
        connection.calls
    ) == 1

    sql, params = (
        connection.calls[0]
    )

    assert (
        "dataset_volume_history"
        in sql
    )

    assert params == {
        "volume_policy_id": 10,
        "ingestion_event_id": 30,
    }


def test_create_volume_check_inserts_new_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(
        select_rows=[
            None
        ],
        scalar_values=[
            41
        ],
    )

    expected = {
        "volume_check_id": 41,
        "volume_status": "DROP",
    }

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    monkeypatch.setattr(
        volume_repository,
        "get_volume_check",
        lambda volume_check_id: (
            expected
            if volume_check_id == 41
            else None
        ),
    )

    result = (
        volume_repository
        .create_volume_check(
            volume_policy_id=10,
            catalog_id=2,
            ingestion_event_id=31,
            version_id=4,
            baseline_ingestion_event_id=30,
            baseline_version_id=3,
            baseline_row_count=200,
            current_row_count=100,
            drop_threshold_pct=25,
            spike_threshold_pct=50,
            row_change_pct=-50,
            volume_status="drop",
        )
    )

    assert result == expected

    assert len(
        connection.calls
    ) == 2

    assert (
        "INSERT INTO dbo.dataset_volume_history"
        in connection.calls[1][0]
    )

    insert_params = (
        connection.calls[1][1]
    )

    assert insert_params is not None

    assert insert_params[
        "catalog_id"
    ] == 2

    assert insert_params[
        "baseline_row_count"
    ] == 200

    assert insert_params[
        "current_row_count"
    ] == 100

    assert insert_params[
        "row_change_pct"
    ] == -50.0

    assert insert_params[
        "volume_status"
    ] == "DROP"


def test_get_volume_check_returns_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(
        select_rows=[
            {
                "volume_check_id": 55,
                "volume_policy_id": 10,
                "catalog_id": 2,
                "ingestion_event_id": 31,
                "version_id": 4,
                "volume_status": "NORMAL",
            }
        ]
    )

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    result = (
        volume_repository
        .get_volume_check(
            55
        )
    )

    assert result is not None

    assert result[
        "volume_check_id"
    ] == 55

    assert result[
        "volume_status"
    ] == "NORMAL"


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
def test_get_volume_history_clamps_limit(
    monkeypatch: pytest.MonkeyPatch,
    requested_limit: int,
    expected_limit: int,
) -> None:
    connection = FakeConnection()

    expected = pd.DataFrame()

    captured: dict[
        str,
        Any,
    ] = {}

    def fake_read_sql_query(
        query: Any,
        sql_connection: Any,
        **kwargs: Any,
    ) -> pd.DataFrame:
        captured["sql"] = str(
            query
        )
        captured[
            "connection"
        ] = sql_connection
        captured[
            "kwargs"
        ] = kwargs

        return expected

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        lambda: FakeEngine(
            connection
        ),
    )

    monkeypatch.setattr(
        volume_repository.pd,
        "read_sql_query",
        fake_read_sql_query,
    )

    result = (
        volume_repository
        .get_volume_history(
            7,
            limit=requested_limit,
        )
    )

    pd.testing.assert_frame_equal(
        result,
        expected,
    )

    assert (
        f"SELECT TOP {expected_limit}"
        in captured["sql"]
    )

    assert captured[
        "kwargs"
    ][
        "params"
    ] == {
        "catalog_id": 7,
    }


def test_get_volume_history_rejects_invalid_catalog_before_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_get_engine() -> None:
        raise AssertionError(
            "database access must not occur"
        )

    monkeypatch.setattr(
        volume_repository,
        "get_engine",
        fail_get_engine,
    )

    with pytest.raises(
        ValueError,
        match="catalog_id",
    ):
        volume_repository.get_volume_history(
            0
        )