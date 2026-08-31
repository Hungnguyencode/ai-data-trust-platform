from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import test_connection
from database.repositories.scan_repository import (
    get_quality_issues_by_scan,
    get_scan_history,
)
from src.reports.html_report import (
    build_data_quality_html_report,
    generate_report_filename,
    save_html_report,
)
from src.utils.config import REPORTS_DIR
from src.utils.ui import inject_custom_css, render_metric_card, render_recommendation_box

st.set_page_config(
    page_title="Reports",
    page_icon="📄",
    layout="wide",
)

inject_custom_css()

st.markdown(
    """
    <div class="main-title">📄 Reports & Export</div>
    <div class="subtitle">
        Sinh báo cáo HTML từ kết quả scan hiện tại và xem lịch sử đánh giá dữ liệu đã lưu trong SQL Server.
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown('<div class="section-title">1. Generate HTML Report</div>', unsafe_allow_html=True)

has_current_dataset = "current_df" in st.session_state

if not has_current_dataset:
    render_recommendation_box(
        "Bạn chưa upload dataset trong session hiện tại. Hãy vào Upload Dataset, sau đó chạy Trust Score, Privacy Risk hoặc Drift Analysis nếu muốn báo cáo đầy đủ.",
        level="warning",
    )
else:
    df = st.session_state["current_df"]
    file_name = st.session_state.get("current_file_name", "unknown_dataset")
    file_type = st.session_state.get("current_file_type", "Unknown")
    profile = st.session_state.get("current_profile")
    quality_report = st.session_state.get("current_quality_report")
    trust_score_report = st.session_state.get("current_trust_score_report")
    privacy_report = st.session_state.get("current_privacy_report")
    drift_report = st.session_state.get("current_drift_report")

    if drift_report is not None:
        drift_report["baseline_file_name"] = drift_report.get(
            "baseline_file_name",
            st.session_state.get("drift_baseline_file_name", "baseline dataset"),
        )
        drift_report["current_file_name"] = drift_report.get(
            "current_file_name",
            st.session_state.get("drift_current_file_name", "current dataset"),
        )

    report_col1, report_col2, report_col3, report_col4 = st.columns(4)

    with report_col1:
        render_metric_card(
            "Dataset",
            file_name,
            f"Type: {file_type}",
        )

    with report_col2:
        render_metric_card(
            "Shape",
            f"{df.shape[0]:,} × {df.shape[1]:,}",
            "Rows × Columns",
        )

    with report_col3:
        score_value = "N/A"
        if trust_score_report:
            score_value = f"{trust_score_report.get('overall_score', 'N/A')}/100"

        render_metric_card(
            "Trust Score",
            score_value,
            "Current session",
        )

    with report_col4:
        drift_value = "N/A"
        if drift_report:
            drift_value = drift_report.get("summary", {}).get("overall_drift_level", "N/A")

        render_metric_card(
            "Drift Level",
            drift_value,
            "Current session",
        )

    missing_parts = []

    if quality_report is None:
        missing_parts.append("Quality Issues")

    if trust_score_report is None:
        missing_parts.append("Trust Score")

    if privacy_report is None:
        missing_parts.append("Privacy Risk")

    if drift_report is None:
        missing_parts.append("Drift Analysis")

    if missing_parts:
        render_recommendation_box(
            "Báo cáo vẫn sinh được, nhưng sẽ đầy đủ hơn nếu bạn chạy thêm: "
            + ", ".join(missing_parts)
            + ".",
            level="warning",
        )
    else:
        render_recommendation_box(
            "Session hiện tại đã có đủ Quality, Trust Score, Privacy và Drift để sinh báo cáo đầy đủ.",
            level="success",
        )

    html_content = build_data_quality_html_report(
        file_name=file_name,
        file_type=file_type,
        df=df,
        profile=profile,
        quality_report=quality_report,
        trust_score_report=trust_score_report,
        privacy_report=privacy_report,
        drift_report=drift_report,
    )

    report_file_name = generate_report_filename()

    action_col1, action_col2 = st.columns([1, 1])

    with action_col1:
        st.download_button(
            label="Download HTML report",
            data=html_content.encode("utf-8"),
            file_name=report_file_name,
            mime="text/html",
            use_container_width=True,
        )

    with action_col2:
        if st.button("Save report to data/reports", use_container_width=True):
            try:
                output_path = save_html_report(
                    html_content=html_content,
                    output_dir=REPORTS_DIR,
                    file_name=report_file_name,
                )

                st.success(f"Đã lưu report tại: {output_path}")

            except Exception as exc:
                st.error(f"Không thể lưu report: {exc}")

    with st.expander("Preview HTML source"):
        st.code(html_content[:5000], language="html")

    st.info(
        "PDF report: mở file HTML bằng trình duyệt, sau đó bấm Ctrl + P và chọn Save as PDF. "
        "Cách này ổn định hơn trên Windows so với cài thêm thư viện PDF."
    )


st.markdown('<div class="section-title">2. Database connection</div>', unsafe_allow_html=True)

ok, message = test_connection()

if ok:
    render_recommendation_box(message, level="success")
else:
    render_recommendation_box(message, level="danger")
    st.stop()


st.markdown('<div class="section-title">3. Scan history</div>', unsafe_allow_html=True)

limit = st.slider("Số scan gần nhất", min_value=5, max_value=100, value=50, step=5)

try:
    history_df = get_scan_history(limit=limit)

except Exception as exc:
    st.error(f"Không thể đọc lịch sử scan: {exc}")
    st.stop()

if history_df.empty:
    st.info("Chưa có scan nào được lưu vào database.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card("Total scans", str(len(history_df)), "Số lần scan đã lưu")

with col2:
    avg_score = round(history_df["overall_score"].dropna().mean(), 2)
    render_metric_card("Average score", f"{avg_score}/100", "Điểm trung bình")

with col3:
    high_risk_count = int(history_df["risk_level"].isin(["High", "Critical"]).sum())
    render_metric_card("High/Critical risk", str(high_risk_count), "Scan rủi ro cao")

with col4:
    total_issues = int(history_df["total_issues"].sum())
    render_metric_card("Total issues", str(total_issues), "Tổng issue group")

st.dataframe(history_df, use_container_width=True)


st.markdown('<div class="section-title">4. Score trend</div>', unsafe_allow_html=True)

if "created_at" in history_df.columns and "overall_score" in history_df.columns:
    trend_df = history_df.sort_values(by="created_at")

    fig_trend = px.line(
        trend_df,
        x="created_at",
        y="overall_score",
        markers=True,
        title="Data Trust Score theo thời gian",
    )
    st.plotly_chart(fig_trend, use_container_width=True)


st.markdown('<div class="section-title">5. Issues by scan</div>', unsafe_allow_html=True)

scan_ids = history_df["scan_id"].tolist()

selected_scan_id = st.selectbox(
    "Chọn scan_id để xem quality issues",
    scan_ids,
)

try:
    issues_df = get_quality_issues_by_scan(int(selected_scan_id))

except Exception as exc:
    st.error(f"Không thể đọc quality issues: {exc}")
    st.stop()

if issues_df.empty:
    st.success("Scan này không có quality issues được lưu.")
else:
    st.dataframe(issues_df, use_container_width=True)

    issue_type_count = (
        issues_df.groupby("issue_type")["issue_count"]
        .sum()
        .reset_index()
        .sort_values(by="issue_count", ascending=False)
    )

    fig_issue = px.bar(
        issue_type_count,
        x="issue_type",
        y="issue_count",
        text="issue_count",
        title=f"Số lỗi theo loại — scan_id={selected_scan_id}",
    )
    fig_issue.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig_issue, use_container_width=True)