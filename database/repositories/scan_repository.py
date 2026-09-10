from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from sqlalchemy import text

from database.db import get_engine


def save_dataset_metadata(
    file_name: str,
    file_type: str,
    df: pd.DataFrame,
    profile: Dict[str, Any],
) -> int:
    """
    Lưu metadata dataset vào bảng datasets.
    """
    basic_info = profile["basic_info"]

    query = text(
        """
        INSERT INTO datasets (
            file_name,
            file_type,
            total_rows,
            total_columns,
            total_cells,
            missing_cells,
            duplicate_rows
        )
        OUTPUT INSERTED.dataset_id
        VALUES (
            :file_name,
            :file_type,
            :total_rows,
            :total_columns,
            :total_cells,
            :missing_cells,
            :duplicate_rows
        );
        """
    )

    engine = get_engine()

    with engine.begin() as conn:
        dataset_id = conn.execute(
            query,
            {
                "file_name": file_name,
                "file_type": file_type,
                "total_rows": int(basic_info["total_rows"]),
                "total_columns": int(basic_info["total_columns"]),
                "total_cells": int(basic_info["total_cells"]),
                "missing_cells": int(basic_info["missing_cells"]),
                "duplicate_rows": int(basic_info["duplicate_rows"]),
            },
        ).scalar_one()

    return int(dataset_id)


def save_scan_run(dataset_id: int, quality_report: Dict[str, Any]) -> int:
    """
    Lưu một lần scan vào bảng scan_runs.
    """
    summary = quality_report["summary"]

    query = text(
        """
        INSERT INTO scan_runs (
            dataset_id,
            scan_status,
            total_issues,
            high_issues,
            medium_issues,
            low_issues,
            affected_columns
        )
        OUTPUT INSERTED.scan_id
        VALUES (
            :dataset_id,
            :scan_status,
            :total_issues,
            :high_issues,
            :medium_issues,
            :low_issues,
            :affected_columns
        );
        """
    )

    engine = get_engine()

    with engine.begin() as conn:
        scan_id = conn.execute(
            query,
            {
                "dataset_id": int(dataset_id),
                "scan_status": "completed",
                "total_issues": int(summary["total_issues"]),
                "high_issues": int(summary["high_issues"]),
                "medium_issues": int(summary["medium_issues"]),
                "low_issues": int(summary["low_issues"]),
                "affected_columns": int(summary["affected_columns"]),
            },
        ).scalar_one()

    return int(scan_id)


def save_trust_score(scan_id: int, trust_score_report: Dict[str, Any]) -> int:
    """
    Lưu Data Trust Score vào bảng trust_scores.
    """
    score_items = trust_score_report["score_items"]

    query = text(
        """
        INSERT INTO trust_scores (
            scan_id,
            overall_score,
            risk_level,
            ai_readiness,
            completeness_score,
            validity_score,
            uniqueness_score,
            consistency_score,
            anomaly_safety_score
        )
        OUTPUT INSERTED.score_id
        VALUES (
            :scan_id,
            :overall_score,
            :risk_level,
            :ai_readiness,
            :completeness_score,
            :validity_score,
            :uniqueness_score,
            :consistency_score,
            :anomaly_safety_score
        );
        """
    )

    engine = get_engine()

    with engine.begin() as conn:
        score_id = conn.execute(
            query,
            {
                "scan_id": int(scan_id),
                "overall_score": float(trust_score_report["overall_score"]),
                "risk_level": trust_score_report["risk_level"],
                "ai_readiness": trust_score_report["ai_readiness"],
                "completeness_score": float(score_items["completeness_score"]["score"]),
                "validity_score": float(score_items["validity_score"]["score"]),
                "uniqueness_score": float(score_items["uniqueness_score"]["score"]),
                "consistency_score": float(score_items["consistency_score"]["score"]),
                "anomaly_safety_score": float(score_items["anomaly_safety_score"]["score"]),
            },
        ).scalar_one()

    return int(score_id)


def save_quality_issues(scan_id: int, quality_report: Dict[str, Any]) -> int:
    """
    Lưu danh sách quality issues vào bảng quality_issues.
    """
    issues_df = quality_report["issues_df"]

    if issues_df.empty:
        return 0

    query = text(
        """
        INSERT INTO quality_issues (
            scan_id,
            issue_type,
            column_name,
            severity,
            issue_count,
            issue_rate,
            description,
            recommendation
        )
        VALUES (
            :scan_id,
            :issue_type,
            :column_name,
            :severity,
            :issue_count,
            :issue_rate,
            :description,
            :recommendation
        );
        """
    )

    records = []

    for _, row in issues_df.iterrows():
        records.append(
            {
                "scan_id": int(scan_id),
                "issue_type": str(row["issue_type"]),
                "column_name": str(row["column_name"]),
                "severity": str(row["severity"]),
                "issue_count": int(row["issue_count"]),
                "issue_rate": float(row["issue_rate (%)"]),
                "description": str(row["description"]),
                "recommendation": str(row["recommendation"]),
            }
        )

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(query, records)

    return len(records)


def save_full_scan(
    file_name: str,
    file_type: str,
    df: pd.DataFrame,
    profile: Dict[str, Any],
    quality_report: Dict[str, Any],
    trust_score_report: Dict[str, Any],
) -> Dict[str, int]:
    """
    Lưu toàn bộ kết quả scan:
    - dataset metadata
    - scan run
    - trust score
    - quality issues
    """
    dataset_id = save_dataset_metadata(file_name, file_type, df, profile)
    scan_id = save_scan_run(dataset_id, quality_report)
    score_id = save_trust_score(scan_id, trust_score_report)
    issue_count = save_quality_issues(scan_id, quality_report)

    return {
        "dataset_id": dataset_id,
        "scan_id": scan_id,
        "score_id": score_id,
        "saved_issues": issue_count,
    }


def get_scan_history(limit: int = 50) -> pd.DataFrame:
    """
    Lấy lịch sử scan gần nhất.
    """
    safe_limit = max(1, min(int(limit), 1000))

    query = text(
        f"""
        SELECT TOP {safe_limit}
            sr.scan_id,
            d.dataset_id,
            d.file_name,
            d.file_type,
            d.total_rows,
            d.total_columns,
            d.missing_cells,
            d.duplicate_rows,
            sr.total_issues,
            sr.high_issues,
            sr.medium_issues,
            sr.low_issues,
            sr.affected_columns,
            ts.overall_score,
            ts.risk_level,
            ts.ai_readiness,
            sr.created_at
        FROM scan_runs sr
        INNER JOIN datasets d
            ON sr.dataset_id = d.dataset_id
        LEFT JOIN trust_scores ts
            ON sr.scan_id = ts.scan_id
        ORDER BY sr.created_at DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)

    return df


def get_scan_by_id(scan_id: int) -> pd.DataFrame:
    """
    Load one persisted scan with dataset metadata and Trust Score.
    """

    query = text(
        """
        SELECT
            sr.scan_id,
            d.dataset_id,
            d.file_name,
            d.file_type,
            d.total_rows,
            d.total_columns,
            d.missing_cells,
            d.duplicate_rows,
            sr.total_issues,
            sr.high_issues,
            sr.medium_issues,
            sr.low_issues,
            sr.affected_columns,
            ts.overall_score,
            ts.risk_level,
            ts.ai_readiness,
            sr.created_at
        FROM scan_runs sr
        INNER JOIN datasets d
            ON sr.dataset_id = d.dataset_id
        LEFT JOIN trust_scores ts
            ON sr.scan_id = ts.scan_id
        WHERE sr.scan_id = :scan_id;
        """
    )

    engine = get_engine()

    with engine.connect() as conn:
        df = pd.read_sql_query(
            query,
            conn,
            params={
                "scan_id": int(scan_id),
            },
        )

    return df


def get_quality_issues_by_scan(scan_id: int) -> pd.DataFrame:
    """
    Lấy quality issues theo scan_id.
    """
    query = text(
        """
        SELECT
            issue_id,
            scan_id,
            issue_type,
            column_name,
            severity,
            issue_count,
            issue_rate,
            description,
            recommendation,
            created_at
        FROM quality_issues
        WHERE scan_id = :scan_id
        ORDER BY
            CASE severity
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
                ELSE 4
            END,
            issue_count DESC;
        """
    )

    engine = get_engine()

    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn, params={"scan_id": int(scan_id)})

    return df