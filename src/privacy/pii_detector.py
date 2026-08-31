from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from src.privacy.regex_patterns import (
    ADDRESS_COLUMN_KEYWORDS,
    ADDRESS_REGEX_PATTERN,
    CITIZEN_ID_COLUMN_KEYWORDS,
    CITIZEN_ID_PATTERN,
    EMAIL_COLUMN_KEYWORDS,
    EMAIL_PATTERN,
    NAME_COLUMN_KEYWORDS,
    PHONE_COLUMN_KEYWORDS,
    PHONE_PATTERN,
)


def _contains_keyword(column_name: str, keywords: List[str]) -> bool:
    lower_name = column_name.lower().strip()
    return any(keyword.lower() in lower_name for keyword in keywords)


def _safe_string_series(series: pd.Series) -> pd.Series:
    return series.dropna().astype(str)


def _risk_level_from_score(score: float) -> str:
    if score >= 90:
        return "Low"
    if score >= 75:
        return "Medium"
    if score >= 50:
        return "High"
    return "Critical"


def _severity_from_pii_type(pii_type: str, match_rate: float) -> str:
    high_risk_types = {"Citizen ID", "Phone Number", "Email"}
    medium_risk_types = {"Full Name", "Address"}

    if pii_type in high_risk_types:
        if match_rate >= 20:
            return "High"
        return "Medium"

    if pii_type in medium_risk_types:
        if match_rate >= 30:
            return "High"
        return "Medium"

    return "Low"


def _mask_value(value: Any, pii_type: str) -> str:
    if pd.isna(value):
        return ""

    text = str(value)

    if pii_type == "Email":
        if "@" not in text:
            return "***"
        prefix, domain = text.split("@", 1)
        return f"{prefix[:2]}***@{domain}"

    if pii_type == "Phone Number":
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) <= 4:
            return "***"
        return f"***{digits[-4:]}"

    if pii_type == "Citizen ID":
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) <= 4:
            return "***"
        return f"***{digits[-4:]}"

    if pii_type == "Full Name":
        parts = text.strip().split()
        if not parts:
            return "***"
        return f"{parts[0][0]}***"

    if pii_type == "Address":
        return text[:8] + "***" if len(text) > 8 else "***"

    return "***"


def detect_email_column(df: pd.DataFrame, col: str) -> Dict[str, Any] | None:
    series = _safe_string_series(df[col])
    if series.empty:
        return None

    regex_mask = series.str.contains(EMAIL_PATTERN, regex=True, na=False)
    name_hint = _contains_keyword(col, EMAIL_COLUMN_KEYWORDS)

    match_count = int(regex_mask.sum())
    if name_hint:
        match_count = max(match_count, int(series.notna().sum()))

    if match_count <= 0:
        return None

    match_rate = round(match_count / max(len(df), 1) * 100, 2)

    examples = [
        _mask_value(v, "Email")
        for v in series[regex_mask].head(3).tolist()
    ]

    if name_hint and not examples:
        examples = [
            _mask_value(v, "Email")
            for v in series.head(3).tolist()
        ]

    return {
        "pii_type": "Email",
        "column_name": col,
        "match_count": match_count,
        "match_rate (%)": match_rate,
        "severity": _severity_from_pii_type("Email", match_rate),
        "detection_method": "regex + column name heuristic",
        "masked_examples": ", ".join(examples),
        "recommendation": "Mask hoặc hash email trước khi chia sẻ dữ liệu; chỉ giữ domain nếu cần phân tích.",
    }


def detect_phone_column(df: pd.DataFrame, col: str) -> Dict[str, Any] | None:
    series = _safe_string_series(df[col])
    if series.empty:
        return None

    regex_mask = series.str.contains(PHONE_PATTERN, regex=True, na=False)
    name_hint = _contains_keyword(col, PHONE_COLUMN_KEYWORDS)

    match_count = int(regex_mask.sum())
    if name_hint:
        match_count = max(match_count, int(series.notna().sum()))

    if match_count <= 0:
        return None

    match_rate = round(match_count / max(len(df), 1) * 100, 2)

    examples = [
        _mask_value(v, "Phone Number")
        for v in series[regex_mask].head(3).tolist()
    ]

    if name_hint and not examples:
        examples = [
            _mask_value(v, "Phone Number")
            for v in series.head(3).tolist()
        ]

    return {
        "pii_type": "Phone Number",
        "column_name": col,
        "match_count": match_count,
        "match_rate (%)": match_rate,
        "severity": _severity_from_pii_type("Phone Number", match_rate),
        "detection_method": "regex + column name heuristic",
        "masked_examples": ", ".join(examples),
        "recommendation": "Ẩn một phần số điện thoại hoặc loại bỏ trước khi public dataset.",
    }


def detect_citizen_id_column(df: pd.DataFrame, col: str) -> Dict[str, Any] | None:
    series = _safe_string_series(df[col])
    if series.empty:
        return None

    regex_mask = series.str.fullmatch(CITIZEN_ID_PATTERN, na=False)
    name_hint = _contains_keyword(col, CITIZEN_ID_COLUMN_KEYWORDS)

    match_count = int(regex_mask.sum())
    if name_hint:
        match_count = max(match_count, int(series.notna().sum()))

    if match_count <= 0:
        return None

    match_rate = round(match_count / max(len(df), 1) * 100, 2)

    examples = [
        _mask_value(v, "Citizen ID")
        for v in series[regex_mask].head(3).tolist()
    ]

    if name_hint and not examples:
        examples = [
            _mask_value(v, "Citizen ID")
            for v in series.head(3).tolist()
        ]

    return {
        "pii_type": "Citizen ID",
        "column_name": col,
        "match_count": match_count,
        "match_rate (%)": match_rate,
        "severity": "High",
        "detection_method": "regex + column name heuristic",
        "masked_examples": ", ".join(examples),
        "recommendation": "Không lưu hoặc chia sẻ CCCD/CMND dạng plain text. Nên mã hóa, hash hoặc loại bỏ.",
    }


def detect_full_name_column(df: pd.DataFrame, col: str) -> Dict[str, Any] | None:
    series = _safe_string_series(df[col])
    if series.empty:
        return None

    name_hint = _contains_keyword(col, NAME_COLUMN_KEYWORDS)

    if not name_hint:
        return None

    valid_name_mask = series.str.strip().str.len() >= 2
    match_count = int(valid_name_mask.sum())

    if match_count <= 0:
        return None

    match_rate = round(match_count / max(len(df), 1) * 100, 2)

    examples = [
        _mask_value(v, "Full Name")
        for v in series[valid_name_mask].head(3).tolist()
    ]

    return {
        "pii_type": "Full Name",
        "column_name": col,
        "match_count": match_count,
        "match_rate (%)": match_rate,
        "severity": _severity_from_pii_type("Full Name", match_rate),
        "detection_method": "column name heuristic",
        "masked_examples": ", ".join(examples),
        "recommendation": "Cân nhắc pseudonymize tên người dùng nếu không cần định danh trực tiếp.",
    }


def detect_address_column(df: pd.DataFrame, col: str) -> Dict[str, Any] | None:
    series = _safe_string_series(df[col])
    if series.empty:
        return None

    name_hint = _contains_keyword(col, ADDRESS_COLUMN_KEYWORDS)

    regex_mask = series.str.contains(ADDRESS_REGEX_PATTERN, regex=True, na=False)

    # Chỉ coi là address nếu:
    # 1. Tên cột gợi ý rõ là địa chỉ, hoặc
    # 2. Giá trị có pattern địa chỉ rõ ràng.
    match_count = int(regex_mask.sum())

    if name_hint:
        match_count = max(match_count, int(series.notna().sum()))

    if match_count <= 0:
        return None

    match_rate = round(match_count / max(len(df), 1) * 100, 2)

    examples = [
        _mask_value(v, "Address")
        for v in series[regex_mask].head(3).tolist()
    ]

    if name_hint and not examples:
        examples = [
            _mask_value(v, "Address")
            for v in series.head(3).tolist()
        ]

    return {
        "pii_type": "Address",
        "column_name": col,
        "match_count": match_count,
        "match_rate (%)": match_rate,
        "severity": _severity_from_pii_type("Address", match_rate),
        "detection_method": "address regex + column name heuristic",
        "masked_examples": ", ".join(examples),
        "recommendation": "Ẩn địa chỉ chi tiết; chỉ giữ cấp tỉnh/thành phố nếu đủ cho phân tích.",
    }


def calculate_privacy_safety_score(pii_findings_df: pd.DataFrame, total_cells: int) -> float:
    if pii_findings_df.empty:
        return 100.0

    weighted_risk = 0.0

    severity_weights = {
        "Low": 0.6,
        "Medium": 1.0,
        "High": 1.8,
        "Critical": 2.5,
    }

    for _, row in pii_findings_df.iterrows():
        severity = str(row["severity"])
        match_count = float(row["match_count"])
        weighted_risk += match_count * severity_weights.get(severity, 1.0)

    risk_rate = weighted_risk / max(total_cells, 1)
    score = 100 - risk_rate * 100

    return round(max(0.0, min(100.0, score)), 2)


def run_privacy_scan(df: pd.DataFrame) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []

    for col in df.columns:
        detectors = [
            detect_email_column,
            detect_phone_column,
            detect_citizen_id_column,
            detect_full_name_column,
            detect_address_column,
        ]

        for detector in detectors:
            result = detector(df, col)
            if result is not None:
                findings.append(result)

    findings_df = pd.DataFrame(findings)

    total_rows = len(df)
    total_columns = len(df.columns)
    total_cells = total_rows * total_columns

    if findings_df.empty:
        privacy_score = 100.0
        risk_level = "Low"
        pii_columns = 0
        pii_cells = 0
        high_risk_findings = 0
    else:
        pii_columns = int(findings_df["column_name"].nunique())
        pii_cells = int(findings_df["match_count"].sum())
        privacy_score = calculate_privacy_safety_score(findings_df, total_cells)
        risk_level = _risk_level_from_score(privacy_score)
        high_risk_findings = int(findings_df["severity"].isin(["High", "Critical"]).sum())

        severity_order = {"High": 0, "Medium": 1, "Low": 2, "Critical": -1}
        findings_df["severity_order"] = findings_df["severity"].map(severity_order).fillna(9)
        findings_df = (
            findings_df.sort_values(
                by=["severity_order", "match_rate (%)", "match_count"],
                ascending=[True, False, False],
            )
            .drop(columns=["severity_order"])
            .reset_index(drop=True)
        )

    summary = {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "total_cells": total_cells,
        "pii_columns": pii_columns,
        "pii_cells": pii_cells,
        "pii_cell_rate (%)": round(pii_cells / max(total_cells, 1) * 100, 2),
        "privacy_safety_score": privacy_score,
        "risk_level": risk_level,
        "high_risk_findings": high_risk_findings,
    }

    return {
        "summary": summary,
        "findings_df": findings_df,
    }