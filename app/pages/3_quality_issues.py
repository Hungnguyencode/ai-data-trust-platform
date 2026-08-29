from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.utils.ui import inject_custom_css, render_metric_card, render_recommendation_box
from src.validation.rule_engine import run_quality_checks

st.set_page_config(
    page_title="Quality Issues",
    page_icon="⚠️",
    layout="wide",
)

inject_custom_css()


st.markdown(
    """
    <div class="main-title">⚠️ Quality Issues</div>
    <div class="subtitle">Phát hiện, phân loại và diễn giải các lỗi dữ liệu cơ bản trong dataset.</div>
    """,
    unsafe_allow_html=True,
)


if "current_df" not in st.session_state:
    st.warning("Bạn chưa upload dataset. Hãy vào trang Upload Dataset trước.")
    st.stop()


df = st.session_state["current_df"]

quality_report = run_quality_checks(df)
st.session_state["current_quality_report"] = quality_report

summary = quality_report["summary"]
issues_df = quality_report["issues_df"]


st.markdown('<div class="section-title">1. Tổng quan lỗi dữ liệu</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    render_metric_card("Tổng số lỗi", str(summary["total_issues"]), "Số issue group phát hiện")

with col2:
    render_metric_card("High", str(summary["high_issues"]), "Lỗi nghiêm trọng", status="high")

with col3:
    render_metric_card("Medium", str(summary["medium_issues"]), "Lỗi cần xử lý", status="medium")

with col4:
    render_metric_card("Low", str(summary["low_issues"]), "Lỗi nhẹ", status="low")

with col5:
    render_metric_card(
        "Cột bị ảnh hưởng",
        f"{summary['affected_columns']} / {summary['total_columns']}",
        "Affected columns",
    )


if issues_df.empty:
    render_recommendation_box(
        "Không phát hiện lỗi dữ liệu cơ bản. Dataset đang ở trạng thái tốt ở Version 0.4.",
        level="success",
    )
    st.stop()


st.markdown('<div class="section-title">2. Top issues cần ưu tiên</div>', unsafe_allow_html=True)

top_issues = issues_df.head(5)

st.dataframe(
    top_issues[
        [
            "issue_type",
            "column_name",
            "severity",
            "issue_count",
            "issue_rate (%)",
            "description",
            "recommendation",
        ]
    ],
    use_container_width=True,
)


top_high = issues_df[issues_df["severity"] == "High"]

if not top_high.empty:
    render_recommendation_box(
        "Dataset có lỗi mức <b>High</b>. Nên ưu tiên xử lý missing value nghiêm trọng, duplicate rows hoặc lỗi validity trước khi dùng cho phân tích/AI.",
        level="danger",
    )
elif (issues_df["severity"] == "Medium").any():
    render_recommendation_box(
        "Dataset có lỗi mức <b>Medium</b>. Có thể dùng để phân tích sơ bộ, nhưng nên xử lý trước khi dùng chính thức.",
        level="warning",
    )
else:
    render_recommendation_box(
        "Dataset chỉ có lỗi mức <b>Low</b>. Dữ liệu tương đối ổn ở bước kiểm tra cơ bản.",
        level="success",
    )


st.markdown('<div class="section-title">3. Bộ lọc lỗi</div>', unsafe_allow_html=True)

filter_col1, filter_col2 = st.columns(2)

severity_options = ["All"] + sorted(issues_df["severity"].unique().tolist())
issue_type_options = ["All"] + sorted(issues_df["issue_type"].unique().tolist())

selected_severity = filter_col1.selectbox("Lọc theo severity", severity_options)
selected_issue_type = filter_col2.selectbox("Lọc theo issue type", issue_type_options)

filtered_df = issues_df.copy()

if selected_severity != "All":
    filtered_df = filtered_df[filtered_df["severity"] == selected_severity]

if selected_issue_type != "All":
    filtered_df = filtered_df[filtered_df["issue_type"] == selected_issue_type]


st.markdown('<div class="section-title">4. Danh sách lỗi dữ liệu</div>', unsafe_allow_html=True)

st.dataframe(filtered_df, use_container_width=True)


st.markdown('<div class="section-title">5. Biểu đồ tổng quan lỗi</div>', unsafe_allow_html=True)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    issue_type_count = (
        issues_df.groupby("issue_type")["issue_count"]
        .sum()
        .reset_index()
        .sort_values(by="issue_count", ascending=False)
    )

    fig_issue_type = px.bar(
        issue_type_count,
        x="issue_type",
        y="issue_count",
        title="Số lượng lỗi theo loại",
        text="issue_count",
    )
    fig_issue_type.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig_issue_type, use_container_width=True)

with chart_col2:
    severity_count = issues_df["severity"].value_counts().reset_index()
    severity_count.columns = ["severity", "count"]

    fig_severity = px.pie(
        severity_count,
        names="severity",
        values="count",
        title="Tỷ lệ lỗi theo severity",
        hole=0.45,
    )
    st.plotly_chart(fig_severity, use_container_width=True)


st.markdown('<div class="section-title">6. Chi tiết theo từng nhóm kiểm tra</div>', unsafe_allow_html=True)

with st.expander("Missing value checker"):
    st.dataframe(quality_report["missing_summary"], use_container_width=True)

with st.expander("Duplicate checker"):
    duplicate_rows_df = quality_report["duplicate_rows_df"]

    if duplicate_rows_df.empty:
        st.success("Không phát hiện dòng trùng lặp hoàn toàn.")
    else:
        st.warning(f"Phát hiện {len(duplicate_rows_df)} dòng nằm trong nhóm duplicate.")
        st.dataframe(duplicate_rows_df, use_container_width=True)

with st.expander("Type checker"):
    type_issues_df = quality_report["type_issues_df"]

    if type_issues_df.empty:
        st.info("Không có cột nào được kiểm tra kiểu dữ liệu theo heuristic hiện tại.")
    else:
        st.dataframe(type_issues_df, use_container_width=True)

with st.expander("Range checker"):
    range_issues_df = quality_report["range_issues_df"]

    if range_issues_df.empty:
        st.info("Không có rule range nào được áp dụng.")
    else:
        st.dataframe(range_issues_df, use_container_width=True)

with st.expander("Categorical value checker"):
    categorical_issues_df = quality_report["categorical_issues_df"]

    if categorical_issues_df.empty:
        st.info("Không có rule categorical nào được áp dụng.")
    else:
        st.dataframe(categorical_issues_df, use_container_width=True)