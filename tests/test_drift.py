import pandas as pd

from src.drift.data_drift import (
    build_categorical_distribution_df,
    detect_categorical_drift,
    detect_numeric_drift,
    run_drift_detection,
)
from src.drift.psi import calculate_psi, interpret_psi
from src.drift.schema_drift import compare_schema


def test_psi_interpretation_thresholds():
    assert interpret_psi(0.0) == "No significant drift"
    assert interpret_psi(0.099) == "No significant drift"

    assert interpret_psi(0.10) == "Moderate drift"
    assert interpret_psi(0.249) == "Moderate drift"

    assert interpret_psi(0.25) == "High drift"
    assert interpret_psi(1.0) == "High drift"


def test_calculate_psi_identical_distribution_is_stable():
    baseline = pd.Series(range(1, 101))
    current = pd.Series(range(1, 101))

    result = calculate_psi(
        baseline_series=baseline,
        current_series=current,
    )

    assert result["psi"] == 0.0
    assert result["interpretation"] == "No significant drift"
    assert not result["details_df"].empty


def test_schema_drift_detects_added_removed_and_dtype_changes():
    baseline = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "age": [20, 30, 40],
            "old_column": ["A", "B", "C"],
        }
    )

    current = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "age": ["20", "30", "40"],
            "new_column": [10, 20, 30],
        }
    )

    result = compare_schema(
        baseline_df=baseline,
        current_df=current,
    )

    summary = result["summary"]

    assert summary["baseline_columns"] == 3
    assert summary["current_columns"] == 3
    assert summary["common_columns"] == 2

    assert summary["added_columns"] == 1
    assert summary["removed_columns"] == 1
    assert summary["dtype_changes"] == 1
    assert summary["schema_drift_detected"] is True

    assert result["added_columns"] == ["new_column"]
    assert result["removed_columns"] == ["old_column"]

    assert len(result["dtype_changes"]) == 1
    assert result["dtype_changes"][0]["column_name"] == "age"

    change_types = set(result["changes_df"]["change_type"])

    assert change_types == {
        "Added Column",
        "Removed Column",
        "Dtype Changed",
    }


def test_numeric_drift_detects_large_distribution_change_and_skips_id():
    baseline = pd.DataFrame(
        {
            "customer_id": list(range(100)),
            "amount": list(range(100)),
        }
    )

    current = pd.DataFrame(
        {
            "customer_id": list(range(100, 200)),
            "amount": list(range(1000, 1100)),
        }
    )

    result = detect_numeric_drift(
        baseline_df=baseline,
        current_df=current,
        common_columns=[
            "customer_id",
            "amount",
        ],
    )

    # ID column phải bị loại khỏi drift detection.
    assert "customer_id" not in result["column_name"].tolist()

    assert result["column_name"].tolist() == ["amount"]

    amount = result.iloc[0]

    assert amount["drift_type"] == "Numeric"
    assert amount["drift_level"] == "High drift"

    assert amount["psi"] >= 0.25
    assert amount["current_mean"] > amount["baseline_mean"]


def test_categorical_drift_detects_large_distribution_change():
    baseline = pd.DataFrame(
        {
            "segment": (
                ["A"] * 90
                + ["B"] * 10
            )
        }
    )

    current = pd.DataFrame(
        {
            "segment": (
                ["A"] * 10
                + ["B"] * 90
            )
        }
    )

    result = detect_categorical_drift(
        baseline_df=baseline,
        current_df=current,
        common_columns=["segment"],
    )

    assert len(result) == 1

    segment = result.iloc[0]

    assert segment["column_name"] == "segment"
    assert segment["drift_type"] == "Categorical"

    assert segment["distribution_diff"] == 0.8
    assert segment["drift_level"] == "High drift"


def test_build_categorical_distribution_dataframe():
    baseline = pd.DataFrame(
        {
            "segment": [
                "A",
                "A",
                "A",
                "B",
            ]
        }
    )

    current = pd.DataFrame(
        {
            "segment": [
                "A",
                "B",
                "B",
                "B",
            ]
        }
    )

    result = build_categorical_distribution_df(
        baseline_df=baseline,
        current_df=current,
        column_name="segment",
    )

    assert set(result["value"]) == {
        "A",
        "B",
    }

    distributions = result.set_index("value")

    assert distributions.loc["A", "baseline_pct"] == 75.0
    assert distributions.loc["A", "current_pct"] == 25.0

    assert distributions.loc["B", "baseline_pct"] == 25.0
    assert distributions.loc["B", "current_pct"] == 75.0

    assert result["baseline_pct"].sum() == 100.0
    assert result["current_pct"].sum() == 100.0


def test_drift_engine_identical_datasets_are_stable():
    baseline = pd.DataFrame(
        {
            "customer_id": list(range(1, 101)),
            "amount": list(range(100)),
            "segment": (
                ["A"] * 50
                + ["B"] * 50
            ),
        }
    )

    current = baseline.copy()

    result = run_drift_detection(
        baseline_df=baseline,
        current_df=current,
    )

    assert set(result.keys()) == {
        "summary",
        "schema_report",
        "numeric_drift_df",
        "categorical_drift_df",
        "all_drift_df",
    }

    summary = result["summary"]

    assert summary["baseline_rows"] == 100
    assert summary["current_rows"] == 100

    assert summary["schema_drift_count"] == 0
    assert summary["drifted_columns"] == 0
    assert summary["high_drift_columns"] == 0
    assert summary["moderate_drift_columns"] == 0

    assert summary["drift_rate (%)"] == 0.0
    assert summary["overall_drift_level"] == "None"
    assert summary["drift_score"] == 100.0

    assert (
        result["schema_report"]["summary"][
            "schema_drift_detected"
        ]
        is False
    )


def test_drift_engine_reports_schema_change():
    baseline = pd.DataFrame(
        {
            "amount": [10, 20, 30, 40],
            "segment": ["A", "A", "B", "B"],
        }
    )

    current = baseline.copy()
    current["new_feature"] = [1, 2, 3, 4]

    result = run_drift_detection(
        baseline_df=baseline,
        current_df=current,
    )

    summary = result["summary"]

    assert summary["schema_drift_count"] == 1

    assert (
        result["schema_report"]["summary"][
            "added_columns"
        ]
        == 1
    )

    assert (
        result["schema_report"]["added_columns"]
        == ["new_feature"]
    )

    # Có schema change nên overall không được báo hoàn toàn "None".
    assert summary["overall_drift_level"] != "None"

    assert 0 <= summary["drift_score"] <= 100