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
    def register_pipeline_run() -> dict[str, Any]:
        from database.repositories.pipeline_run_repository import (
            create_pipeline_run,
        )

        context = get_current_context()

        source_path = str(
            context["params"]["source_path"]
        )

        task_instance = context[
            "task_instance"
        ]

        pipeline_run = create_pipeline_run(
            dag_id=str(
                task_instance.dag_id
            ),
            airflow_run_id=str(
                task_instance.run_id
            ),
            source_path=source_path,
        )

        pipeline_run_id = int(
            pipeline_run["pipeline_run_id"]
        )

        print(
            "Registered pipeline run: "
            f"{pipeline_run_id}"
        )

        return {
            "pipeline_run_id": (
                pipeline_run_id
            ),
            "source_path": source_path,
        }

    @task
    def validate_input(
        run_context: dict[str, Any],
    ) -> dict[str, Any]:
        from database.repositories.pipeline_run_repository import (
            fail_pipeline_run,
        )
        from src.observability.operational_events import (
            emit_pipeline_failed_event,
        )

        pipeline_run_id = int(
            run_context["pipeline_run_id"]
        )

        source_path = str(
            run_context["source_path"]
        )

        try:
            path = Path(source_path)

            if not path.exists():
                raise FileNotFoundError(
                    "Dataset not found: "
                    f"{source_path}"
                )

            if not path.is_file():
                raise ValueError(
                    "Dataset path is not a file: "
                    f"{source_path}"
                )

        except Exception as exc:
            fail_pipeline_run(
                pipeline_run_id=(
                    pipeline_run_id
                ),
                error=exc,
            )

            emit_pipeline_failed_event(
                pipeline_run_id=(
                    pipeline_run_id
                ),
                event_stage="VALIDATE_INPUT",
                error=exc,
            )

            raise

        print(
            "Validated dataset input: "
            f"{source_path}"
        )

        return run_context

    @task(
        retries=2,
        retry_delay=timedelta(
            seconds=20
        ),
        execution_timeout=timedelta(
            minutes=10
        ),
    )
    def run_platform_workflow(
        run_context: dict[str, Any],
    ) -> dict[str, Any]:
        from database.repositories.pipeline_run_repository import (
            fail_pipeline_run,
            mark_pipeline_run_running,
        )
        from src.observability.operational_events import (
            emit_pipeline_failed_event,
        )
        from src.workflows import (
            run_dataset_workflow,
        )

        pipeline_run_id = int(
            run_context["pipeline_run_id"]
        )

        source_path = str(
            run_context["source_path"]
        )

        mark_pipeline_run_running(
            pipeline_run_id
        )

        try:
            result = run_dataset_workflow(
                source_path
            )

            summary = json.loads(
                json.dumps(
                    result.summary(),
                    default=str,
                )
            )

            return summary

        except Exception as exc:
            fail_pipeline_run(
                pipeline_run_id=(
                    pipeline_run_id
                ),
                error=exc,
            )

            emit_pipeline_failed_event(
                pipeline_run_id=(
                    pipeline_run_id
                ),
                event_stage="PLATFORM_WORKFLOW",
                error=exc,
            )

            raise

    @task
    def publish_summary(
        run_context: dict[str, Any],
        summary: dict[str, Any],
    ) -> None:
        from database.repositories.pipeline_run_repository import (
            complete_pipeline_run,
            fail_pipeline_run,
        )
        from src.observability.operational_events import (
            emit_pipeline_failed_event,
        )

        pipeline_run_id = int(
            run_context["pipeline_run_id"]
        )

        try:
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

            complete_pipeline_run(
                pipeline_run_id=(
                    pipeline_run_id
                ),
                summary=summary,
            )

        except Exception as exc:
            fail_pipeline_run(
                pipeline_run_id=(
                    pipeline_run_id
                ),
                error=exc,
            )

            emit_pipeline_failed_event(
                pipeline_run_id=(
                    pipeline_run_id
                ),
                event_stage="PUBLISH_SUMMARY",
                error=exc,
            )

            raise

    run_context = (
        register_pipeline_run()
    )

    validated_run_context = (
        validate_input(
            run_context
        )
    )

    summary = run_platform_workflow(
        validated_run_context
    )

    publish_summary(
        validated_run_context,
        summary,
    )


ai_data_trust_pipeline()