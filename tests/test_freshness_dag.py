from __future__ import annotations

from pathlib import Path


def test_freshness_dag_source_contains_expected_contract():
    dag_path = (
        Path(__file__).resolve().parents[1]
        / "orchestration"
        / "airflow"
        / "dags"
        / "data_freshness_monitor.py"
    )

    source = dag_path.read_text(
        encoding="utf-8"
    )

    assert (
        'dag_id="data_freshness_monitor"'
        in source
    )

    assert (
        'schedule="*/5 * * * *"'
        in source
    )

    assert (
        "check_enabled_freshness_policies"
        in source
    )

    assert (
        "run_freshness_checks"
        in source
    )

    assert (
        'max_active_runs=1'
        in source
    )