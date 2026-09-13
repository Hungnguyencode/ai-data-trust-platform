from __future__ import annotations

from datetime import timedelta

from airflow.sdk import dag, task


@dag(
    dag_id="ai_data_trust_smoke",
    schedule=None,
    catchup=False,
    tags=["ai-data-trust", "orchestration"],
)
def ai_data_trust_smoke():
    @task(
        retries=2,
        retry_delay=timedelta(seconds=10),
    )
    def start() -> str:
        return "airflow-ok"

    @task
    def finish(message: str) -> None:
        print(
            "AI Data Trust Platform "
            f"orchestration smoke: {message}"
        )

    finish(start())


ai_data_trust_smoke()