from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from src.anomaly.anomaly_engine import run_anomaly_detection
from src.scoring.weights import SCORE_LABELS, SCORE_WEIGHTS, validate_weights


def clamp_score(score: float) -> float:
    """
    Giữ điểm trong khoảng 0–100.
    """
    return round(max(0.0, min(100.0, score)), 2)


def calculate_completeness_score(df: pd.DataFrame) -> Dict[str, Any]:
    total_cells = df.shape[0] * df.shape[1]
    missing_cells = int(df.isna().sum().sum())
    missing_rate = missing_cells / max(total_cells, 1)

    score = 100 * (1 - missing_rate)

    return {
        "score_name": "completeness_score",
        "score": clamp_score(score),
        "raw_value": round(missing_rate * 100, 2),
        "detail": f"Dataset có {missing_cells} ô bị thiếu trên tổng {total_cells} ô.",
        "interpretation": "Điểm càng cao nghĩa là dữ liệu càng đầy đủ, ít missing value.",
    }


def calculate_uniqueness_score(df: pd.DataFrame) -> Dict[str, Any]:
    total_rows = len(df)
    duplicate_rows = int(df.duplicated().sum())
    duplicate_rate = duplicate_rows / max(total_rows, 1)

    score = 100 * (1 - duplicate_rate)

    return {
        "score_name": "uniqueness_score",
        "score": clamp_score(score),
        "raw_value": round(duplicate_rate * 100, 2),
        "detail": f"Dataset có {duplicate_rows} dòng trùng lặp hoàn toàn trên tổng {total_rows} dòng.",
        "interpretation": "Điểm càng cao nghĩa là dữ liệu càng ít trùng lặp.",
    }


def calculate_validity_score(df: pd.DataFrame, quality_report: Dict[str, Any]) -> Dict[str, Any]:
    issues_df = quality_report.get("issues_df", pd.DataFrame())

    if issues_df.empty:
        return {
            "score_name": "validity_score",
            "score": 100.0,
            "raw_value": 0.0,
            "detail": "Không phát hiện lỗi validity trong dataset.",
            "interpretation": "Điểm càng cao nghĩa là dữ liệu càng đúng kiểu, đúng miền giá trị và đúng tập giá trị hợp lệ.",
        }

    validity_issue_types = {
        "Invalid Numeric Type",
        "Invalid Datetime Type",
        "Invalid Range",
        "Invalid Age Range",
        "Invalid Categorical Value",
    }

    validity_issues = issues_df[issues_df["issue_type"].isin(validity_issue_types)]

    total_rows = len(df)
    total_columns = len(df.columns)
    total_cells = max(total_rows * total_columns, 1)

    invalid_count = int(validity_issues["issue_count"].sum()) if not validity_issues.empty else 0
    invalid_rate = invalid_count / total_cells

    penalty = invalid_rate * 100 * 3
    score = 100 - penalty

    return {
        "score_name": "validity_score",
        "score": clamp_score(score),
        "raw_value": round(invalid_rate * 100, 2),
        "detail": f"Phát hiện {invalid_count} lỗi liên quan đến kiểu dữ liệu, miền giá trị hoặc categorical value.",
        "interpretation": "Điểm càng cao nghĩa là dữ liệu càng hợp lệ về kiểu, format và miền giá trị.",
    }


def calculate_consistency_score(df: pd.DataFrame, quality_report: Dict[str, Any]) -> Dict[str, Any]:
    issues_df = quality_report.get("issues_df", pd.DataFrame())

    if issues_df.empty:
        return {
            "score_name": "consistency_score",
            "score": 100.0,
            "raw_value": 0.0,
            "detail": "Không phát hiện lỗi consistency trong dataset.",
            "interpretation": "Điểm càng cao nghĩa là dữ liệu càng nhất quán về định dạng và logic cơ bản.",
        }

    consistency_issue_types = {
        "Text Format Inconsistency",
    }

    consistency_issues = issues_df[issues_df["issue_type"].isin(consistency_issue_types)]

    total_rows = len(df)
    total_columns = len(df.columns)
    total_cells = max(total_rows * total_columns, 1)

    consistency_error_count = int(consistency_issues["issue_count"].sum()) if not consistency_issues.empty else 0

    missing_issues = issues_df[issues_df["issue_type"] == "Missing Value"]
    missing_count = int(missing_issues["issue_count"].sum()) if not missing_issues.empty else 0

    weighted_error_count = consistency_error_count + 0.5 * missing_count
    error_rate = weighted_error_count / total_cells

    penalty = error_rate * 100 * 2
    score = 100 - penalty

    return {
        "score_name": "consistency_score",
        "score": clamp_score(score),
        "raw_value": round(error_rate * 100, 2),
        "detail": (
            f"Phát hiện {consistency_error_count} lỗi định dạng/nhất quán "
            f"và {missing_count} missing value được tính phạt nhẹ."
        ),
        "interpretation": "Điểm càng cao nghĩa là dữ liệu càng nhất quán và ít lỗi định dạng.",
    }


def calculate_anomaly_safety_score(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Version 0.6:
    Anomaly Safety Score dùng engine mới gồm IQR, Z-score và Isolation Forest.
    """
    anomaly_report = run_anomaly_detection(df)

    summary = anomaly_report["summary"]
    anomaly_score = summary["anomaly_score"]
    anomaly_rate = summary["anomaly_rate (%)"]
    total_anomaly_rows = summary["total_anomaly_rows"]

    return {
        "score_name": "anomaly_safety_score",
        "score": clamp_score(anomaly_score),
        "raw_value": anomaly_rate,
        "detail": (
            f"Phát hiện {total_anomaly_rows} dòng bất thường bằng tổ hợp "
            "IQR, Z-score và Isolation Forest."
        ),
        "interpretation": "Điểm càng cao nghĩa là dataset càng ít giá trị bất thường.",
        "anomaly_report": anomaly_report,
        "outlier_details_df": anomaly_report["summary_df"],
    }


def calculate_overall_score(score_items: Dict[str, Dict[str, Any]]) -> float:
    validate_weights()

    total_score = 0.0

    for score_name, weight in SCORE_WEIGHTS.items():
        total_score += score_items[score_name]["score"] * weight

    return clamp_score(total_score)


def get_risk_level(overall_score: float) -> str:
    if overall_score >= 85:
        return "Low"
    if overall_score >= 70:
        return "Medium"
    if overall_score >= 50:
        return "High"
    return "Critical"


def get_ai_readiness(overall_score: float) -> str:
    if overall_score >= 85:
        return "Ready for Analytics and ML"
    if overall_score >= 70:
        return "Usable, Minor Cleaning Needed"
    if overall_score >= 50:
        return "Needs Cleaning Before Training"
    return "Not Ready for AI/ML"


def get_score_conclusion(overall_score: float, risk_level: str, ai_readiness: str) -> str:
    if overall_score >= 85:
        return (
            "Dataset có chất lượng tốt, ít lỗi nghiêm trọng và có thể sử dụng "
            "cho phân tích hoặc huấn luyện mô hình sau các bước kiểm tra nghiệp vụ bổ sung."
        )

    if overall_score >= 70:
        return (
            "Dataset ở mức khá. Có thể sử dụng cho phân tích sơ bộ, nhưng nên xử lý "
            "các lỗi còn tồn tại trước khi dùng trong môi trường chính thức."
        )

    if overall_score >= 50:
        return (
            "Dataset có nhiều vấn đề chất lượng. Cần làm sạch missing value, lỗi kiểu dữ liệu, "
            "duplicate hoặc outlier trước khi huấn luyện mô hình AI/ML."
        )

    return (
        "Dataset có rủi ro chất lượng cao. Không nên sử dụng trực tiếp cho phân tích "
        "hoặc mô hình AI/ML nếu chưa xử lý dữ liệu nghiêm túc."
    )


def build_score_breakdown_df(score_items: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for score_name, item in score_items.items():
        rows.append(
            {
                "score_key": score_name,
                "score_name": SCORE_LABELS.get(score_name, score_name),
                "score": item["score"],
                "weight": SCORE_WEIGHTS.get(score_name, 0),
                "weighted_score": round(item["score"] * SCORE_WEIGHTS.get(score_name, 0), 2),
                "raw_value (%)": item["raw_value"],
                "detail": item["detail"],
                "interpretation": item["interpretation"],
            }
        )

    return pd.DataFrame(rows)


def calculate_data_trust_score(
    df: pd.DataFrame,
    quality_report: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if quality_report is None:
        quality_report = {"issues_df": pd.DataFrame()}

    completeness = calculate_completeness_score(df)
    validity = calculate_validity_score(df, quality_report)
    uniqueness = calculate_uniqueness_score(df)
    consistency = calculate_consistency_score(df, quality_report)
    anomaly_safety = calculate_anomaly_safety_score(df)

    score_items = {
        "completeness_score": completeness,
        "validity_score": validity,
        "uniqueness_score": uniqueness,
        "consistency_score": consistency,
        "anomaly_safety_score": anomaly_safety,
    }

    overall_score = calculate_overall_score(score_items)
    risk_level = get_risk_level(overall_score)
    ai_readiness = get_ai_readiness(overall_score)
    conclusion = get_score_conclusion(overall_score, risk_level, ai_readiness)

    breakdown_df = build_score_breakdown_df(score_items)

    anomaly_report = anomaly_safety.get("anomaly_report", {})

    return {
        "overall_score": overall_score,
        "risk_level": risk_level,
        "ai_readiness": ai_readiness,
        "conclusion": conclusion,
        "score_items": score_items,
        "breakdown_df": breakdown_df,
        "outlier_details_df": anomaly_safety.get("outlier_details_df", pd.DataFrame()),
        "anomaly_report": anomaly_report,
    }