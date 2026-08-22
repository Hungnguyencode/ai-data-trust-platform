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


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "N/A":
            return default
        return int(float(value))
    except Exception:
        return default


def _get(context: Dict[str, Any], group: str, key: str, default: Any = "N/A") -> Any:
    value = context.get(group, {})
    if not isinstance(value, dict):
        return default
    return value.get(key, default)


def _records(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _raw_value_from_component(item: Dict[str, Any]) -> Any:
    """
    Fix lỗi raw=N/A%.
    Vì breakdown_df bên Streamlit dùng key 'raw_value (%)',
    còn API schema/minimal mode có thể dùng 'raw_value'.
    """
    for key in ["raw_value (%)", "raw_value", "raw", "raw_value_percent"]:
        if key in item and item.get(key) is not None:
            return item.get(key)
    return "N/A"


def _top_quality_issues(quality: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    issues = _records(quality.get("issues"))
    if not issues:
        return []

    severity_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

    def sort_key(item: Dict[str, Any]) -> tuple:
        severity = str(item.get("severity", "Low"))
        count = _safe_float(item.get("issue_count", 0))
        rate = _safe_float(item.get("issue_rate (%)", 0))
        return (severity_rank.get(severity, 9), -rate, -count)

    return sorted(issues, key=sort_key)[:limit]


def _top_privacy_findings(privacy: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    findings = _records(privacy.get("findings"))
    if not findings:
        return []

    severity_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

    def sort_key(item: Dict[str, Any]) -> tuple:
        severity = str(item.get("severity", "Low"))
        count = _safe_float(item.get("match_count", 0))
        rate = _safe_float(item.get("match_rate (%)", 0))
        return (severity_rank.get(severity, 9), -rate, -count)

    return sorted(findings, key=sort_key)[:limit]


def _top_drift_columns(drift: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    details = _records(drift.get("drifted_columns_detail"))
    if not details:
        return []

    rank = {"High drift": 0, "Moderate drift": 1, "Low drift": 2, "No significant drift": 9}

    def sort_key(item: Dict[str, Any]) -> tuple:
        level = str(item.get("drift_level", "No significant drift"))
        return (rank.get(level, 9), str(item.get("column_name", "")))

    return sorted(details, key=sort_key)[:limit]


def dataset_summary(context: Dict[str, Any]) -> str:
    dataset = context.get("dataset", {}) or {}

    return f"""
### Tóm tắt dataset

- Dataset hiện tại: **{_fmt(dataset.get("file_name"))}**
- Loại file: **{_fmt(dataset.get("file_type"))}**
- Kích thước: **{_fmt(dataset.get("total_rows"))} dòng × {_fmt(dataset.get("total_columns"))} cột**
- Tổng số ô dữ liệu: **{_fmt(dataset.get("total_cells"))}**
- Missing cells: **{_fmt(dataset.get("missing_cells"))}**
- Duplicate rows: **{_fmt(dataset.get("duplicate_rows"))}**

Nhận xét: đây là phần mô tả nền để assistant chỉ phân tích dựa trên dataset đang có trong session, không tự thêm dữ liệu ngoài.
""".strip()


def trust_score_summary(context: Dict[str, Any]) -> str:
    trust = context.get("trust_score", {}) or {}

    if not trust:
        return "### Giải thích Data Trust Score\n\nChưa có kết quả Trust Score trong session hiện tại. Hãy chạy tab **Trust Score** trước."

    components = _records(trust.get("components"))
    component_lines: List[str] = []

    for item in components:
        raw_value = _raw_value_from_component(item)
        component_lines.append(
            f"- **{_fmt(item.get('score_name'))}**: "
            f"{_fmt(item.get('score'))}/100, "
            f"weight={_fmt(item.get('weight'))}, "
            f"raw={_fmt(raw_value)}%."
        )

    component_text = "\n".join(component_lines) if component_lines else "- Chưa có breakdown chi tiết."

    overall_score = _fmt(trust.get("overall_score"))
    risk_level = _fmt(trust.get("risk_level"))
    ai_readiness = _fmt(trust.get("ai_readiness"))
    conclusion = _fmt(trust.get("conclusion", trust.get("recommendation", "")), "")

    return f"""
### Giải thích Data Trust Score

- Overall Data Trust Score: **{overall_score}/100**
- Risk Level: **{risk_level}**
- AI Readiness: **{ai_readiness}**

**Diễn giải:** điểm này tổng hợp nhiều nhóm kiểm tra như completeness, validity, uniqueness, consistency và anomaly safety. Điểm càng cao nghĩa là dataset càng đáng tin cậy để phân tích hoặc huấn luyện mô hình.

**Breakdown điểm:**

{component_text}

**Kết luận từ hệ thống:** {conclusion}
""".strip()


def quality_summary(context: Dict[str, Any]) -> str:
    quality = context.get("quality", {}) or {}

    if not quality:
        return "### Tóm tắt Quality Issues\n\nChưa có kết quả Quality Issues trong session hiện tại. Hãy chạy tab **Quality Issues** trước."

    total = _fmt(quality.get("total_issues"))
    high = _fmt(quality.get("high_issues"))
    medium = _fmt(quality.get("medium_issues"))
    low = _fmt(quality.get("low_issues"))
    affected = _fmt(quality.get("affected_columns"))
    total_columns = _fmt(quality.get("total_columns"))

    top_issues = _top_quality_issues(quality)
    issue_lines = []

    for item in top_issues:
        issue_lines.append(
            f"- **{_fmt(item.get('issue_type'))}** ở cột **{_fmt(item.get('column_name'))}**: "
            f"severity={_fmt(item.get('severity'))}, "
            f"count={_fmt(item.get('issue_count'))}, "
            f"rate={_fmt(item.get('issue_rate (%)'))}%."
        )

    if not issue_lines:
        issue_lines.append("- Không có issue chi tiết để hiển thị.")

    return f"""
### Tóm tắt Quality Issues

- Tổng số issue group: **{total}**
- High issues: **{high}**
- Medium issues: **{medium}**
- Low issues: **{low}**
- Số cột bị ảnh hưởng: **{affected}/{total_columns}**

**Các lỗi nổi bật:**

{chr(10).join(issue_lines)}

**Nhận xét:** nếu có lỗi High, nên ưu tiên xử lý trước khi dùng dataset cho báo cáo chính thức, dashboard hoặc AI/ML.
""".strip()


def anomaly_summary(context: Dict[str, Any]) -> str:
    anomaly = context.get("anomaly", {}) or {}

    if not anomaly:
        return "### Tóm tắt Anomaly Detection\n\nChưa có kết quả Anomaly Detection trong session hiện tại. Hãy chạy tab **Anomaly Detection** trước."

    return f"""
### Tóm tắt Anomaly Detection

- Tổng số dòng: **{_fmt(anomaly.get("total_rows"))}**
- Số dòng bất thường: **{_fmt(anomaly.get("total_anomaly_rows"))}**
- Anomaly rate: **{_fmt(anomaly.get("anomaly_rate"))}%**
- Anomaly Score: **{_fmt(anomaly.get("anomaly_score"))}/100**
- Risk Level: **{_fmt(anomaly.get("risk_level"))}**

**Diễn giải:** nếu anomaly rate cao, cần kiểm tra các dòng bị đánh dấu trước khi dùng dataset để huấn luyện mô hình hoặc đưa vào phân tích chính thức.
""".strip()


def privacy_summary(context: Dict[str, Any]) -> str:
    privacy = context.get("privacy", {}) or {}

    if not privacy:
        return "### Tóm tắt Privacy Risk\n\nChưa có kết quả Privacy Risk trong session hiện tại. Hãy chạy tab **Privacy Risk** trước."

    findings = _top_privacy_findings(privacy)
    finding_lines = []

    for item in findings:
        finding_lines.append(
            f"- **{_fmt(item.get('pii_type'))}** ở cột **{_fmt(item.get('column_name'))}**: "
            f"severity={_fmt(item.get('severity'))}, "
            f"match_count={_fmt(item.get('match_count'))}, "
            f"match_rate={_fmt(item.get('match_rate (%)'))}%."
        )

    if not finding_lines:
        finding_lines.append("- Không có finding chi tiết để hiển thị.")

    return f"""
### Đánh giá Privacy Risk

- Privacy Safety Score: **{_fmt(privacy.get("privacy_safety_score"))}/100**
- Risk Level: **{_fmt(privacy.get("risk_level"))}**
- PII Columns: **{_fmt(privacy.get("pii_columns"))}/{_fmt(privacy.get("total_columns"))}**
- PII Cell Rate: **{_fmt(privacy.get("pii_cell_rate"))}%**
- High-risk findings: **{_fmt(privacy.get("high_risk_findings"))}**

**Dẫn chứng từ scan:**

{chr(10).join(finding_lines)}

**Diễn giải:** nếu risk level là High hoặc Critical, không nên public dataset khi chưa mask/hash/pseudonymize các trường định danh.
""".strip()


def drift_summary(context: Dict[str, Any]) -> str:
    drift = context.get("drift", {}) or {}

    if not drift:
        return "### Tóm tắt Drift Detection\n\nChưa có kết quả Drift Detection trong session hiện tại. Hãy chạy tab **Drift Analysis** trước."

    drifted = _top_drift_columns(drift)
    drift_lines = []

    for item in drifted:
        drift_lines.append(
            f"- **{_fmt(item.get('column_name'))}**: "
            f"type={_fmt(item.get('drift_type'))}, "
            f"level={_fmt(item.get('drift_level'))}."
        )

    if not drift_lines:
        drift_lines.append("- Không có cột drift đáng kể trong chi tiết hiện tại.")

    return f"""
### Phân tích Drift Detection

- Drift Score: **{_fmt(drift.get("drift_score"))}/100**
- Overall Drift Level: **{_fmt(drift.get("overall_drift_level"))}**
- Schema Drift Count: **{_fmt(drift.get("schema_drift_count"))}**
- Drifted Columns: **{_fmt(drift.get("drifted_columns"))}**
- High Drift Columns: **{_fmt(drift.get("high_drift_columns"))}**
- Moderate Drift Columns: **{_fmt(drift.get("moderate_drift_columns"))}**

**Các cột drift đáng chú ý:**

{chr(10).join(drift_lines)}

**Diễn giải:** nếu Overall Drift là High, không nên thay thế baseline bằng current dataset khi chưa điều tra nguyên nhân thay đổi phân phối.
""".strip()


def ai_readiness_explanation(context: Dict[str, Any]) -> str:
    trust = context.get("trust_score", {}) or {}
    quality = context.get("quality", {}) or {}
    anomaly = context.get("anomaly", {}) or {}
    privacy = context.get("privacy", {}) or {}
    drift = context.get("drift", {}) or {}

    if not trust:
        return "### Giải thích AI Readiness\n\nChưa có Trust Score nên chưa thể giải thích AI Readiness đầy đủ."

    lines = [
        f"AI Readiness hiện tại: **{_fmt(trust.get('ai_readiness'))}**.",
        f"Overall Trust Score: **{_fmt(trust.get('overall_score'))}/100**.",
        f"Risk Level: **{_fmt(trust.get('risk_level'))}**.",
    ]

    if quality:
        lines.append(
            f"Quality Issues: **{_fmt(quality.get('total_issues'))} issue group**, trong đó High={_fmt(quality.get('high_issues'))}."
        )

    if anomaly:
        lines.append(
            f"Anomaly: **{_fmt(anomaly.get('total_anomaly_rows'))} dòng bất thường**, anomaly rate={_fmt(anomaly.get('anomaly_rate'))}%."
        )

    if privacy:
        lines.append(
            f"Privacy Risk: **{_fmt(privacy.get('risk_level'))}**, PII columns={_fmt(privacy.get('pii_columns'))}/{_fmt(privacy.get('total_columns'))}."
        )

    if drift:
        lines.append(
            f"Drift Detection: **{_fmt(drift.get('overall_drift_level'))}**, drifted columns={_fmt(drift.get('drifted_columns'))}."
        )

    lines.append(
        "Dataset chỉ nên được coi là sẵn sàng cho AI/ML khi chất lượng dữ liệu ổn, ít lỗi nghiêm trọng, ít outlier, privacy risk thấp và drift không mạnh."
    )

    return "### Giải thích AI Readiness\n\n" + "\n".join(f"- {line}" for line in lines)


def public_dataset_decision(context: Dict[str, Any]) -> str:
    privacy = context.get("privacy", {}) or {}
    quality = context.get("quality", {}) or {}
    drift = context.get("drift", {}) or {}
    trust = context.get("trust_score", {}) or {}

    evidence = []
    decision = "Có thể public có điều kiện"

    privacy_level = str(privacy.get("risk_level", "")).lower()
    pii_columns = _safe_int(privacy.get("pii_columns", 0))

    if privacy and (privacy_level in ["high", "critical"] or pii_columns > 0):
        decision = "Không nên public ngay"
        evidence.append(
            f"Privacy Risk đang là **{_fmt(privacy.get('risk_level'))}**, có **{_fmt(privacy.get('pii_columns'))}/{_fmt(privacy.get('total_columns'))}** cột chứa dấu hiệu PII."
        )

    high_issues = _safe_int(quality.get("high_issues", 0))
    if quality and high_issues > 0:
        decision = "Không nên public ngay"
        evidence.append(
            f"Quality scan có **{high_issues} High issues**, cần xử lý trước khi chia sẻ."
        )

    drift_level = str(drift.get("overall_drift_level", "")).lower()
    if drift and drift_level == "high":
        evidence.append(
            f"Drift Detection đang ở mức **High**, current dataset có thay đổi phân phối mạnh so với baseline."
        )

    score = _safe_float(trust.get("overall_score", 0))
    if trust and score < 70:
        decision = "Không nên public ngay"
        evidence.append(
            f"Data Trust Score chỉ đạt **{_fmt(trust.get('overall_score'))}/100**, chưa đủ an toàn cho chia sẻ chính thức."
        )

    if not evidence:
        evidence.append(
            "Các kết quả scan hiện có không cho thấy cảnh báo lớn. Tuy nhiên vẫn nên kiểm tra nghiệp vụ và ẩn danh hóa dữ liệu trước khi public."
        )

    return f"""
### Dataset này có nên public không?

**Kết luận:** {decision}.

**Dẫn chứng từ kết quả scan:**

{chr(10).join(f"- {item}" for item in evidence)}

**Khuyến nghị:** nếu dataset có dữ liệu người dùng thật, hãy mask/hash/pseudonymize các cột định danh như name, email, phone, citizen_id, address trước khi public.
""".strip()


def biggest_risk_summary(context: Dict[str, Any]) -> str:
    quality = context.get("quality", {}) or {}
    anomaly = context.get("anomaly", {}) or {}
    privacy = context.get("privacy", {}) or {}
    drift = context.get("drift", {}) or {}
    trust = context.get("trust_score", {}) or {}

    candidates: List[Dict[str, Any]] = []

    privacy_level = str(privacy.get("risk_level", "")).lower()
    if privacy:
        score = {"critical": 100, "high": 85, "medium": 55, "low": 20}.get(privacy_level, 0)
        candidates.append(
            {
                "name": "Privacy Risk",
                "score": score,
                "evidence": f"Risk Level={_fmt(privacy.get('risk_level'))}, PII Columns={_fmt(privacy.get('pii_columns'))}/{_fmt(privacy.get('total_columns'))}.",
            }
        )

    if quality:
        high_issues = _safe_int(quality.get("high_issues", 0))
        medium_issues = _safe_int(quality.get("medium_issues", 0))
        score = high_issues * 35 + medium_issues * 10
        candidates.append(
            {
                "name": "Quality Issues",
                "score": score,
                "evidence": f"High issues={high_issues}, Medium issues={medium_issues}, Total issues={_fmt(quality.get('total_issues'))}.",
            }
        )

    if anomaly:
        anomaly_rate = _safe_float(anomaly.get("anomaly_rate", 0))
        candidates.append(
            {
                "name": "Anomaly / Outlier",
                "score": anomaly_rate * 3,
                "evidence": f"Anomaly rows={_fmt(anomaly.get('total_anomaly_rows'))}, Anomaly rate={_fmt(anomaly.get('anomaly_rate'))}%, Risk Level={_fmt(anomaly.get('risk_level'))}.",
            }
        )

    if drift:
        drift_level = str(drift.get("overall_drift_level", "")).lower()
        drift_score = {"high": 90, "medium": 60, "low": 35, "none": 0}.get(drift_level, 0)
        candidates.append(
            {
                "name": "Data Drift",
                "score": drift_score,
                "evidence": f"Overall Drift={_fmt(drift.get('overall_drift_level'))}, Drifted Columns={_fmt(drift.get('drifted_columns'))}.",
            }
        )

    if trust:
        overall = _safe_float(trust.get("overall_score", 100))
        if overall < 70:
            candidates.append(
                {
                    "name": "Low Data Trust Score",
                    "score": 100 - overall,
                    "evidence": f"Overall Score={_fmt(trust.get('overall_score'))}/100, Risk Level={_fmt(trust.get('risk_level'))}.",
                }
            )

    if not candidates:
        return "### Rủi ro lớn nhất hiện tại\n\nChưa có đủ kết quả scan để xác định rủi ro lớn nhất. Hãy chạy Quality, Trust Score, Anomaly, Privacy và Drift trước."

    top = sorted(candidates, key=lambda x: x["score"], reverse=True)[0]

    return f"""
### Rủi ro lớn nhất hiện tại

**Rủi ro lớn nhất:** {top["name"]}

**Dẫn chứng:** {top["evidence"]}

**Khuyến nghị:** xử lý nhóm rủi ro này trước, sau đó chạy lại các tab scan để xem điểm và mức rủi ro có cải thiện không.
""".strip()


def priority_action_plan(context: Dict[str, Any]) -> str:
    quality = context.get("quality", {}) or {}
    anomaly = context.get("anomaly", {}) or {}
    privacy = context.get("privacy", {}) or {}
    drift = context.get("drift", {}) or {}

    actions: List[str] = []

    privacy_level = str(privacy.get("risk_level", "")).lower()
    if privacy and privacy_level in ["critical", "high"]:
        findings = _top_privacy_findings(privacy, limit=3)
        pii_cols = sorted({str(item.get("column_name")) for item in findings if item.get("column_name")})
        col_text = ", ".join(pii_cols) if pii_cols else "các cột PII"
        actions.append(
            f"**Bước 1 — Xử lý Privacy Risk:** mask/hash/pseudonymize {col_text}. "
            f"Dẫn chứng: Privacy Risk={_fmt(privacy.get('risk_level'))}, PII Columns={_fmt(privacy.get('pii_columns'))}/{_fmt(privacy.get('total_columns'))}."
        )

    high_issues = _safe_int(quality.get("high_issues", 0))
    if quality and high_issues > 0:
        top_issues = _top_quality_issues(quality, limit=3)
        issue_text = "; ".join(
            f"{_fmt(item.get('issue_type'))} ở {_fmt(item.get('column_name'))}"
            for item in top_issues
        )
        actions.append(
            f"**Bước 2 — Sửa High Quality Issues:** ưu tiên {issue_text}. "
            f"Dẫn chứng: High issues={high_issues}, Total issues={_fmt(quality.get('total_issues'))}."
        )

    drift_level = str(drift.get("overall_drift_level", "")).lower()
    if drift and drift_level in ["high", "medium"]:
        actions.append(
            f"**Bước 3 — Kiểm tra Drift:** điều tra các cột bị drift trước khi dùng current thay baseline. "
            f"Dẫn chứng: Overall Drift={_fmt(drift.get('overall_drift_level'))}, Drifted Columns={_fmt(drift.get('drifted_columns'))}."
        )

    anomaly_rate = _safe_float(anomaly.get("anomaly_rate", 0))
    if anomaly and anomaly_rate > 0 and len(actions) < 3:
        actions.append(
            f"**Bước {len(actions) + 1} — Kiểm tra anomaly/outlier:** xem các dòng bất thường trước khi training hoặc phân tích. "
            f"Dẫn chứng: anomaly rows={_fmt(anomaly.get('total_anomaly_rows'))}, anomaly rate={_fmt(anomaly.get('anomaly_rate'))}%."
        )

    if not actions:
        actions.append(
            "**Bước 1 — Kiểm tra nghiệp vụ:** các kết quả scan hiện chưa có cảnh báo lớn, nhưng vẫn cần rule nghiệp vụ."
        )
        actions.append(
            "**Bước 2 — Lưu scan/report:** lưu kết quả vào SQL Server và export HTML report để làm minh chứng."
        )
        actions.append(
            "**Bước 3 — Theo dõi định kỳ:** khi có dataset mới, chạy Drift Analysis để so sánh với baseline."
        )

    actions = actions[:3]

    return "### Kế hoạch xử lý ưu tiên 3 bước\n\n" + "\n\n".join(f"{idx + 1}. {item}" for idx, item in enumerate(actions))


def smart_diagnosis(context: Dict[str, Any]) -> str:
    trust = context.get("trust_score", {}) or {}
    quality = context.get("quality", {}) or {}
    privacy = context.get("privacy", {}) or {}
    drift = context.get("drift", {}) or {}
    anomaly = context.get("anomaly", {}) or {}

    diagnosis: List[str] = []

    if trust:
        score = _safe_float(trust.get("overall_score", 0))
        if score >= 85:
            diagnosis.append(
                f"Trust Score đang tốt (**{_fmt(trust.get('overall_score'))}/100**), dataset có nền tảng chất lượng khá ổn."
            )
        elif score >= 70:
            diagnosis.append(
                f"Trust Score ở mức khá (**{_fmt(trust.get('overall_score'))}/100**), nhưng vẫn nên xử lý lỗi còn lại trước khi dùng chính thức."
            )
        else:
            diagnosis.append(
                f"Trust Score còn thấp (**{_fmt(trust.get('overall_score'))}/100**), cần làm sạch dữ liệu trước khi dùng cho AI/ML."
            )

    if quality:
        high_issues = _safe_int(quality.get("high_issues", 0))
        if high_issues > 0:
            diagnosis.append(
                f"Có **{high_issues} High quality issues**, đây là nhóm cần xử lý sớm."
            )

    if privacy:
        privacy_level = str(privacy.get("risk_level", "N/A"))
        if privacy_level in ["High", "Critical"]:
            diagnosis.append(
                f"Privacy Risk đang ở mức **{privacy_level}**, không nên public dataset nếu chưa ẩn danh hóa."
            )
        else:
            diagnosis.append(
                f"Privacy Risk hiện là **{privacy_level}** theo rule scanner."
            )

    if drift:
        drift_level = str(drift.get("overall_drift_level", "N/A"))
        if drift_level in ["High", "Medium"]:
            diagnosis.append(
                f"Drift Detection ở mức **{drift_level}**, cần kiểm tra sự thay đổi phân phối giữa baseline và current."
            )

    if anomaly:
        anomaly_rate = _safe_float(anomaly.get("anomaly_rate", 0))
        if anomaly_rate > 0:
            diagnosis.append(
                f"Anomaly Detection phát hiện **{_fmt(anomaly.get('total_anomaly_rows'))}** dòng bất thường, anomaly rate={_fmt(anomaly.get('anomaly_rate'))}%."
            )

    if not diagnosis:
        diagnosis.append(
            "Chưa có đủ kết quả scan để chẩn đoán sâu. Hãy chạy Quality, Trust Score, Anomaly, Privacy và Drift."
        )

    return "### Smart Diagnosis\n\n" + "\n".join(f"- {item}" for item in diagnosis)


def generate_recommendation_summary(context: Dict[str, Any]) -> str:
    return priority_action_plan(context)


def explain_score_gap(context: Dict[str, Any]) -> str:
    """
    Giải thích vì sao Trust Score chưa đạt mức rất cao.
    Rule-grounded: chỉ dùng score components và issue hiện có.
    """
    trust = context.get("trust_score", {}) or {}
    quality = context.get("quality", {}) or {}
    anomaly = context.get("anomaly", {}) or {}
    privacy = context.get("privacy", {}) or {}
    drift = context.get("drift", {}) or {}

    if not trust:
        return (
            "### Tại sao Trust Score chưa đạt 90?\n\n"
            "Chưa có kết quả Trust Score trong session hiện tại. Hãy chạy tab **Trust Score** trước."
        )

    score = _safe_float(trust.get("overall_score", 0))
    components = _records(trust.get("components"))

    weak_components = []
    for item in components:
        component_score = _safe_float(item.get("score", 100))
        if component_score < 90:
            weak_components.append(item)

    weak_components = sorted(
        weak_components,
        key=lambda item: _safe_float(item.get("score", 100)),
    )

    lines = [
        f"Overall Trust Score hiện tại là **{_fmt(score)}/100**.",
    ]

    if score >= 90:
        lines.append("Điểm đã đạt từ 90 trở lên, tức là dataset đang ở mức rất tốt theo bộ rule hiện tại.")
    else:
        lines.append(
            "Điểm chưa đạt 90 vì một số nhóm điểm thành phần vẫn còn bị trừ bởi missing value, duplicate, validity issue, consistency issue hoặc anomaly."
        )

    if weak_components:
        lines.append("")
        lines.append("Các nhóm điểm đang kéo Trust Score xuống:")

        for item in weak_components[:5]:
            raw_value = _raw_value_from_component(item)
            lines.append(
                f"- **{_fmt(item.get('score_name'))}**: "
                f"{_fmt(item.get('score'))}/100, "
                f"weight={_fmt(item.get('weight'))}, "
                f"raw={_fmt(raw_value)}%. "
                f"{_fmt(item.get('detail'), '')}"
            )
    else:
        lines.append("- Không có breakdown nào dưới 90 trong context hiện tại.")

    if quality:
        lines.append("")
        lines.append(
            f"Quality Issues hiện có **{_fmt(quality.get('total_issues'))} issue group**, "
            f"trong đó High={_fmt(quality.get('high_issues'))}, Medium={_fmt(quality.get('medium_issues'))}."
        )

    if anomaly:
        lines.append(
            f"Anomaly hiện có **{_fmt(anomaly.get('total_anomaly_rows'))} dòng bất thường**, "
            f"anomaly rate={_fmt(anomaly.get('anomaly_rate'))}%."
        )

    if privacy:
        lines.append(
            f"Privacy Risk đang là **{_fmt(privacy.get('risk_level'))}**, "
            f"PII columns={_fmt(privacy.get('pii_columns'))}/{_fmt(privacy.get('total_columns'))}."
        )

    if drift:
        lines.append(
            f"Drift Detection đang là **{_fmt(drift.get('overall_drift_level'))}**, "
            f"drifted columns={_fmt(drift.get('drifted_columns'))}."
        )

    lines.append("")
    lines.append(
        "**Kết luận:** muốn kéo Trust Score lên gần 90+, nên ưu tiên xử lý các nhóm điểm thành phần dưới 90 trước, đặc biệt là validity, uniqueness, consistency và anomaly safety."
    )

    return "### Tại sao Trust Score chưa đạt 90?\n\n" + "\n".join(lines)


def explain_missing_fix(context: Dict[str, Any]) -> str:
    quality = context.get("quality", {}) or {}
    issues = _records(quality.get("issues"))

    missing_issues = [
        item for item in issues
        if str(item.get("issue_type", "")).lower() == "missing value"
    ]

    if not quality:
        return (
            "### Sửa missing value như thế nào?\n\n"
            "Chưa có kết quả Quality Issues trong session hiện tại. Hãy chạy tab **Quality Issues** trước."
        )

    if not missing_issues:
        return (
            "### Sửa missing value như thế nào?\n\n"
            "Không phát hiện missing value trong context hiện tại. Chưa cần xử lý nhóm lỗi này."
        )

    lines = [
        "Các cột có missing value cần xem xét:",
    ]

    for item in missing_issues[:8]:
        col = _fmt(item.get("column_name"))
        count = _fmt(item.get("issue_count"))
        rate = _fmt(item.get("issue_rate (%)"))
        severity = _fmt(item.get("severity"))

        lines.append(
            f"- **{col}**: missing={count}, rate={rate}%, severity={severity}."
        )

    lines.extend(
        [
            "",
            "**Cách xử lý đề xuất:**",
            "- Nếu cột là numeric: có thể điền median nếu dữ liệu lệch, hoặc mean nếu phân phối tương đối đều.",
            "- Nếu cột là categorical/text: có thể điền `Unknown`, mode, hoặc tạo nhãn riêng để giữ thông tin thiếu.",
            "- Nếu một dòng thiếu quá nhiều trường quan trọng: cân nhắc loại bỏ dòng đó.",
            "- Nếu cột thiếu quá nhiều và không quan trọng: cân nhắc loại bỏ cột khỏi pipeline.",
            "",
            "**Lưu ý:** không nên điền missing bừa bằng 0 nếu 0 có ý nghĩa nghiệp vụ thật, vì có thể làm lệch phân phối dữ liệu.",
        ]
    )

    return "### Sửa missing value như thế nào?\n\n" + "\n".join(lines)


def explain_duplicate_fix(context: Dict[str, Any]) -> str:
    quality = context.get("quality", {}) or {}
    dataset = context.get("dataset", {}) or {}
    issues = _records(quality.get("issues"))

    duplicate_issues = [
        item for item in issues
        if str(item.get("issue_type", "")).lower() == "duplicate rows"
    ]

    duplicate_rows = dataset.get("duplicate_rows")

    if not quality and duplicate_rows in [None, "N/A"]:
        return (
            "### Sửa duplicate rows như thế nào?\n\n"
            "Chưa có đủ kết quả scan để đánh giá duplicate rows."
        )

    if not duplicate_issues and _safe_int(duplicate_rows, 0) == 0:
        return (
            "### Sửa duplicate rows như thế nào?\n\n"
            "Không phát hiện duplicate rows trong context hiện tại. Chưa cần xử lý nhóm lỗi này."
        )

    lines = []

    if duplicate_issues:
        for item in duplicate_issues:
            lines.append(
                f"- Phát hiện **{_fmt(item.get('issue_count'))}** duplicate rows, "
                f"rate={_fmt(item.get('issue_rate (%)'))}%, severity={_fmt(item.get('severity'))}."
            )
    else:
        lines.append(f"- Dataset có **{_fmt(duplicate_rows)}** duplicate rows.")

    lines.extend(
        [
            "",
            "**Cách xử lý đề xuất:**",
            "- Nếu duplicate là lỗi nhập liệu: dùng `drop_duplicates()` để loại bỏ.",
            "- Nếu duplicate có ý nghĩa nghiệp vụ, ví dụ nhiều giao dịch giống nhau: không xóa ngay, cần kiểm tra khóa định danh như `order_id`, `transaction_id`, `customer_id`.",
            "- Sau khi xử lý duplicate, chạy lại tab **Quality Issues** và **Trust Score** để kiểm tra điểm Uniqueness có tăng không.",
        ]
    )

    return "### Sửa duplicate rows như thế nào?\n\n" + "\n".join(lines)


def explain_outlier_decision(context: Dict[str, Any]) -> str:
    anomaly = context.get("anomaly", {}) or {}

    if not anomaly:
        return (
            "### Outlier có nên xóa không?\n\n"
            "Chưa có kết quả Anomaly Detection trong session hiện tại. Hãy chạy tab **Anomaly Detection** trước."
        )

    anomaly_rows = _safe_int(anomaly.get("total_anomaly_rows", 0))
    anomaly_rate = _safe_float(anomaly.get("anomaly_rate", 0))
    risk_level = _fmt(anomaly.get("risk_level"))

    lines = [
        f"Anomaly rows: **{anomaly_rows}**.",
        f"Anomaly rate: **{_fmt(anomaly_rate)}%**.",
        f"Risk Level: **{risk_level}**.",
        "",
    ]

    if anomaly_rows == 0:
        lines.append("Không phát hiện outlier đáng kể, nên chưa cần xóa dữ liệu.")
    elif anomaly_rate <= 5:
        lines.append(
            "Có ít outlier. Không nên xóa tự động ngay; nên kiểm tra từng dòng để xem đó là lỗi nhập liệu hay giá trị hiếm nhưng hợp lệ."
        )
    elif anomaly_rate <= 15:
        lines.append(
            "Tỷ lệ outlier ở mức cần chú ý. Nên kiểm tra nguồn dữ liệu, so sánh với rule nghiệp vụ, sau đó mới quyết định sửa, winsorize, biến đổi log hoặc loại bỏ."
        )
    else:
        lines.append(
            "Tỷ lệ outlier cao. Không nên xóa hàng loạt vì có thể làm mất đặc trưng thật của dữ liệu; cần điều tra nguyên nhân trước."
        )

    lines.extend(
        [
            "",
            "**Nguyên tắc xử lý:**",
            "- Nếu outlier là lỗi nhập liệu: sửa hoặc loại bỏ.",
            "- Nếu outlier là giá trị thật nhưng quá lớn: cân nhắc log-transform hoặc winsorization.",
            "- Nếu dùng cho mô hình ML nhạy với outlier: nên xử lý trước khi training.",
            "- Nếu dùng cho phân tích nghiệp vụ: cần giữ lại nếu outlier phản ánh hành vi quan trọng.",
        ]
    )

    return "### Outlier có nên xóa không?\n\n" + "\n".join(lines)


def explain_drift_decision(context: Dict[str, Any]) -> str:
    drift = context.get("drift", {}) or {}

    if not drift:
        return (
            "### Drift cao thì có dùng current dataset được không?\n\n"
            "Chưa có kết quả Drift Detection trong session hiện tại. Hãy chạy tab **Drift Analysis** trước."
        )

    level = str(drift.get("overall_drift_level", "N/A"))
    drifted_columns = _safe_int(drift.get("drifted_columns", 0))
    high_drift = _safe_int(drift.get("high_drift_columns", 0))
    schema_changes = _safe_int(drift.get("schema_drift_count", 0))
    score = _fmt(drift.get("drift_score"))

    lines = [
        f"Overall Drift Level: **{level}**.",
        f"Drift Score: **{score}/100**.",
        f"Drifted Columns: **{drifted_columns}**.",
        f"High Drift Columns: **{high_drift}**.",
        f"Schema Drift Count: **{schema_changes}**.",
        "",
    ]

    level_lower = level.lower()

    if level_lower == "none":
        lines.append("Có thể dùng current dataset thay baseline vì chưa phát hiện drift đáng kể.")
    elif level_lower == "low":
        lines.append("Có thể dùng current dataset, nhưng nên theo dõi thêm nếu dữ liệu dùng cho dashboard hoặc mô hình định kỳ.")
    elif level_lower == "medium":
        lines.append("Chưa nên thay thế baseline ngay. Nên kiểm tra các cột bị drift và xác định drift là do thay đổi thật hay lỗi pipeline.")
    else:
        lines.append("Không nên dùng current dataset thay baseline ngay. Cần điều tra nguyên nhân phân phối thay đổi trước khi dùng cho phân tích hoặc training.")

    lines.extend(
        [
            "",
            "**Cách kiểm tra tiếp:**",
            "- Xem các cột High drift trước.",
            "- Kiểm tra có schema drift không: thêm/xóa/đổi kiểu cột.",
            "- So sánh phân phối numeric bằng PSI/KS-test.",
            "- So sánh categorical distribution với các cột như city, category, label.",
        ]
    )

    return "### Drift cao thì có dùng current dataset được không?\n\n" + "\n".join(lines)


def explain_privacy_high_reason(context: Dict[str, Any]) -> str:
    privacy = context.get("privacy", {}) or {}

    if not privacy:
        return (
            "### Vì sao Privacy Risk là High?\n\n"
            "Chưa có kết quả Privacy Risk trong session hiện tại. Hãy chạy tab **Privacy Risk** trước."
        )

    findings = _records(privacy.get("findings"))
    level = _fmt(privacy.get("risk_level"))
    score = _fmt(privacy.get("privacy_safety_score"))
    pii_columns = _fmt(privacy.get("pii_columns"))
    total_columns = _fmt(privacy.get("total_columns"))
    pii_rate = _fmt(privacy.get("pii_cell_rate"))

    lines = [
        f"Privacy Risk hiện tại: **{level}**.",
        f"Privacy Safety Score: **{score}/100**.",
        f"PII Columns: **{pii_columns}/{total_columns}**.",
        f"PII Cell Rate: **{pii_rate}%**.",
        "",
    ]

    if findings:
        lines.append("Các phát hiện PII nổi bật:")
        for item in findings[:8]:
            lines.append(
                f"- **{_fmt(item.get('pii_type'))}** ở cột **{_fmt(item.get('column_name'))}**: "
                f"match_count={_fmt(item.get('match_count'))}, "
                f"match_rate={_fmt(item.get('match_rate (%)'))}%, "
                f"severity={_fmt(item.get('severity'))}."
            )
    else:
        lines.append("Không có bảng findings chi tiết trong context hiện tại.")

    lines.extend(
        [
            "",
            "**Vì sao bị đánh giá rủi ro cao:** dataset có dấu hiệu chứa dữ liệu định danh như name, email, phone, citizen_id hoặc address. Các trường này có thể liên kết trực tiếp đến người thật nếu public dữ liệu.",
            "",
            "**Khuyến nghị:** mask/hash/pseudonymize hoặc loại bỏ các cột định danh trước khi chia sẻ dataset.",
        ]
    )

    return "### Vì sao Privacy Risk là High?\n\n" + "\n".join(lines)


def explain_top_columns_to_fix(context: Dict[str, Any]) -> str:
    quality = context.get("quality", {}) or {}
    privacy = context.get("privacy", {}) or {}
    drift = context.get("drift", {}) or {}

    candidates = []

    for item in _records(privacy.get("findings")):
        candidates.append(
            {
                "column": item.get("column_name"),
                "reason": f"Privacy Risk: {item.get('pii_type')}, severity={item.get('severity')}",
                "priority": 1 if str(item.get("severity", "")).lower() in ["high", "critical"] else 2,
            }
        )

    for item in _records(quality.get("issues")):
        severity = str(item.get("severity", "")).lower()
        priority = 1 if severity == "high" else 2 if severity == "medium" else 3
        candidates.append(
            {
                "column": item.get("column_name"),
                "reason": f"Quality Issue: {item.get('issue_type')}, severity={item.get('severity')}, count={item.get('issue_count')}",
                "priority": priority,
            }
        )

    for item in _records(drift.get("drifted_columns_detail")):
        level = str(item.get("drift_level", "")).lower()
        priority = 1 if "high" in level else 2
        candidates.append(
            {
                "column": item.get("column_name"),
                "reason": f"Drift: type={item.get('drift_type')}, level={item.get('drift_level')}",
                "priority": priority,
            }
        )

    if not candidates:
        return (
            "### Cột nào nên xử lý trước?\n\n"
            "Chưa có đủ findings từ Quality, Privacy hoặc Drift để xếp hạng cột cần xử lý."
        )

    grouped: Dict[str, List[str]] = {}
    priority_by_col: Dict[str, int] = {}

    for item in candidates:
        col = _fmt(item.get("column"), "__row__")
        grouped.setdefault(col, []).append(str(item.get("reason")))
        priority_by_col[col] = min(priority_by_col.get(col, 99), int(item.get("priority", 9)))

    sorted_cols = sorted(
        grouped.keys(),
        key=lambda col: (priority_by_col.get(col, 9), col),
    )

    lines = [
        "Các cột/nhóm nên xử lý trước:",
        "",
    ]

    for idx, col in enumerate(sorted_cols[:8], start=1):
        lines.append(f"{idx}. **{col}**")
        for reason in grouped[col][:3]:
            lines.append(f"   - {reason}")

    lines.extend(
        [
            "",
            "**Nguyên tắc ưu tiên:** Privacy Risk High/Critical > Quality Issues High > Drift High > các lỗi Medium/Low.",
        ]
    )

    return "### Cột nào nên xử lý trước?\n\n" + "\n".join(lines)


def fast_score_improvement_plan(context: Dict[str, Any]) -> str:
    """
    Gợi ý tăng điểm nhanh nhất dựa trên lỗi hiện có.
    Không dự đoán điểm chính xác, chỉ nêu nhóm có khả năng cải thiện.
    """
    quality = context.get("quality", {}) or {}
    trust = context.get("trust_score", {}) or {}
    anomaly = context.get("anomaly", {}) or {}
    privacy = context.get("privacy", {}) or {}
    drift = context.get("drift", {}) or {}

    lines = []

    if not trust:
        lines.append("Chưa có Trust Score, nên chưa thể phân tích nhóm điểm kéo score xuống chính xác.")
    else:
        lines.append(f"Trust Score hiện tại: **{_fmt(trust.get('overall_score'))}/100**.")
        lines.append(f"AI Readiness: **{_fmt(trust.get('ai_readiness'))}**.")

    high_issues = _safe_int(quality.get("high_issues", 0))
    medium_issues = _safe_int(quality.get("medium_issues", 0))

    if high_issues > 0:
        lines.append(
            f"1. **Xử lý High Quality Issues trước**: hiện có High={high_issues}, Medium={medium_issues}. Đây thường là nhóm tác động trực tiếp đến Validity/Completeness/Uniqueness."
        )

    privacy_level = str(privacy.get("risk_level", "")).lower()
    if privacy_level in ["high", "critical"]:
        lines.append(
            f"2. **Giảm Privacy Risk**: risk={_fmt(privacy.get('risk_level'))}, PII columns={_fmt(privacy.get('pii_columns'))}/{_fmt(privacy.get('total_columns'))}. Nên mask/hash/pseudonymize trước khi public."
        )

    anomaly_rows = _safe_int(anomaly.get("total_anomaly_rows", 0))
    if anomaly_rows > 0:
        lines.append(
            f"3. **Kiểm tra anomaly/outlier**: hiện có {anomaly_rows} dòng bất thường, anomaly rate={_fmt(anomaly.get('anomaly_rate'))}%. Không xóa vội, cần xác minh lỗi thật hay giá trị hợp lệ."
        )

    drift_level = str(drift.get("overall_drift_level", "")).lower()
    if drift_level in ["medium", "high"]:
        lines.append(
            f"4. **Điều tra Drift Detection**: overall drift={_fmt(drift.get('overall_drift_level'))}, drifted columns={_fmt(drift.get('drifted_columns'))}. Nếu dùng current dataset cho mô hình, cần kiểm tra phân phối trước."
        )

    if len(lines) <= 2:
        lines.append("Dataset hiện khá ổn. Muốn tăng điểm tiếp, nên xử lý các issue nhỏ còn lại và chạy lại toàn bộ scan.")

    lines.append("")
    lines.append(
        "**Lưu ý:** bản rule-grounded không dự đoán chính xác điểm mới sau khi sửa; nó chỉ chỉ ra nhóm có khả năng cải thiện điểm dựa trên kết quả scan hiện tại."
    )

    return "### Muốn tăng điểm nhanh nhất thì sửa gì?\n\n" + "\n".join(lines)
