from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from airflow.sdk import dag, task


@dag(
    dag_id="data_freshness_monitor",
    description=(
        "Scheduled freshness monitoring for "
        "enabled dataset policies."
    ),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=[
        "ai-data-trust",
        "observability",
        "freshness",
    ],
)
def data_freshness_monitor():
    @task(
        retries=1,
        retry_delay=timedelta(
            minutes=1
        ),
        execution_timeout=timedelta(
            minutes=5
        ),
    )
    def run_freshness_checks() -> dict[str, Any]:
        from src.observability.freshness_monitor import (
            check_enabled_freshness_policies,
        )

        result = (
            check_enabled_freshness_policies()
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
            "fresh_count": result[
                "fresh_count"
            ],
            "stale_count": result[
                "stale_count"
            ],
            "no_data_count": result[
                "no_data_count"
            ],
        }

        print(
            "Dataset freshness monitor result:"
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
                "Freshness monitor failed for "
                f"{result['failed_count']} "
                "dataset(s)."
            )

        return summary

    run_freshness_checks()


data_freshness_monitor()