from __future__ import annotations


SCORE_WEIGHTS = {
    "completeness_score": 0.25,
    "validity_score": 0.25,
    "uniqueness_score": 0.20,
    "consistency_score": 0.15,
    "anomaly_safety_score": 0.15,
}


SCORE_LABELS = {
    "completeness_score": "Completeness",
    "validity_score": "Validity",
    "uniqueness_score": "Uniqueness",
    "consistency_score": "Consistency",
    "anomaly_safety_score": "Anomaly Safety",
}


def validate_weights() -> None:
    """
    Kiểm tra tổng trọng số có bằng 1.0 không.
    """
    total_weight = sum(SCORE_WEIGHTS.values())

    if round(total_weight, 4) != 1.0:
        raise ValueError(
            f"Tổng trọng số phải bằng 1.0, hiện tại = {total_weight}"
        )