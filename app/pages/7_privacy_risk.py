from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.privacy.pii_detector import run_privacy_scan
from src.utils.ui import inject_custom_css, render_metric_card, render_recommendation_box


st.set_page_config(
    page_title="Privacy Risk",
    page_icon="🔐",
    layout="wide",
)

inject_custom_css()

st.markdown(
    """
    <div class="main-title">🔐 Privacy Risk Scanner</div>
    <div class="subtitle">
        Phát hiện dữ liệu nhạy cảm như email, số điện thoại, họ tên, địa chỉ và CCCD/CMND.
    </div>
    """,
    unsafe_allow_html=True,
)

if "current_df" not in st.session_state:
    st.warning("Bạn chưa upload dataset. Hãy vào trang Upload Dataset trước.")
    st.stop()

df = st.session_state["current_df"]

privacy_report = run_privacy_scan(df)
st.session_state["current_privacy_report"] = privacy_report

summary = privacy_report["summary"]
findings_df = privacy_report["findings_df"]

status = "low"
if summary["risk_level"] == "Medium":
    status = "medium"
elif summary["risk_level"] == "High":
    status = "high"
elif summary["risk_level"] == "Critical":
    status = "critical"

st.markdown('<div class="section-title">1. Tổng quan Privacy Risk</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card(
        "Privacy Safety Score",
        f"{summary['privacy_safety_score']}/100",
        "Điểm càng cao càng an toàn",
        status=status,
    )

with col2:
    render_metric_card(
        "Risk Level",
        summary["risk_level"],
        "Mức rủi ro riêng tư",
        status=status,
    )

with col3:
    render_metric_card(
        "PII Columns",
        f"{summary['pii_columns']} / {summary['total_columns']}",
        "Số cột có dấu hiệu nhạy cảm",
        status=status,
    )

with col4:
    render_metric_card(
        "PII Cell Rate",
        f"{summary['pii_cell_rate (%)']}%",
        "Tỷ lệ ô có khả năng chứa PII",
        status=status,
    )

if summary["risk_level"] == "Low":
    render_recommendation_box(
        "Dataset có rủi ro riêng tư thấp theo các rule hiện tại.",
        level="success",
    )
elif summary["risk_level"] == "Medium":
    render_recommendation_box(
        "Dataset có một số cột chứa dữ liệu định danh. Nên mask/hash trước khi chia sẻ hoặc huấn luyện mô hình.",
        level="warning",
    )
else:
    render_recommendation_box(
        "Dataset có rủi ro riêng tư cao. Không nên public dữ liệu khi chưa ẩn danh hóa các trường nhạy cảm.",
        level="danger",
    )

st.markdown('<div class="section-title">2. Danh sách dữ liệu nhạy cảm phát hiện</div>', unsafe_allow_html=True)

if findings_df.empty:
    st.success("Không phát hiện dữ liệu nhạy cảm theo rule hiện tại.")
    st.stop()

st.dataframe(findings_df, use_container_width=True)

st.markdown('<div class="section-title">3. Biểu đồ Privacy Risk</div>', unsafe_allow_html=True)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    pii_type_count = (
        findings_df.groupby("pii_type")["match_count"]
        .sum()
        .reset_index()
        .sort_values(by="match_count", ascending=False)
    )

    fig_type = px.bar(
        pii_type_count,
        x="pii_type",
        y="match_count",
        text="match_count",
        title="Số lượng PII theo loại",
    )
    fig_type.update_traces(textposition="outside")
    st.plotly_chart(fig_type, use_container_width=True)

with chart_col2:
    severity_count = findings_df["severity"].value_counts().reset_index()
    severity_count.columns = ["severity", "count"]

    fig_severity = px.pie(
        severity_count,
        names="severity",
        values="count",
        title="Tỷ lệ Privacy Risk theo severity",
        hole=0.45,
    )
    st.plotly_chart(fig_severity, use_container_width=True)

st.markdown('<div class="section-title">4. Chi tiết theo cột</div>', unsafe_allow_html=True)

selected_pii_type = st.selectbox(
    "Lọc theo loại dữ liệu nhạy cảm",
    ["All"] + sorted(findings_df["pii_type"].unique().tolist()),
)

filtered_df = findings_df.copy()

if selected_pii_type != "All":
    filtered_df = filtered_df[filtered_df["pii_type"] == selected_pii_type]

st.dataframe(filtered_df, use_container_width=True)

st.markdown('<div class="section-title">5. Recommendation Box</div>', unsafe_allow_html=True)

high_risk_df = findings_df[findings_df["severity"].isin(["High", "Critical"])]

if not high_risk_df.empty:
    high_risk_columns = ", ".join(high_risk_df["column_name"].unique().tolist())

    render_recommendation_box(
        f"""
        <b>Ưu tiên xử lý:</b> Các cột <b>{high_risk_columns}</b> có rủi ro riêng tư cao.
        Nên mask, hash, pseudonymize hoặc loại bỏ trước khi chia sẻ dataset.
        """,
        level="danger",
    )
else:
    render_recommendation_box(
        """
        <b>Khuyến nghị:</b> Dataset có thể dùng cho demo nội bộ, nhưng vẫn nên kiểm tra lại
        các cột định danh như email, phone, name, address nếu dữ liệu đến từ người thật.
        """,
        level="warning",
    )

st.markdown('<div class="section-title">6. Diễn giải kết quả</div>', unsafe_allow_html=True)

st.markdown(
    f"""
- **Privacy Safety Score:** `{summary['privacy_safety_score']}/100`
- **Risk Level:** `{summary['risk_level']}`
- **Số cột có PII:** `{summary['pii_columns']}/{summary['total_columns']}`
- **Tỷ lệ ô có PII:** `{summary['pii_cell_rate (%)']}%`

Version 0.7 dùng rule-based scanner để phát hiện dữ liệu nhạy cảm. Các rule gồm:
email regex, phone regex, citizen ID regex, column-name heuristic cho họ tên và địa chỉ.
"""
)