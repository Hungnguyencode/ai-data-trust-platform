from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def compare_schema(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
) -> Dict[str, Any]:
    baseline_columns = set(baseline_df.columns)
    current_columns = set(current_df.columns)

    added_columns = sorted(current_columns - baseline_columns)
    removed_columns = sorted(baseline_columns - current_columns)
    common_columns = sorted(baseline_columns & current_columns)

    dtype_changes: List[Dict[str, Any]] = []

    for col in common_columns:
        baseline_dtype = str(baseline_df[col].dtype)
        current_dtype = str(current_df[col].dtype)

        if baseline_dtype != current_dtype:
            dtype_changes.append(
                {
                    "column_name": col,
                    "baseline_dtype": baseline_dtype,
                    "current_dtype": current_dtype,
                }
            )

    schema_drift_detected = (
        len(added_columns) > 0
        or len(removed_columns) > 0
        or len(dtype_changes) > 0
    )

    summary = {
        "baseline_columns": len(baseline_columns),
        "current_columns": len(current_columns),
        "common_columns": len(common_columns),
        "added_columns": len(added_columns),
        "removed_columns": len(removed_columns),
        "dtype_changes": len(dtype_changes),
        "schema_drift_detected": schema_drift_detected,
    }

    changes_df = pd.DataFrame(
        [
            {
                "change_type": "Added Column",
                "column_name": col,
                "baseline_dtype": None,
                "current_dtype": str(current_df[col].dtype),
            }
            for col in added_columns
        ]
        + [
            {
                "change_type": "Removed Column",
                "column_name": col,
                "baseline_dtype": str(baseline_df[col].dtype),
                "current_dtype": None,
            }
            for col in removed_columns
        ]
        + [
            {
                "change_type": "Dtype Changed",
                "column_name": item["column_name"],
                "baseline_dtype": item["baseline_dtype"],
                "current_dtype": item["current_dtype"],
            }
            for item in dtype_changes
        ]
    )

    return {
        "summary": summary,
        "added_columns": added_columns,
        "removed_columns": removed_columns,
        "common_columns": common_columns,
        "dtype_changes": dtype_changes,
        "changes_df": changes_df,
    }