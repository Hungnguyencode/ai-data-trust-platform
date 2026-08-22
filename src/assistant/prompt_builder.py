from typing import Any, Dict, List


def has_value(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, dict):
        return len(value) > 0

    if isinstance(value, list):
        return len(value) > 0

    try:
        import pandas as pd

        if isinstance(value, pd.DataFrame):
            return not value.empty
    except Exception:
        pass

    return True


def build_available_result_names(context: Dict[str, Any]) -> List[str]:
    result_map = {
        "dataset": "Dataset",
        "profile": "Data Profile",
        "quality": "Quality Issues",
        "trust_score": "Trust Score",
        "anomaly": "Anomaly Detection",
        "privacy": "Privacy Risk",
        "drift": "Drift Detection",
    }

    available = []

    for key, label in result_map.items():
        if has_value(context.get(key)):
            available.append(label)

    return available


def build_missing_result_names(context: Dict[str, Any]) -> List[str]:
    result_map = {
        "dataset": "Dataset",
        "profile": "Data Profile",
        "quality": "Quality Issues",
        "trust_score": "Trust Score",
        "anomaly": "Anomaly Detection",
        "privacy": "Privacy Risk",
        "drift": "Drift Detection",
    }

    missing = []

    for key, label in result_map.items():
        if not has_value(context.get(key)):
            missing.append(label)

    return missing


def build_grounding_notice(context: Dict[str, Any]) -> str:
    available = build_available_result_names(context)
    missing = build_missing_result_names(context)

    available_text = ", ".join(available) if available else "chưa có dữ liệu"
    missing_text = ", ".join(missing) if missing else "không thiếu phần nào"

    return (
        f"Assistant hiện có dữ liệu từ: {available_text}. "
        f"Các phần chưa có/chưa chạy: {missing_text}."
    )


def build_context_summary(context: Dict[str, Any]) -> Dict[str, Any]:
    dataset = context.get("dataset", {}) or {}
    trust_score = context.get("trust_score", {}) or {}
    quality = context.get("quality", {}) or {}
    anomaly = context.get("anomaly", {}) or {}
    privacy = context.get("privacy", {}) or {}
    drift = context.get("drift", {}) or {}

    return {
        "dataset_name": dataset.get("file_name", "N/A"),
        "rows": dataset.get("total_rows", "N/A"),
        "columns": dataset.get("total_columns", "N/A"),
        "overall_score": trust_score.get("overall_score", "N/A"),
        "risk_level": trust_score.get("risk_level", "N/A"),
        "ai_readiness": trust_score.get("ai_readiness", "N/A"),
        "total_quality_issues": quality.get("total_issues", "N/A"),
        "anomaly_score": anomaly.get("anomaly_score", "N/A"),
        "privacy_score": privacy.get("privacy_safety_score", "N/A"),
        "drift_score": drift.get("drift_score", "N/A"),
    }