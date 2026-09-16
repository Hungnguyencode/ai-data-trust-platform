from __future__ import annotations

from pathlib import Path


def test_volume_dag_source_contains_expected_contract():
    dag_path = (
        Path(__file__).resolve().parents[1]
        / "orchestration"
        / "airflow"
        / "dags"
        / "data_volume_monitor.py"
    )

    source = dag_path.read_text(
        encoding="utf-8"
    )

    assert (
        'dag_id="data_volume_monitor"'
        in source
    )

    assert (
        'schedule="*/5 * * * *"'
        in source
    )

    assert (
        "check_enabled_volume_policies"
        in source
    )

    assert (
        "run_volume_checks"
        in source
    )

    assert (
        "max_active_runs=1"
        in source
    )