import pandas as pd

from src.anomaly.anomaly_engine import (
    calculate_anomaly_score,
    get_anomaly_risk_level,
    run_anomaly_detection,
)
from src.anomaly.iqr_detector import detect_iqr_outliers
from src.anomaly.isolation_forest import detect_isolation_forest_outliers
from src.anomaly.zscore_detector import detect_zscore_outliers


def test_anomaly_score_and_risk_thresholds():
    assert calculate_anomaly_score(0.0) == 100.0
    assert calculate_anomaly_score(5.0) == 90.0
    assert calculate_anomaly_score(12.5) == 75.0
    assert calculate_anomaly_score(25.0) == 50.0

    # Score phải được clamp trong khoảng 0..100.
    assert calculate_anomaly_score(100.0) == 0.0

    assert get_anomaly_risk_level(90.0) == "Low"
    assert get_anomaly_risk_level(89.99) == "Medium"

    assert get_anomaly_risk_level(75.0) == "Medium"
    assert get_anomaly_risk_level(74.99) == "High"

    assert get_anomaly_risk_level(50.0) == "High"
    assert get_anomaly_risk_level(49.99) == "Critical"


def test_iqr_detector_finds_extreme_value():
    df = pd.DataFrame(
        {
            "value": [1, 2, 3, 4, 5, 100],
        }
    )

    result = detect_iqr_outliers(df)

    assert result["method"] == "IQR"
    assert result["outlier_row_indexes"] == {5}
    assert result["total_outlier_rows"] == 1
    assert result["outlier_rate (%)"] == 16.67

    summary = result["summary_df"].iloc[0]

    assert summary["column_name"] == "value"
    assert summary["outlier_count"] == 1
    assert summary["upper_bound"] < 100


def test_zscore_detector_finds_extreme_value():
    df = pd.DataFrame(
        {
            "value": [0] * 20 + [100],
        }
    )

    result = detect_zscore_outliers(
        df,
        threshold=3.0,
    )

    assert result["method"] == "Z-score"
    assert result["outlier_row_indexes"] == {20}
    assert result["total_outlier_rows"] == 1

    summary = result["summary_df"].iloc[0]

    assert summary["column_name"] == "value"
    assert summary["threshold"] == 3.0
    assert summary["outlier_count"] == 1


def test_isolation_forest_skips_dataset_that_is_too_small():
    df = pd.DataFrame(
        {
            "x": [1, 2, 3, 4, 5, 6, 7],
            "y": [10, 20, 30, 40, 50, 60, 70],
        }
    )

    result = detect_isolation_forest_outliers(df)

    summary = result["summary"]

    assert result["method"] == "Isolation Forest"
    assert summary["used"] is False
    assert summary["total_outlier_rows"] == 0

    assert result["outlier_row_indexes"] == set()
    assert result["outlier_rows_df"].empty
    assert result["scores_df"].empty


def test_isolation_forest_is_deterministic():
    df = pd.DataFrame(
        {
            "x": list(range(20)),
            "y": [
                10, 11, 12, 13, 14,
                15, 16, 17, 18, 19,
                20, 21, 22, 23, 24,
                25, 26, 27, 1000, -1000,
            ],
        }
    )

    first = detect_isolation_forest_outliers(
        df,
        contamination=0.10,
    )

    second = detect_isolation_forest_outliers(
        df,
        contamination=0.10,
    )

    assert first["summary"]["used"] is True
    assert second["summary"]["used"] is True

    assert first["summary"]["numeric_columns"] == [
        "x",
        "y",
    ]

    assert len(first["scores_df"]) == len(df)

    assert (
        first["summary"]["total_outlier_rows"]
        == len(first["outlier_row_indexes"])
    )

    # random_state=42 phải làm kết quả ổn định giữa các lần chạy.
    assert (
        first["outlier_row_indexes"]
        == second["outlier_row_indexes"]
    )


def test_anomaly_engine_combines_unique_rows_correctly():
    df = pd.DataFrame(
        {
            "x": list(range(20)) + [1000],
            "y": [
                100, 101, 102, 103, 104,
                105, 106, 107, 108, 109,
                110, 111, 112, 113, 114,
                115, 116, 117, 118, 119,
                -1000,
            ],
        }
    )

    result = run_anomaly_detection(
        df,
        zscore_threshold=3.0,
        isolation_contamination=0.10,
    )

    expected_indexes = set()

    expected_indexes.update(
        result["iqr_result"]["outlier_row_indexes"]
    )

    expected_indexes.update(
        result["zscore_result"]["outlier_row_indexes"]
    )

    expected_indexes.update(
        result["isolation_forest_result"]["outlier_row_indexes"]
    )

    summary = result["summary"]

    assert set(result.keys()) == {
        "summary",
        "summary_df",
        "iqr_result",
        "zscore_result",
        "isolation_forest_result",
        "combined_outlier_rows_df",
    }

    assert summary["total_rows"] == len(df)

    assert (
        summary["total_anomaly_rows"]
        == len(expected_indexes)
    )

    assert set(
        result["combined_outlier_rows_df"].index
    ) == expected_indexes

    expected_rate = round(
        len(expected_indexes) / len(df) * 100,
        2,
    )

    assert summary["anomaly_rate (%)"] == expected_rate

    assert (
        summary["anomaly_score"]
        == calculate_anomaly_score(expected_rate)
    )

    assert len(result["summary_df"]) == 4


def test_anomaly_engine_handles_dataset_without_numeric_columns():
    df = pd.DataFrame(
        {
            "name": ["A", "B", "C", "D"],
            "city": ["HN", "HCM", "DN", "HP"],
        }
    )

    result = run_anomaly_detection(df)

    summary = result["summary"]

    assert summary["total_rows"] == 4
    assert summary["total_anomaly_rows"] == 0
    assert summary["anomaly_rate (%)"] == 0.0
    assert summary["anomaly_score"] == 100.0
    assert summary["risk_level"] == "Low"

    assert result["combined_outlier_rows_df"].empty