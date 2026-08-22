from __future__ import annotations

from typing import Any, Dict, List


def _fmt(value: Any, default: str = "N/A") -> str:
    if value is None:
        return default
    if value == "":
        return default
    return str(value)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "N/A":
            return default
        return float(value)
    except Exception:
        return default


def _records(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _priority_score(severity: str, issue_type: str = "", source: str = "") -> int:
    severity = str(severity or "").lower()
    issue_type = str(issue_type or "").lower()
    source = str(source or "").lower()

    score = 0

    if severity == "critical":
        score += 100
    elif severity == "high":
        score += 80
    elif severity == "medium":
        score += 50
    elif severity == "low":
        score += 20

    if source == "Privacy Risk":
        score += 30

    if "citizen" in issue_type or "phone" in issue_type or "email" in issue_type:
        score += 25

    if "missing" in issue_type:
        score += 15

    if "duplicate" in issue_type:
        score += 12

    if "invalid" in issue_type:
        score += 10

    if "drift" in issue_type:
        score += 8

    return score


def _suggest_action(source: str, issue_type: str, column_name: str) -> str:
    source_l = source.lower()
    issue_l = issue_type.lower()
    col_l = column_name.lower()

    if source == "Privacy Risk":
        if "email" in issue_l or "email" in col_l:
            return "Mask/hash email; nếu chỉ cần phân tích domain thì tách domain và bỏ local-part."
        if "phone" in issue_l or "phone" in col_l:
            return "Mask số điện thoại, chỉ giữ 3–4 số cuối nếu cần đối soát."
        if "citizen" in issue_l or "cccd" in col_l or "cmnd" in col_l:
            return "Không public plain text; hash/mã hóa hoặc loại bỏ khỏi dataset."
        if "name" in issue_l or "name" in col_l:
            return "Pseudonymize tên; thay bằng mã khách hàng ẩn danh."
        if "address" in issue_l or "address" in col_l:
            return "Ẩn địa chỉ chi tiết; chỉ giữ cấp tỉnh/thành phố nếu đủ cho phân tích."
        return "Ẩn danh hóa trường PII trước khi chia sẻ hoặc training."

    if source == "Quality Issues":
        if "missing" in issue_l:
            return "Kiểm tra nguyên nhân thiếu; numeric dùng median/mean, categorical dùng mode/Unknown tùy nghiệp vụ."
        if "duplicate" in issue_l:
            return "Kiểm tra khóa định danh; nếu là duplicate thật thì drop_duplicates()."
        if "numeric type" in issue_l:
            return "Chuẩn hóa kiểu số; ép kiểu bằng pd.to_numeric(errors='coerce'), sau đó xử lý giá trị lỗi."
        if "datetime" in issue_l:
            return "Chuẩn hóa format ngày tháng, ví dụ YYYY-MM-DD, rồi parse lại datetime."
        if "range" in issue_l:
            return "Kiểm tra miền giá trị; giá trị âm hoặc quá lớn cần sửa, winsorize hoặc đưa thành missing."
        if "categorical" in issue_l:
            return "Chuẩn hóa tập nhãn hợp lệ, map giá trị sai về nhóm chuẩn hoặc Unknown."
        if "text format" in issue_l:
            return "Trim khoảng trắng, chuẩn hóa viết hoa/thường và ký tự đặc biệt."
        return "Xử lý theo recommendation của quality rule, sau đó chạy lại Quality Issues."

    if source == "Drift Detection":
        return "So sánh với baseline; kiểm tra nguyên nhân phân phối thay đổi trước khi dùng current dataset."

    if source == "Anomaly Detection":
        return "Kiểm tra dòng bất thường; nếu lỗi nhập liệu thì sửa/xóa, nếu là giá trị thật thì cân nhắc giữ hoặc winsorize."

    return "Kiểm tra nghiệp vụ và xử lý trước khi dùng dataset chính thức."


def _reason_text(source: str, issue_type: str, severity: str, count: Any, rate: Any) -> str:
    if source == "Privacy Risk":
        return (
            f"Phát hiện {issue_type}, severity={severity}, "
            f"match_count={_fmt(count)}, match_rate={_fmt(rate)}%."
        )

    if source == "Quality Issues":
        return (
            f"Phát hiện {issue_type}, severity={severity}, "
            f"issue_count={_fmt(count)}, issue_rate={_fmt(rate)}%."
        )

    if source == "Drift Detection":
        return f"Cột có drift_level={severity}; cần kiểm tra thay đổi phân phối."

    if source == "Anomaly Detection":
        return f"Có anomaly/outlier trong dataset; cần kiểm tra dòng bất thường trước khi training."

    return "Có dấu hiệu rủi ro trong scan context."


def build_cleaning_plan_records(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Sinh cleaning plan theo từng cột dựa trên scan context.

    Nguồn dữ liệu:
    - quality.issues
    - privacy.findings
    - drift.drifted_columns_detail
    - anomaly summary, nếu có anomaly thì thêm task cấp row-level
    """

    plan: List[Dict[str, Any]] = []

    quality = context.get("quality", {}) or {}
    privacy = context.get("privacy", {}) or {}
    drift = context.get("drift", {}) or {}
    anomaly = context.get("anomaly", {}) or {}

    # 1. Quality Issues
    for item in _records(quality.get("issues")):
        issue_type = _fmt(item.get("issue_type"))
        column_name = _fmt(item.get("column_name"))
        severity = _fmt(item.get("severity"))
        count = item.get("issue_count")
        rate = item.get("issue_rate (%)")

        display_col = "row-level" if column_name == "__row__" else column_name

        plan.append(
            {
                "priority_score": _priority_score(severity, issue_type, "Quality Issues"),
                "source": "Quality Issues",
                "column_name": display_col,
                "problem": issue_type,
                "severity": severity,
                "evidence": _reason_text("Quality Issues", issue_type, severity, count, rate),
                "suggested_action": _suggest_action("Quality Issues", issue_type, display_col),
            }
        )

    # 2. Privacy Findings
    for item in _records(privacy.get("findings")):
        pii_type = _fmt(item.get("pii_type"))
        column_name = _fmt(item.get("column_name"))
        severity = _fmt(item.get("severity"))
        count = item.get("match_count")
        rate = item.get("match_rate (%)")

        plan.append(
            {
                "priority_score": _priority_score(severity, pii_type, "Privacy Risk"),
                "source": "Privacy Risk",
                "column_name": column_name,
                "problem": pii_type,
                "severity": severity,
                "evidence": _reason_text("Privacy Risk", pii_type, severity, count, rate),
                "suggested_action": _suggest_action("Privacy Risk", pii_type, column_name),
            }
        )

    # 3. Drift Detection
    for item in _records(drift.get("drifted_columns_detail")):
        column_name = _fmt(item.get("column_name"))
        drift_type = _fmt(item.get("drift_type"))
        drift_level = _fmt(item.get("drift_level"))

        if drift_level in {"No significant drift", "None", "N/A"}:
            continue

        plan.append(
            {
                "priority_score": _priority_score(drift_level, "Drift", "Drift Detection"),
                "source": "Drift Detection",
                "column_name": column_name,
                "problem": drift_type,
                "severity": drift_level,
                "evidence": _reason_text("Drift Detection", drift_type, drift_level, None, None),
                "suggested_action": _suggest_action("Drift Detection", drift_type, column_name),
            }
        )

    # 4. Anomaly Detection row-level
    anomaly_rows = _safe_float(anomaly.get("total_anomaly_rows"), 0.0)
    anomaly_rate = _safe_float(anomaly.get("anomaly_rate"), 0.0)
    anomaly_risk = _fmt(anomaly.get("risk_level"), "N/A")

    if anomaly_rows > 0:
        plan.append(
            {
                "priority_score": _priority_score(anomaly_risk, "Anomaly", "Anomaly Detection"),
                "source": "Anomaly Detection",
                "column_name": "row-level",
                "problem": "Anomaly / Outlier",
                "severity": anomaly_risk,
                "evidence": (
                    f"Phát hiện {_fmt(anomaly_rows)} dòng bất thường, "
                    f"anomaly_rate={_fmt(anomaly_rate)}%."
                ),
                "suggested_action": _suggest_action("Anomaly Detection", "Anomaly / Outlier", "row-level"),
            }
        )

    plan = sorted(
        plan,
        key=lambda item: (
            -int(item.get("priority_score", 0)),
            str(item.get("column_name", "")),
            str(item.get("problem", "")),
        ),
    )

    return plan


def cleaning_plan_markdown(context: Dict[str, Any], limit: int = 12) -> str:
    plan = build_cleaning_plan_records(context)

    if not plan:
        return """
### Cleaning Plan theo từng cột

Chưa có vấn đề nào đủ rõ trong scan context để lập cleaning plan.

Hãy chạy thêm các tab **Quality Issues**, **Privacy Risk**, **Anomaly Detection** và **Drift Analysis** để assistant có đủ dữ liệu lập kế hoạch xử lý.
""".strip()

    rows = plan[:limit]

    table_lines = [
        "| Priority | Column | Source | Problem | Severity | Suggested Action |",
        "|---:|---|---|---|---|---|",
    ]

    for idx, item in enumerate(rows, start=1):
        table_lines.append(
            "| "
            f"{idx} | "
            f"{_fmt(item.get('column_name'))} | "
            f"{_fmt(item.get('source'))} | "
            f"{_fmt(item.get('problem'))} | "
            f"{_fmt(item.get('severity'))} | "
            f"{_fmt(item.get('suggested_action'))} |"
        )

    evidence_lines = []

    for idx, item in enumerate(rows[:6], start=1):
        evidence_lines.append(
            f"{idx}. **{_fmt(item.get('column_name'))}** — {_fmt(item.get('evidence'))}"
        )

    return f"""
### Cleaning Plan theo từng cột

Bảng dưới đây được sinh từ kết quả scan hiện có: Quality Issues, Privacy Risk, Drift Detection và Anomaly Detection. Assistant không tự thêm dữ liệu ngoài context.

{chr(10).join(table_lines)}

### Dẫn chứng ưu tiên

{chr(10).join(evidence_lines)}

### Cách dùng kế hoạch này

1. Xử lý các dòng/cột có **Privacy Risk High/Critical** trước nếu dataset có thể bị public hoặc dùng dữ liệu người thật.
2. Sau đó xử lý **Quality Issues High**, đặc biệt là missing value, duplicate rows, invalid type và invalid range.
3. Kiểm tra anomaly/outlier trước khi training model.
4. Nếu có drift, không thay baseline bằng current dataset khi chưa điều tra nguyên nhân phân phối thay đổi.
5. Sau khi xử lý, chạy lại các tab scan và so sánh Trust Score mới.
""".strip()