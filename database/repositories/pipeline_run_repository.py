from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
from sqlalchemy import text

from database.db import get_engine


def create_pipeline_run(
    *,
    dag_id: str,
    airflow_run_id: str,
    source_path: str,
) -> dict[str, Any]:
    existing_query = text(
        """
        SELECT TOP 1
            pipeline_run_id,
            dag_id,
            airflow_run_id,
            source_path,
            run_status,
            attempt_count,
            catalog_id,
            version_id,
            validation_status,
            governance_decision,
            trust_score,
            lifecycle_state,
            started_at,
            finished_at,
            duration_ms,
            error_type,
            error_message,
            created_at,
            updated_at
        FROM dbo.pipeline_runs
        WHERE dag_id = :dag_id
          AND airflow_run_id = :airflow_run_id;
        """
    )

    insert_query = text(
        """
        INSERT INTO dbo.pipeline_runs (
            dag_id,
            airflow_run_id,
            source_path,
            run_status
        )
        OUTPUT
            INSERTED.pipeline_run_id
        VALUES (
            :dag_id,
            :airflow_run_id,
            :source_path,
            'RUNNING'
        );
        """
    )

    params = {
        "dag_id": str(dag_id),
        "airflow_run_id": str(
            airflow_run_id
        ),
        "source_path": str(source_path),
    }

    engine = get_engine()

    with engine.begin() as connection:
        existing = connection.execute(
            existing_query,
            {
                "dag_id": params["dag_id"],
                "airflow_run_id": params[
                    "airflow_run_id"
                ],
            },
        ).mappings().first()

        if existing is not None:
            return dict(existing)

        pipeline_run_id = connection.execute(
            insert_query,
            params,
        ).scalar_one()

    created_run = get_pipeline_run(
        int(pipeline_run_id)
    )

    if created_run is None:
        raise RuntimeError(
            "Pipeline run was created but "
            "could not be loaded."
        )

    return created_run


def mark_pipeline_run_running(
    pipeline_run_id: int,
) -> None:
    query = text(
        """
        UPDATE dbo.pipeline_runs
        SET
            run_status = 'RUNNING',
            attempt_count = attempt_count + 1,
            finished_at = NULL,
            duration_ms = NULL,
            error_type = NULL,
            error_message = NULL,
            updated_at = SYSUTCDATETIME()
        WHERE pipeline_run_id =
            :pipeline_run_id;
        """
    )

    engine = get_engine()

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "pipeline_run_id": int(
                    pipeline_run_id
                ),
            },
        )

        if result.rowcount != 1:
            raise ValueError(
                "Pipeline run not found: "
                f"{pipeline_run_id}"
            )


def complete_pipeline_run(
    *,
    pipeline_run_id: int,
    summary: Mapping[str, Any],
) -> None:
    values = dict(summary)

    query = text(
        """
        UPDATE dbo.pipeline_runs
        SET
            run_status = 'SUCCESS',
            catalog_id = :catalog_id,
            version_id = :version_id,
            validation_status =
                :validation_status,
            governance_decision =
                :governance_decision,
            trust_score = :trust_score,
            lifecycle_state =
                :lifecycle_state,
            finished_at = SYSUTCDATETIME(),
            duration_ms = DATEDIFF_BIG(
                MILLISECOND,
                started_at,
                SYSUTCDATETIME()
            ),
            error_type = NULL,
            error_message = NULL,
            updated_at = SYSUTCDATETIME()
        WHERE pipeline_run_id =
            :pipeline_run_id;
        """
    )

    params = {
        "pipeline_run_id": int(
            pipeline_run_id
        ),
        "catalog_id": values.get(
            "catalog_id"
        ),
        "version_id": values.get(
            "version_id"
        ),
        "validation_status": values.get(
            "validation_status"
        ),
        "governance_decision": values.get(
            "governance_decision"
        ),
        "trust_score": values.get(
            "trust_score"
        ),
        "lifecycle_state": values.get(
            "lifecycle_state"
        ),
    }

    engine = get_engine()

    with engine.begin() as connection:
        result = connection.execute(
            query,
            params,
        )

        if result.rowcount != 1:
            raise ValueError(
                "Pipeline run not found: "
                f"{pipeline_run_id}"
            )


def fail_pipeline_run(
    *,
    pipeline_run_id: int,
    error: BaseException,
) -> None:
    query = text(
        """
        UPDATE dbo.pipeline_runs
        SET
            run_status = 'FAILED',
            finished_at = SYSUTCDATETIME(),
            duration_ms = DATEDIFF_BIG(
                MILLISECOND,
                started_at,
                SYSUTCDATETIME()
            ),
            error_type = :error_type,
            error_message = :error_message,
            updated_at = SYSUTCDATETIME()
        WHERE pipeline_run_id =
            :pipeline_run_id;
        """
    )

    engine = get_engine()

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "pipeline_run_id": int(
                    pipeline_run_id
                ),
                "error_type": type(
                    error
                ).__name__,
                "error_message": str(error),
            },
        )

        if result.rowcount != 1:
            raise ValueError(
                "Pipeline run not found: "
                f"{pipeline_run_id}"
            )


def get_pipeline_run(
    pipeline_run_id: int,
) -> dict[str, Any] | None:
    query = text(
        """
        SELECT
            pipeline_run_id,
            dag_id,
            airflow_run_id,
            source_path,
            run_status,
            attempt_count,
            catalog_id,
            version_id,
            validation_status,
            governance_decision,
            trust_score,
            lifecycle_state,
            started_at,
            finished_at,
            duration_ms,
            error_type,
            error_message,
            created_at,
            updated_at
        FROM dbo.pipeline_runs
        WHERE pipeline_run_id =
            :pipeline_run_id;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "pipeline_run_id": int(
                    pipeline_run_id
                ),
            },
        ).mappings().first()

    return (
        dict(row)
        if row is not None
        else None
    )


def get_pipeline_run_history(
    limit: int = 50,
) -> pd.DataFrame:
    safe_limit = max(
        1,
        min(
            int(limit),
            1000,
        ),
    )

    query = text(
        f"""
        SELECT TOP {safe_limit}
            pipeline_run_id,
            dag_id,
            airflow_run_id,
            source_path,
            run_status,
            attempt_count,
            catalog_id,
            version_id,
            validation_status,
            governance_decision,
            trust_score,
            lifecycle_state,
            started_at,
            finished_at,
            duration_ms,
            error_type,
            error_message,
            created_at,
            updated_at
        FROM dbo.pipeline_runs
        ORDER BY
            started_at DESC,
            pipeline_run_id DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
        )


def get_pipeline_run_history_by_catalog(
    catalog_id: int,
    limit: int = 50,
) -> pd.DataFrame:
    if (
        isinstance(catalog_id, bool)
        or not isinstance(catalog_id, int)
        or catalog_id <= 0
    ):
        raise ValueError(
            "catalog_id must be a positive integer."
        )

    safe_limit = max(
        1,
        min(
            int(limit),
            1000,
        ),
    )

    query = text(
        f"""
        SELECT TOP {safe_limit}
            pipeline_run_id,
            dag_id,
            airflow_run_id,
            source_path,
            run_status,
            attempt_count,
            catalog_id,
            version_id,
            validation_status,
            governance_decision,
            trust_score,
            lifecycle_state,
            started_at,
            finished_at,
            duration_ms,
            error_type,
            error_message,
            created_at,
            updated_at
        FROM dbo.pipeline_runs
        WHERE catalog_id = :catalog_id
        ORDER BY
            started_at DESC,
            pipeline_run_id DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql_query(
            query,
            connection,
            params={
                "catalog_id": catalog_id,
            },
        )
