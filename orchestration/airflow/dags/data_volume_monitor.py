from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from airflow.sdk import dag, task


@dag(
    dag_id="data_volume_monitor",
    description=(
        "Scheduled volume monitoring for "
        "enabled dataset policies."
    ),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=[
        "ai-data-trust",
        "observability",
        "volume",
    ],
)
def data_volume_monitor():
    @task(
        retries=1,
        retry_delay=timedelta(
            minutes=1
        ),
        execution_timeout=timedelta(
            minutes=5
        ),
    )
    def run_volume_checks() -> dict[str, Any]:
        from src.observability.volume_monitor import (
            check_enabled_volume_policies,
        )

        result = (
            check_enabled_volume_policies()
        )

        summary = {
            "policy_count": result[
                "policy_count"
            ],
            "checked_count": result[
                "checked_count"
            ],
            "failed_count": result[
                "failed_count"
            ],
            "normal_count": result[
                "normal_count"
            ],
            "drop_count": result[
                "drop_count"
            ],
            "spike_count": result[
                "spike_count"
            ],
            "no_baseline_count": result[
                "no_baseline_count"
            ],
        }

        print(
            "Dataset volume monitor result:"
        )

        print(
            json.dumps(
                {
                    "summary": summary,
                    "errors": result[
                        "errors"
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
        )

        if result["failed_count"] > 0:
            raise RuntimeError(
                "Volume monitor failed for "
                f"{result['failed_count']} "
                "dataset(s)."
            )

        return summary

    run_volume_checks()


data_volume_monitor()