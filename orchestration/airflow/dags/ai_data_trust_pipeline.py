from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from airflow.sdk import dag, get_current_context, task

DEFAULT_SOURCE_PATH = (
    "/app/data/lifecycle_test/v3/sample_customers.csv"
)


@dag(
    dag_id="ai_data_trust_pipeline",
    description="Governed AI Data Trust Platform pipeline.",
    schedule=None,
    catchup=False,
    max_active_runs=1,
    params={
        "source_path": DEFAULT_SOURCE_PATH,
    },
    tags=[
        "ai-data-trust",
        "data-quality",
        "governance",
    ],
)
def ai_data_trust_pipeline():
    @task
    def validate_input() -> str:
        context = get_current_context()

        source_path = str(
            context["params"]["source_path"]
        )

        path = Path(source_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {source_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Dataset path is not a file: {source_path}"
            )

        print(
            "Validated dataset input: "
            f"{source_path}"
        )

        return source_path

    @task(
        retries=2,
        retry_delay=timedelta(seconds=20),
        execution_timeout=timedelta(minutes=10),
    )
    def run_platform_workflow(
        source_path: str,
    ) -> dict[str, Any]:
        from src.workflows import (
            run_dataset_workflow,
        )

        result = run_dataset_workflow(
            source_path,
        )

        summary = result.summary()

        # Guarantee that the XCom payload remains
        # JSON serializable and lightweight.
        return json.loads(
            json.dumps(
                summary,
                default=str,
            )
        )

    @task
    def publish_summary(
        summary: dict[str, Any],
    ) -> None:
        print(
            "AI Data Trust Platform "
            "workflow completed:"
        )

        print(
            json.dumps(
                summary,
                indent=2,
                ensure_ascii=False,
            )
        )

    source_path = validate_input()

    summary = run_platform_workflow(
        source_path
    )

    publish_summary(
        summary
    )


ai_data_trust_pipeline()