from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


def detect_isolation_forest_outliers(
    df: pd.DataFrame,
    contamination: float = 0.1,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Phát hiện anomaly bằng Isolation Forest.

    Chỉ dùng các cột numeric.
    Với dataset quá nhỏ hoặc không có numeric column thì trả về rỗng.
    """
    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty or len(numeric_df) < 8:
        return {
            "method": "Isolation Forest",
            "summary": {
                "used": False,
                "reason": "Dataset quá nhỏ hoặc không có cột numeric phù hợp.",
                "contamination": contamination,
                "total_outlier_rows": 0,
                "outlier_rate (%)": 0.0,
            },
            "outlier_rows_df": pd.DataFrame(),
            "scores_df": pd.DataFrame(),
            "outlier_row_indexes": set(),
        }

    numeric_columns = numeric_df.columns.tolist()

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()

    imputed_values = imputer.fit_transform(numeric_df)
    scaled_values = scaler.fit_transform(imputed_values)

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=100,
    )

    predictions = model.fit_predict(scaled_values)
    anomaly_scores = model.decision_function(scaled_values)

    scores_df = pd.DataFrame(
        {
            "row_index": numeric_df.index,
            "is_anomaly": predictions == -1,
            "anomaly_score": anomaly_scores,
        }
    )

    outlier_indexes = set(scores_df.loc[scores_df["is_anomaly"], "row_index"].tolist())
    outlier_rows_df = df.loc[sorted(outlier_indexes)].copy() if outlier_indexes else pd.DataFrame()

    total_outlier_rows = len(outlier_indexes)
    outlier_rate = round(total_outlier_rows / max(len(df), 1) * 100, 2)

    return {
        "method": "Isolation Forest",
        "summary": {
            "used": True,
            "reason": "Isolation Forest chạy thành công.",
            "numeric_columns": numeric_columns,
            "contamination": contamination,
            "total_outlier_rows": total_outlier_rows,
            "outlier_rate (%)": outlier_rate,
        },
        "outlier_rows_df": outlier_rows_df,
        "scores_df": scores_df,
        "outlier_row_indexes": outlier_indexes,
    }