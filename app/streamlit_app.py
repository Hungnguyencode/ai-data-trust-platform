from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.scoring.score_engine import calculate_data_trust_score
from src.validation.rule_engine import run_quality_checks
from src.utils.ui import inject_custom_css, render_metric_card, render_recommendation_box


st.set_page_config(
    page_title="AI Data Trust Platform",
    page_icon="🧠",
    layout="wide",
)

inject_custom_css()


st.markdown(
    """
    <div class="main-title">🧠 AI-assisted Data Trust Platform</div>
    <div class="subtitle">
        Nền tảng đánh giá độ tin cậy và mức độ sẵn sàng của dữ liệu cho phân tích và AI/ML.
    </div>
    """,
    unsafe_allow_html=True,
)


if "current_df" not in st.session_state:
    st.markdown('<div class="section-title">Tổng quan hệ thống</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        render_metric_card(
            "Data Profiling",
            "Schema + Missing",
            "Phân tích cấu trúc, kiểu dữ liệu, missing value và duplicate rows.",
        )

    with col2:
        render_metric_card(
            "Quality Checking",
            "Rules + Issues",
            "Phát hiện lỗi kiểu dữ liệu, range, categorical value và consistency.",
        )

    with col3:
        render_metric_card(
            "Trust Scoring",
            "0–100 Score",
            "Chấm điểm mức độ tin cậy và sẵn sàng cho phân tích/AI.",
        )

    st.markdown('<div class="section-title">Luồng sử dụng</div>', unsafe_allow_html=True)

    st.markdown(
        """
        1. Vào trang **Upload Dataset** để tải file CSV/Excel/JSON.  
        2. Xem tổng quan ở **Data Profile**.  
        3. Kiểm tra lỗi tại **Quality Issues**.  
        4. Xem điểm tổng hợp tại **Trust Score**.  
        5. Các version sau sẽ bổ sung **Privacy Risk**, **Drift Analysis**, **AI Assistant** và **Reports**.
        """
    )

    render_recommendation_box(
        "Bắt đầu bằng cách mở trang <b>Upload Dataset</b> ở sidebar bên trái.",
        level="info",
    )

    st.stop()


df = st.session_state["current_df"]
profile = st.session_state.get("current_profile")
file_name = st.session_state.get("current_file_name", "Unknown file")
file_type = st.session_state.get("current_file_type", "Unknown type")

quality_report = st.session_state.get("current_quality_report")
if quality_report is None:
    quality_report = run_quality_checks(df)
    st.session_state["current_quality_report"] = quality_report

trust_score_report = st.session_state.get("current_trust_score_report")
if trust_score_report is None:
    trust_score_report = calculate_data_trust_score(df, quality_report)
    st.session_state["current_trust_score_report"] = trust_score_report


overall_score = trust_score_report["overall_score"]
risk_level = trust_score_report["risk_level"]
ai_readiness = trust_score_report["ai_readiness"]
issues_df = quality_report["issues_df"]


st.markdown('<div class="section-title">Dashboard Overview</div>', unsafe_allow_html=True)

status = "low"
if risk_level == "Medium":
    status = "medium"
elif risk_level == "High":
    status = "high"
elif risk_level == "Critical":
    status = "critical"

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card(
        "Dataset",
        file_name,
        f"Type: {file_type}",
    )

with col2:
    render_metric_card(
        "Shape",
        f"{df.shape[0]:,} × {df.shape[1]:,}",
        "Rows × Columns",
    )

with col3:
    render_metric_card(
        "Data Trust Score",
        f"{overall_score}/100",
        "Overall quality score",
        status=status,
    )

with col4:
    render_metric_card(
        "AI Readiness",
        ai_readiness,
        f"Risk Level: {risk_level}",
        status=status,
    )


st.markdown('<div class="section-title">Quick Diagnostics</div>', unsafe_allow_html=True)

diag_col1, diag_col2 = st.columns(2)

with diag_col1:
    if profile:
        missing_summary = profile["missing_summary"]
        missing_nonzero = missing_summary[missing_summary["missing_count"] > 0]

        if missing_nonzero.empty:
            render_recommendation_box("Không phát hiện missing value trong dataset.", level="success")
        else:
            fig_missing = px.bar(
                missing_nonzero.head(10),
                x="column_name",
                y="missing_rate (%)",
                title="Top cột có missing value",
                text="missing_rate (%)",
            )
            st.plotly_chart(fig_missing, use_container_width=True)

with diag_col2:
    if issues_df.empty:
        render_recommendation_box("Không phát hiện lỗi dữ liệu cơ bản.", level="success")
    else:
        top_issues = (
            issues_df.sort_values(
                by=["severity", "issue_count"],
                ascending=[True, False],
            )
            .head(5)
        )

        st.markdown("#### Top Issues")
        st.dataframe(
            top_issues[
                [
                    "issue_type",
                    "column_name",
                    "severity",
                    "issue_count",
                    "issue_rate (%)",
                    "recommendation",
                ]
            ],
            use_container_width=True,
        )


st.markdown('<div class="section-title">Recommendation</div>', unsafe_allow_html=True)

if risk_level == "Low":
    render_recommendation_box(
        "Dataset có chất lượng tốt. Có thể dùng cho phân tích sau khi kiểm tra thêm các rule nghiệp vụ.",
        level="success",
    )
elif risk_level == "Medium":
    render_recommendation_box(
        "Dataset dùng được cho phân tích sơ bộ, nhưng nên xử lý các lỗi Medium/High trước khi sử dụng chính thức.",
        level="warning",
    )
else:
    render_recommendation_box(
        "Dataset có rủi ro chất lượng cao. Cần làm sạch dữ liệu trước khi dùng cho phân tích hoặc huấn luyện mô hình.",
        level="danger",
    )