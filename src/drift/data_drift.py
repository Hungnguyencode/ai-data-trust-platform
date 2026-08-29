from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy.stats import chisquare, ks_2samp

from src.drift.psi import calculate_psi
from src.drift.schema_drift import compare_schema


def _drift_level_from_p_value(p_value: float) -> str:
    if p_value < 0.01:
        return "High drift"
    if p_value < 0.05:
        return "Moderate drift"
    return "No significant drift"


def _overall_drift_level(high_count: int, moderate_count: int) -> str:
    if high_count >= 2:
        return "High"
    if high_count >= 1 or moderate_count >= 2:
        return "Medium"
    if moderate_count >= 1:
        return "Low"
    return "None"


def _is_identifier_column(column_name: str) -> bool:
    lower_name = column_name.lower().strip()
    identifier_keywords = [
        "id",
        "_id",
        "customer_id",
        "user_id",
        "account_id",
        "transaction_id",
        "order_id",
        "uuid",
        "code",
    ]

    return (
        lower_name == "id"
        or lower_name.endswith("_id")
        or any(keyword == lower_name for keyword in identifier_keywords)
    )


def _is_numeric_like(series: pd.Series, threshold: float = 0.8) -> bool:
    non_null = series.dropna()

    if non_null.empty:
        return False

    converted = pd.to_numeric(non_null, errors="coerce")
    numeric_ratio = converted.notna().mean()

    return numeric_ratio >= threshold


def detect_numeric_drift(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    common_columns: List[str],
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for col in common_columns:
        if _is_identifier_column(col):
            continue

        baseline_numeric = pd.to_numeric(baseline_df[col], errors="coerce").dropna()
        current_numeric = pd.to_numeric(current_df[col], errors="coerce").dropna()

        if baseline_numeric.empty or current_numeric.empty:
            continue

        # Nếu cột numeric nhưng thực chất là ID, vẫn cho hiện nhưng drift level nhẹ hơn qua p-value/psi.
        psi_result = calculate_psi(baseline_numeric, current_numeric)

        try:
            ks_stat, ks_p_value = ks_2samp(baseline_numeric, current_numeric)
            ks_stat = round(float(ks_stat), 4)
            ks_p_value = round(float(ks_p_value), 6)
        except Exception:
            ks_stat = None
            ks_p_value = None

        baseline_mean = round(float(baseline_numeric.mean()), 4)
        current_mean = round(float(current_numeric.mean()), 4)
        mean_diff = round(current_mean - baseline_mean, 4)

        baseline_median = round(float(baseline_numeric.median()), 4)
        current_median = round(float(current_numeric.median()), 4)

        if psi_result["psi"] >= 0.25:
            drift_level = "High drift"
        elif psi_result["psi"] >= 0.1:
            drift_level = "Moderate drift"
        elif ks_p_value is not None:
            drift_level = _drift_level_from_p_value(ks_p_value)
        else:
            drift_level = "No significant drift"

        rows.append(
            {
                "column_name": col,
                "drift_type": "Numeric",
                "baseline_mean": baseline_mean,
                "current_mean": current_mean,
                "mean_diff": mean_diff,
                "baseline_median": baseline_median,
                "current_median": current_median,
                "psi": psi_result["psi"],
                "psi_interpretation": psi_result["interpretation"],
                "ks_statistic": ks_stat,
                "ks_p_value": ks_p_value,
                "drift_level": drift_level,
            }
        )

    return pd.DataFrame(rows)


def detect_categorical_drift(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    common_columns: List[str],
    max_unique_values: int = 30,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for col in common_columns:
        if _is_identifier_column(col):
            continue

        if _is_numeric_like(baseline_df[col]) and _is_numeric_like(current_df[col]):
            continue


        baseline_series = baseline_df[col].dropna().astype(str)
        current_series = current_df[col].dropna().astype(str)

        if baseline_series.empty or current_series.empty:
            continue

        combined_unique = sorted(set(baseline_series.unique()) | set(current_series.unique()))

        if len(combined_unique) > max_unique_values:
            continue

        baseline_counts = baseline_series.value_counts()
        current_counts = current_series.value_counts()

        baseline_dist = np.array([baseline_counts.get(v, 0) for v in combined_unique], dtype=float)
        current_dist = np.array([current_counts.get(v, 0) for v in combined_unique], dtype=float)

        if baseline_dist.sum() == 0 or current_dist.sum() == 0:
            continue

        baseline_pct = baseline_dist / baseline_dist.sum()
        current_pct = current_dist / current_dist.sum()

        distribution_diff = float(np.abs(baseline_pct - current_pct).sum() / 2)

        try:
            expected = baseline_pct * current_dist.sum()
            expected = np.where(expected == 0, 1e-6, expected)
            chi_stat, chi_p_value = chisquare(f_obs=current_dist, f_exp=expected)
            chi_stat = round(float(chi_stat), 4)
            chi_p_value = round(float(chi_p_value), 6)
        except Exception:
            chi_stat = None
            chi_p_value = None

        if distribution_diff >= 0.3:
            drift_level = "High drift"
        elif distribution_diff >= 0.15:
            drift_level = "Moderate drift"
        elif chi_p_value is not None:
            drift_level = _drift_level_from_p_value(chi_p_value)
        else:
            drift_level = "No significant drift"

        rows.append(
            {
                "column_name": col,
                "drift_type": "Categorical",
                "unique_values": len(combined_unique),
                "distribution_diff": round(distribution_diff, 4),
                "chi_square_statistic": chi_stat,
                "chi_square_p_value": chi_p_value,
                "drift_level": drift_level,
            }
        )

    return pd.DataFrame(rows)


def build_categorical_distribution_df(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    column_name: str,
) -> pd.DataFrame:
    baseline_series = baseline_df[column_name].dropna().astype(str)
    current_series = current_df[column_name].dropna().astype(str)

    baseline_counts = baseline_series.value_counts(normalize=True)
    current_counts = current_series.value_counts(normalize=True)

    values = sorted(set(baseline_counts.index) | set(current_counts.index))

    rows = []

    for value in values:
        rows.append(
            {
                "value": value,
                "baseline_pct": round(float(baseline_counts.get(value, 0) * 100), 2),
                "current_pct": round(float(current_counts.get(value, 0) * 100), 2),
            }
        )

    return pd.DataFrame(rows)


def run_drift_detection(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
) -> Dict[str, Any]:
    schema_report = compare_schema(baseline_df, current_df)
    common_columns = schema_report["common_columns"]

    numeric_drift_df = detect_numeric_drift(
        baseline_df=baseline_df,
        current_df=current_df,
        common_columns=common_columns,
    )

    categorical_drift_df = detect_categorical_drift(
        baseline_df=baseline_df,
        current_df=current_df,
        common_columns=common_columns,
    )

    drift_frames = []

    if not numeric_drift_df.empty:
        drift_frames.append(
            numeric_drift_df[
                ["column_name", "drift_type", "drift_level"]
            ].copy()
        )

    if not categorical_drift_df.empty:
        drift_frames.append(
            categorical_drift_df[
                ["column_name", "drift_type", "drift_level"]
            ].copy()
        )

    if drift_frames:
        all_drift_df = pd.concat(drift_frames, ignore_index=True)
    else:
        all_drift_df = pd.DataFrame(
            columns=["column_name", "drift_type", "drift_level"]
        )

    high_count = int((all_drift_df["drift_level"] == "High drift").sum()) if not all_drift_df.empty else 0
    moderate_count = int((all_drift_df["drift_level"] == "Moderate drift").sum()) if not all_drift_df.empty else 0

    schema_drift_count = (
        schema_report["summary"]["added_columns"]
        + schema_report["summary"]["removed_columns"]
        + schema_report["summary"]["dtype_changes"]
    )

    overall_level = _overall_drift_level(high_count, moderate_count)

    if schema_drift_count > 0 and overall_level == "None":
        overall_level = "Low"
    elif schema_drift_count > 0 and overall_level == "Low":
        overall_level = "Medium"

    total_checked_columns = len(common_columns)
    drifted_columns = int(
        all_drift_df[all_drift_df["drift_level"] != "No significant drift"]["column_name"].nunique()
    ) if not all_drift_df.empty else 0

    drift_rate = round(drifted_columns / max(total_checked_columns, 1) * 100, 2)

    if overall_level == "None":
        drift_score = 100.0
    elif overall_level == "Low":
        drift_score = max(80.0, 100 - drift_rate)
    elif overall_level == "Medium":
        drift_score = max(60.0, 85 - drift_rate)
    else:
        drift_score = max(0.0, 70 - drift_rate * 1.5)

    summary = {
        "baseline_rows": len(baseline_df),
        "current_rows": len(current_df),
        "baseline_columns": len(baseline_df.columns),
        "current_columns": len(current_df.columns),
        "checked_common_columns": total_checked_columns,
        "schema_drift_count": schema_drift_count,
        "drifted_columns": drifted_columns,
        "high_drift_columns": high_count,
        "moderate_drift_columns": moderate_count,
        "drift_rate (%)": drift_rate,
        "overall_drift_level": overall_level,
        "drift_score": round(float(drift_score), 2),
    }

    return {
        "summary": summary,
        "schema_report": schema_report,
        "numeric_drift_df": numeric_drift_df,
        "categorical_drift_df": categorical_drift_df,
        "all_drift_df": all_drift_df,
    }