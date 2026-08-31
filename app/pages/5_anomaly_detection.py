from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.anomaly.anomaly_engine import run_anomaly_detection
from src.utils.ui import inject_custom_css, render_metric_card, render_recommendation_box

st.set_page_config(
    page_title="Anomaly Detection",
    page_icon="🚨",
    layout="wide",
)

inject_custom_css()

st.markdown(
    """
    <div class="main-title">🚨 Anomaly Detection</div>
    <div class="subtitle">
        Phát hiện dòng dữ liệu bất thường bằng IQR, Z-score và Isolation Forest.
    </div>
    """,
    unsafe_allow_html=True,
)


if "current_df" not in st.session_state:
    st.warning("Bạn chưa upload dataset. Hãy vào trang Upload Dataset trước.")
    st.stop()


df = st.session_state["current_df"]

st.markdown('<div class="section-title">1. Cấu hình phát hiện bất thường</div>', unsafe_allow_html=True)

col_config1, col_config2 = st.columns(2)

with col_config1:
    zscore_threshold = st.slider(
        "Z-score threshold",
        min_value=2.0,
        max_value=5.0,
        value=3.0,
        step=0.1,
    )

with col_config2:
    contamination = st.slider(
        "Isolation Forest contamination",
        min_value=0.01,
        max_value=0.30,
        value=0.10,
        step=0.01,
    )


anomaly_report = run_anomaly_detection(
    df,
    zscore_threshold=zscore_threshold,
    isolation_contamination=contamination,
)

st.session_state["current_anomaly_report"] = anomaly_report

summary = anomaly_report["summary"]
summary_df = anomaly_report["summary_df"]
combined_outlier_rows_df = anomaly_report["combined_outlier_rows_df"]
iqr_result = anomaly_report["iqr_result"]
zscore_result = anomaly_report["zscore_result"]
isolation_result = anomaly_report["isolation_forest_result"]


st.markdown('<div class="section-title">2. Tổng quan Anomaly Detection</div>', unsafe_allow_html=True)

status = "low"
if summary["risk_level"] == "Medium":
    status = "medium"
elif summary["risk_level"] == "High":
    status = "high"
elif summary["risk_level"] == "Critical":
    status = "critical"

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card(
        "Total rows",
        str(summary["total_rows"]),
        "Tổng số dòng kiểm tra",
    )

with col2:
    render_metric_card(
        "Anomaly rows",
        str(summary["total_anomaly_rows"]),
        "Số dòng bất thường unique",
        status=status,
    )

with col3:
    render_metric_card(
        "Anomaly rate",
        f"{summary['anomaly_rate (%)']}%",
        "Tỷ lệ dòng bất thường",
        status=status,
    )

with col4:
    render_metric_card(
        "Anomaly Score",
        f"{summary['anomaly_score']}/100",
        f"Risk Level: {summary['risk_level']}",
        status=status,
    )


if summary["risk_level"] == "Low":
    render_recommendation_box(
        "Dataset có ít bất thường theo các detector hiện tại.",
        level="success",
    )
elif summary["risk_level"] == "Medium":
    render_recommendation_box(
        "Dataset có một số dòng bất thường. Nên kiểm tra các dòng bị đánh dấu trước khi huấn luyện mô hình.",
        level="warning",
    )
else:
    render_recommendation_box(
        "Dataset có tỷ lệ bất thường cao. Cần kiểm tra dữ liệu nguồn, rule nghiệp vụ và xử lý outlier trước khi dùng cho AI/ML.",
        level="danger",
    )


st.markdown('<div class="section-title">3. Outlier summary theo phương pháp</div>', unsafe_allow_html=True)

st.dataframe(summary_df, use_container_width=True)

fig_summary = px.bar(
    summary_df,
    x="method",
    y="total_outlier_rows",
    text="total_outlier_rows",
    title="Số dòng bất thường theo từng phương pháp",
)
fig_summary.update_traces(textposition="outside")
st.plotly_chart(fig_summary, use_container_width=True)


st.markdown('<div class="section-title">4. Chi tiết IQR detector</div>', unsafe_allow_html=True)

iqr_summary_df = iqr_result["summary_df"]

if iqr_summary_df.empty:
    st.info("IQR detector không có cột numeric phù hợp để kiểm tra.")
else:
    st.dataframe(iqr_summary_df, use_container_width=True)

    iqr_nonzero = iqr_summary_df[iqr_summary_df["outlier_count"] > 0]

    if not iqr_nonzero.empty:
        fig_iqr = px.bar(
            iqr_nonzero,
            x="column_name",
            y="outlier_count",
            text="outlier_count",
            title="IQR outlier count theo cột",
        )
        st.plotly_chart(fig_iqr, use_container_width=True)


st.markdown('<div class="section-title">5. Chi tiết Z-score detector</div>', unsafe_allow_html=True)

zscore_summary_df = zscore_result["summary_df"]

if zscore_summary_df.empty:
    st.info("Z-score detector không có cột numeric phù hợp để kiểm tra.")
else:
    st.dataframe(zscore_summary_df, use_container_width=True)

    zscore_nonzero = zscore_summary_df[zscore_summary_df["outlier_count"] > 0]

    if not zscore_nonzero.empty:
        fig_zscore = px.bar(
            zscore_nonzero,
            x="column_name",
            y="outlier_count",
            text="outlier_count",
            title="Z-score outlier count theo cột",
        )
        st.plotly_chart(fig_zscore, use_container_width=True)


st.markdown('<div class="section-title">6. Chi tiết Isolation Forest</div>', unsafe_allow_html=True)

iso_summary = isolation_result["summary"]

if not iso_summary["used"]:
    st.info(iso_summary["reason"])
else:
    iso_col1, iso_col2, iso_col3 = st.columns(3)

    iso_col1.metric("Numeric columns", len(iso_summary["numeric_columns"]))
    iso_col2.metric("Contamination", iso_summary["contamination"])
    iso_col3.metric("Outlier rows", iso_summary["total_outlier_rows"])

    scores_df = isolation_result["scores_df"]

    st.dataframe(scores_df, use_container_width=True)

    fig_iso = px.histogram(
        scores_df,
        x="anomaly_score",
        color="is_anomaly",
        title="Phân phối Isolation Forest anomaly score",
    )
    st.plotly_chart(fig_iso, use_container_width=True)


st.markdown('<div class="section-title">7. Danh sách dòng bất thường tổng hợp</div>', unsafe_allow_html=True)

if combined_outlier_rows_df.empty:
    st.success("Không phát hiện dòng bất thường tổng hợp.")
else:
    st.warning(f"Phát hiện {len(combined_outlier_rows_df)} dòng bất thường unique.")
    st.dataframe(combined_outlier_rows_df, use_container_width=True)