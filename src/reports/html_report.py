from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd


def _safe_get(mapping: Dict[str, Any] | None, key: str, default: Any = None) -> Any:
    if not mapping:
        return default
    return mapping.get(key, default)


def _df_to_html_table(df: pd.DataFrame | None, max_rows: int = 30) -> str:
    if df is None or df.empty:
        return '<p class="muted">Không có dữ liệu để hiển thị.</p>'

    display_df = df.head(max_rows).copy()

    return display_df.to_html(
        index=False,
        border=0,
        classes="data-table",
        escape=False,
    )


def _metric_card(title: str, value: Any, description: str = "") -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-desc">{description}</div>
    </div>
    """


def _risk_class(level: str | None) -> str:
    if level is None:
        return "neutral"

    level = str(level).lower()

    if level in {"low", "none"}:
        return "low"
    if level == "medium":
        return "medium"
    if level == "high":
        return "high"
    if level == "critical":
        return "critical"

    return "neutral"


def generate_report_filename(prefix: str = "data_trust_report") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.html"


def build_data_quality_html_report(
    file_name: str,
    file_type: str,
    df: pd.DataFrame,
    profile: Dict[str, Any] | None = None,
    quality_report: Dict[str, Any] | None = None,
    trust_score_report: Dict[str, Any] | None = None,
    privacy_report: Dict[str, Any] | None = None,
    drift_report: Dict[str, Any] | None = None,
) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_rows = len(df)
    total_columns = len(df.columns)
    total_cells = total_rows * total_columns

    basic_info = _safe_get(profile, "basic_info", {})
    missing_rate = _safe_get(basic_info, "missing_rate", 0)
    duplicate_rate = _safe_get(basic_info, "duplicate_rate", 0)

    quality_summary = _safe_get(quality_report, "summary", {})
    issues_df = _safe_get(quality_report, "issues_df", pd.DataFrame())

    trust_overall = _safe_get(trust_score_report, "overall_score", "N/A")
    trust_risk = _safe_get(trust_score_report, "risk_level", "N/A")
    ai_readiness = _safe_get(trust_score_report, "ai_readiness", "N/A")
    trust_breakdown_df = _safe_get(trust_score_report, "breakdown_df", pd.DataFrame())

    privacy_summary = _safe_get(privacy_report, "summary", {})
    privacy_findings_df = _safe_get(privacy_report, "findings_df", pd.DataFrame())

    privacy_score = _safe_get(privacy_summary, "privacy_safety_score", "N/A")
    privacy_risk = _safe_get(privacy_summary, "risk_level", "N/A")
    pii_columns = _safe_get(privacy_summary, "pii_columns", "N/A")
    pii_cell_rate = _safe_get(privacy_summary, "pii_cell_rate (%)", "N/A")

    drift_summary = _safe_get(drift_report, "summary", {})
    drift_score = _safe_get(drift_summary, "drift_score", "N/A")
    drift_level = _safe_get(drift_summary, "overall_drift_level", "N/A")
    drifted_columns = _safe_get(drift_summary, "drifted_columns", "N/A")
    schema_drift_count = _safe_get(drift_summary, "schema_drift_count", "N/A")

    drift_baseline_file_name = _safe_get(
        drift_report,
        "baseline_file_name",
        "baseline dataset",
    )

    drift_current_file_name = _safe_get(
        drift_report,
        "current_file_name",
        "current dataset",
    )

    numeric_drift_df = _safe_get(drift_report, "numeric_drift_df", pd.DataFrame())
    categorical_drift_df = _safe_get(drift_report, "categorical_drift_df", pd.DataFrame())
    schema_report = _safe_get(drift_report, "schema_report", {})
    schema_changes_df = _safe_get(schema_report, "changes_df", pd.DataFrame())

    conclusion = _safe_get(
        trust_score_report,
        "conclusion",
        "Chưa có kết luận Data Trust Score.",
    )

    html = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>AI Data Trust Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #f8fafc;
            color: #111827;
            margin: 0;
            padding: 0;
        }}

        .page {{
            max-width: 1180px;
            margin: 0 auto;
            padding: 36px 42px;
            background: #ffffff;
        }}

        .header {{
            border-bottom: 4px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 28px;
        }}

        .title {{
            font-size: 34px;
            font-weight: 800;
            margin: 0;
            color: #111827;
        }}

        .subtitle {{
            font-size: 15px;
            color: #6b7280;
            margin-top: 8px;
        }}

        .section {{
            margin-top: 34px;
        }}

        .section h2 {{
            font-size: 23px;
            margin-bottom: 14px;
            color: #111827;
            border-left: 6px solid #2563eb;
            padding-left: 12px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-top: 16px;
        }}

        .metric-card {{
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 18px;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
        }}

        .metric-title {{
            font-size: 13px;
            color: #6b7280;
            font-weight: 700;
            margin-bottom: 8px;
        }}

        .metric-value {{
            font-size: 28px;
            font-weight: 800;
            color: #111827;
        }}

        .metric-desc {{
            font-size: 12px;
            color: #6b7280;
            margin-top: 7px;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
        }}

        .badge.low {{
            background: #dcfce7;
            color: #166534;
        }}

        .badge.medium {{
            background: #fef3c7;
            color: #92400e;
        }}

        .badge.high {{
            background: #ffedd5;
            color: #9a3412;
        }}

        .badge.critical {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .badge.neutral {{
            background: #e5e7eb;
            color: #374151;
        }}

        .recommendation {{
            background: #eff6ff;
            border-left: 6px solid #2563eb;
            padding: 16px 18px;
            border-radius: 12px;
            margin-top: 16px;
            color: #1e3a8a;
            line-height: 1.55;
        }}

        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            font-size: 13px;
        }}

        .data-table th {{
            background: #f3f4f6;
            color: #374151;
            text-align: left;
            padding: 10px;
            border: 1px solid #e5e7eb;
        }}

        .data-table td {{
            padding: 9px 10px;
            border: 1px solid #e5e7eb;
            vertical-align: top;
        }}

        .muted {{
            color: #6b7280;
            font-size: 14px;
        }}

        .footer {{
            margin-top: 48px;
            padding-top: 18px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-size: 12px;
        }}

        @media print {{
            body {{
                background: #ffffff;
            }}

            .page {{
                box-shadow: none;
                padding: 24px;
            }}

            .section {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="page">
        <div class="header">
            <h1 class="title">AI Data Trust Report</h1>
            <div class="subtitle">
                Báo cáo tự động sinh bởi AI-assisted Data Trust Platform · Generated at {generated_at}
            </div>
        </div>

        <div class="section">
            <h2>1. Dataset Overview</h2>
            <div class="grid">
                {_metric_card("File name", file_name, f"Type: {file_type}")}
                {_metric_card("Rows", f"{total_rows:,}", "Tổng số dòng")}
                {_metric_card("Columns", f"{total_columns:,}", "Tổng số cột")}
                {_metric_card("Cells", f"{total_cells:,}", "Tổng số ô dữ liệu")}
            </div>

            <div class="grid">
                {_metric_card("Missing rate", f"{missing_rate}%", "Tỷ lệ ô bị thiếu")}
                {_metric_card("Duplicate rate", f"{duplicate_rate}%", "Tỷ lệ dòng trùng")}
                {_metric_card("Total issues", _safe_get(quality_summary, "total_issues", 0), "Số nhóm lỗi phát hiện")}
                {_metric_card("Affected columns", _safe_get(quality_summary, "affected_columns", 0), "Số cột bị ảnh hưởng")}
            </div>
        </div>

        <div class="section">
            <h2>2. Data Trust Score</h2>
            <div class="grid">
                {_metric_card("Overall Score", f"{trust_overall}/100", "Điểm tổng hợp")}
                {_metric_card("Risk Level", f'<span class="badge {_risk_class(trust_risk)}">{trust_risk}</span>', "Mức rủi ro dữ liệu")}
                {_metric_card("AI Readiness", ai_readiness, "Mức độ sẵn sàng cho AI/ML")}
                {_metric_card("Conclusion", "Auto", "Kết luận tự động")}
            </div>

            <div class="recommendation">
                <b>Kết luận:</b> {conclusion}
            </div>

            <h3>Score breakdown</h3>
            {_df_to_html_table(trust_breakdown_df)}
        </div>

        <div class="section">
            <h2>3. Quality Issues</h2>
            <div class="grid">
                {_metric_card("High issues", _safe_get(quality_summary, "high_issues", 0), "Lỗi nghiêm trọng")}
                {_metric_card("Medium issues", _safe_get(quality_summary, "medium_issues", 0), "Lỗi cần xử lý")}
                {_metric_card("Low issues", _safe_get(quality_summary, "low_issues", 0), "Lỗi nhẹ")}
                {_metric_card("Total issues", _safe_get(quality_summary, "total_issues", 0), "Tổng issue group")}
            </div>

            {_df_to_html_table(issues_df)}
        </div>

        <div class="section">
            <h2>4. Privacy Risk</h2>
            <div class="grid">
                {_metric_card("Privacy Safety Score", f"{privacy_score}/100", "Điểm càng cao càng an toàn")}
                {_metric_card("Privacy Risk", f'<span class="badge {_risk_class(privacy_risk)}">{privacy_risk}</span>', "Mức rủi ro riêng tư")}
                {_metric_card("PII Columns", pii_columns, "Số cột có PII")}
                {_metric_card("PII Cell Rate", f"{pii_cell_rate}%", "Tỷ lệ ô có PII")}
            </div>

            {_df_to_html_table(privacy_findings_df)}
        </div>

        <div class="section">
            <h2>5. Drift Detection</h2>

            <p class="muted">
                Drift baseline: <b>{drift_baseline_file_name}</b> ·
                Current: <b>{drift_current_file_name}</b>
            </p>

            <div class="grid">
                {_metric_card("Drift Score", f"{drift_score}/100", "Điểm càng cao càng ổn định")}
                {_metric_card("Overall Drift", f'<span class="badge {_risk_class(drift_level)}">{drift_level}</span>', "Mức drift tổng quan")}
                {_metric_card("Drifted Columns", drifted_columns, "Số cột bị drift")}
                {_metric_card("Schema Drift Count", schema_drift_count, "Số thay đổi schema")}
            </div>

            <h3>Schema drift</h3>
            {_df_to_html_table(schema_changes_df)}

            <h3>Numeric drift</h3>
            {_df_to_html_table(numeric_drift_df)}

            <h3>Categorical drift</h3>
            {_df_to_html_table(categorical_drift_df)}
        </div>

        <div class="section">
            <h2>6. Recommendations</h2>
            <div class="recommendation">
                <ul>
                    <li>Ưu tiên xử lý các lỗi High/Critical trong Quality Issues.</li>
                    <li>Mask, hash hoặc pseudonymize các cột có PII trước khi chia sẻ dữ liệu.</li>
                    <li>Nếu Drift Level là High, không nên dùng current dataset thay thế baseline khi chưa điều tra nguyên nhân.</li>
                    <li>Kiểm tra lại outlier và missing value trước khi huấn luyện mô hình AI/ML.</li>
                </ul>
            </div>
        </div>

        <div class="footer">
            AI-assisted Data Trust Platform · Version 0.9 Report Generator · HTML report có thể in ra PDF bằng trình duyệt.
        </div>
    </div>
</body>
</html>
"""

    return html


def save_html_report(html_content: str, output_dir: Path, file_name: str | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    if file_name is None:
        file_name = generate_report_filename()

    output_path = output_dir / file_name
    output_path.write_text(html_content, encoding="utf-8")

    return output_path