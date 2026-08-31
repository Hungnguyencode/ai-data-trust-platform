from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from src.anomaly.iqr_detector import detect_iqr_outliers
from src.anomaly.isolation_forest import detect_isolation_forest_outliers
from src.anomaly.zscore_detector import detect_zscore_outliers


def calculate_anomaly_score(outlier_rate: float) -> float:
    """
    Anomaly Score càng cao càng tốt.

    outlier_rate là phần trăm dòng bị đánh dấu bất thường.
    Phạt mạnh hơn bản cũ để điểm phản ánh rõ hơn.
    """
    score = 100 - (outlier_rate * 2)
    return round(max(0.0, min(100.0, score)), 2)


def get_anomaly_risk_level(anomaly_score: float) -> str:
    if anomaly_score >= 90:
        return "Low"
    if anomaly_score >= 75:
        return "Medium"
    if anomaly_score >= 50:
        return "High"
    return "Critical"


def run_anomaly_detection(
    df: pd.DataFrame,
    zscore_threshold: float = 3.0,
    isolation_contamination: float = 0.1,
) -> Dict[str, Any]:
    """
    Chạy toàn bộ anomaly detection Version 0.6.

    Bao gồm:
    - IQR
    - Z-score
    - Isolation Forest
    - Tổng hợp unique anomaly rows
    - Anomaly Score
    """
    iqr_result = detect_iqr_outliers(df)
    zscore_result = detect_zscore_outliers(df, threshold=zscore_threshold)
    isolation_result = detect_isolation_forest_outliers(
        df,
        contamination=isolation_contamination,
    )

    combined_indexes = set()
    combined_indexes.update(iqr_result["outlier_row_indexes"])
    combined_indexes.update(zscore_result["outlier_row_indexes"])
    combined_indexes.update(isolation_result["outlier_row_indexes"])

    combined_outlier_rows_df = (
        df.loc[sorted(combined_indexes)].copy()
        if combined_indexes
        else pd.DataFrame()
    )

    total_rows = len(df)
    total_anomaly_rows = len(combined_indexes)
    anomaly_rate = round(total_anomaly_rows / max(total_rows, 1) * 100, 2)
    anomaly_score = calculate_anomaly_score(anomaly_rate)
    risk_level = get_anomaly_risk_level(anomaly_score)

    summary_df = pd.DataFrame(
        [
            {
                "method": "IQR",
                "total_outlier_rows": iqr_result["total_outlier_rows"],
                "outlier_rate (%)": iqr_result["outlier_rate (%)"],
            },
            {
                "method": "Z-score",
                "total_outlier_rows": zscore_result["total_outlier_rows"],
                "outlier_rate (%)": zscore_result["outlier_rate (%)"],
            },
            {
                "method": "Isolation Forest",
                "total_outlier_rows": isolation_result["summary"]["total_outlier_rows"],
                "outlier_rate (%)": isolation_result["summary"]["outlier_rate (%)"],
            },
            {
                "method": "Combined Unique Rows",
                "total_outlier_rows": total_anomaly_rows,
                "outlier_rate (%)": anomaly_rate,
            },
        ]
    )

    return {
        "summary": {
            "total_rows": total_rows,
            "total_anomaly_rows": total_anomaly_rows,
            "anomaly_rate (%)": anomaly_rate,
            "anomaly_score": anomaly_score,
            "risk_level": risk_level,
        },
        "summary_df": summary_df,
        "iqr_result": iqr_result,
        "zscore_result": zscore_result,
        "isolation_forest_result": isolation_result,
        "combined_outlier_rows_df": combined_outlier_rows_df,
    }