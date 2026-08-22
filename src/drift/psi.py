from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def interpret_psi(psi_value: float) -> str:
    if psi_value < 0.1:
        return "No significant drift"
    if psi_value < 0.25:
        return "Moderate drift"
    return "High drift"


def calculate_psi(
    baseline_series: pd.Series,
    current_series: pd.Series,
    bins: int = 10,
) -> Dict[str, Any]:
    baseline_numeric = pd.to_numeric(baseline_series, errors="coerce").dropna()
    current_numeric = pd.to_numeric(current_series, errors="coerce").dropna()

    if baseline_numeric.empty or current_numeric.empty:
        return {
            "psi": 0.0,
            "interpretation": "Not enough numeric data",
            "details_df": pd.DataFrame(),
        }

    quantiles = np.linspace(0, 1, bins + 1)
    breakpoints = np.unique(baseline_numeric.quantile(quantiles).values)

    if len(breakpoints) < 3:
        min_value = min(baseline_numeric.min(), current_numeric.min())
        max_value = max(baseline_numeric.max(), current_numeric.max())

        if min_value == max_value:
            return {
                "psi": 0.0,
                "interpretation": "Constant distribution",
                "details_df": pd.DataFrame(),
            }

        breakpoints = np.linspace(min_value, max_value, bins + 1)

    baseline_counts, bin_edges = np.histogram(baseline_numeric, bins=breakpoints)
    current_counts, _ = np.histogram(current_numeric, bins=bin_edges)

    baseline_pct = baseline_counts / max(baseline_counts.sum(), 1)
    current_pct = current_counts / max(current_counts.sum(), 1)

    epsilon = 1e-6
    baseline_pct_safe = np.where(baseline_pct == 0, epsilon, baseline_pct)
    current_pct_safe = np.where(current_pct == 0, epsilon, current_pct)

    psi_values = (current_pct_safe - baseline_pct_safe) * np.log(
        current_pct_safe / baseline_pct_safe
    )

    psi_score = float(np.sum(psi_values))

    details_df = pd.DataFrame(
        {
            "bin_start": bin_edges[:-1],
            "bin_end": bin_edges[1:],
            "baseline_count": baseline_counts,
            "current_count": current_counts,
            "baseline_pct": baseline_pct.round(4),
            "current_pct": current_pct.round(4),
            "psi_component": psi_values.round(6),
        }
    )

    return {
        "psi": round(psi_score, 4),
        "interpretation": interpret_psi(psi_score),
        "details_df": details_df,
    }