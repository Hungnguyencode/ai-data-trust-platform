from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.drift.data_drift import (
    build_categorical_distribution_df,
    run_drift_detection,
)
from src.ingestion.file_loader import load_dataset
from src.utils.ui import inject_custom_css, render_metric_card, render_recommendation_box


st.set_page_config(
    page_title="Drift Analysis",
    page_icon="📉",
    layout="wide",
)

inject_custom_css()

st.markdown(
    """
    <div class="main-title">📉 Drift Detection</div>
    <div class="subtitle">
        So sánh baseline dataset và current dataset để phát hiện schema drift, data drift, PSI, KS-test và categorical distribution drift.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">1. Upload baseline và current dataset</div>', unsafe_allow_html=True)

upload_col1, upload_col2 = st.columns(2)

with upload_col1:
    baseline_file = st.file_uploader(
        "Baseline dataset",
        type=["csv", "xlsx", "xls", "json"],
        key="baseline_drift_file",
    )

with upload_col2:
    current_file = st.file_uploader(
        "Current dataset",
        type=["csv", "xlsx", "xls", "json"],
        key="current_drift_file",
    )

use_session_current = False

if "current_df" in st.session_state:
    use_session_current = st.checkbox(
        "Dùng dataset hiện tại trong session làm current dataset",
        value=False,
    )

if baseline_file is None:
    st.info("Hãy upload baseline dataset để bắt đầu so sánh drift.")
    st.stop()

try:
    baseline_df, baseline_file_type = load_dataset(baseline_file)

    if use_session_current:
        current_df = st.session_state["current_df"]
        current_file_name = st.session_state.get("current_file_name", "current_session_dataset")
        current_file_type = st.session_state.get("current_file_type", "Session")
    else:
        if current_file is None:
            st.info("Hãy upload current dataset hoặc tick chọn dùng dataset trong session.")
            st.stop()

        current_df, current_file_type = load_dataset(current_file)
        current_file_name = current_file.name

except Exception as exc:
    st.error(f"Không thể đọc dataset: {exc}")
    st.stop()

baseline_file_name = baseline_file.name

# Lưu tên file drift để report biết drift đang so sánh file nào với file nào
st.session_state["drift_baseline_file_name"] = baseline_file_name
st.session_state["drift_current_file_name"] = current_file_name

st.success("Đã đọc baseline/current dataset thành công.")

st.markdown('<div class="section-title">2. Tổng quan dữ liệu so sánh</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card(
        "Baseline",
        f"{baseline_df.shape[0]:,} × {baseline_df.shape[1]:,}",
        baseline_file_name,
    )

with col2:
    render_metric_card(
        "Current",
        f"{current_df.shape[0]:,} × {current_df.shape[1]:,}",
        current_file_name,
    )

with col3:
    row_diff = current_df.shape[0] - baseline_df.shape[0]
    render_metric_card(
        "Row Difference",
        f"{row_diff:+,}",
        "Current rows - baseline rows",
    )

with col4:
    col_diff = current_df.shape[1] - baseline_df.shape[1]
    render_metric_card(
        "Column Difference",
        f"{col_diff:+,}",
        "Current columns - baseline columns",
    )

drift_report = run_drift_detection(
    baseline_df=baseline_df,
    current_df=current_df,
)

# Gắn tên file baseline/current trực tiếp vào drift_report
# để report HTML không bị hiểu nhầm là dùng sample_quality_issues.csv để drift.
drift_report["baseline_file_name"] = baseline_file_name
drift_report["current_file_name"] = current_file_name

st.session_state["current_drift_report"] = drift_report

summary = drift_report["summary"]
schema_report = drift_report["schema_report"]
numeric_drift_df = drift_report["numeric_drift_df"]
categorical_drift_df = drift_report["categorical_drift_df"]
all_drift_df = drift_report["all_drift_df"]

st.markdown('<div class="section-title">3. Tổng quan Drift Detection</div>', unsafe_allow_html=True)

status = "low"

if summary["overall_drift_level"] == "Medium":
    status = "medium"
elif summary["overall_drift_level"] == "High":
    status = "high"
elif summary["overall_drift_level"] == "None":
    status = "low"

drift_col1, drift_col2, drift_col3, drift_col4 = st.columns(4)

with drift_col1:
    render_metric_card(
        "Drift Score",
        f"{summary['drift_score']}/100",
        "Điểm càng cao càng ổn định",
        status=status,
    )

with drift_col2:
    render_metric_card(
        "Overall Drift",
        summary["overall_drift_level"],
        "Mức drift tổng quan",
        status=status,
    )

with drift_col3:
    render_metric_card(
        "Drifted Columns",
        str(summary["drifted_columns"]),
        f"{summary['drift_rate (%)']}% common columns",
        status=status,
    )

with drift_col4:
    render_metric_card(
        "Schema Changes",
        str(summary["schema_drift_count"]),
        "Added/removed/dtype changes",
        status=status,
    )

if summary["overall_drift_level"] == "None":
    render_recommendation_box(
        "Không phát hiện drift đáng kể. Current dataset tương đối ổn định so với baseline.",
        level="success",
    )
elif summary["overall_drift_level"] == "Low":
    render_recommendation_box(
        "Có drift nhẹ. Nên theo dõi thêm nếu dataset dùng cho dashboard hoặc mô hình định kỳ.",
        level="warning",
    )
elif summary["overall_drift_level"] == "Medium":
    render_recommendation_box(
        "Có drift mức trung bình. Nên kiểm tra các cột bị drift trước khi dùng dữ liệu cho phân tích hoặc training.",
        level="warning",
    )
else:
    render_recommendation_box(
        "Có drift mạnh. Không nên dùng current dataset thay thế baseline nếu chưa điều tra nguyên nhân thay đổi phân phối.",
        level="danger",
    )

st.markdown('<div class="section-title">4. Schema Drift</div>', unsafe_allow_html=True)

schema_summary = schema_report["summary"]
schema_changes_df = schema_report["changes_df"]

schema_col1, schema_col2, schema_col3, schema_col4 = st.columns(4)

schema_col1.metric("Baseline columns", schema_summary["baseline_columns"])
schema_col2.metric("Current columns", schema_summary["current_columns"])
schema_col3.metric("Added columns", schema_summary["added_columns"])
schema_col4.metric("Removed columns", schema_summary["removed_columns"])

if schema_changes_df.empty:
    st.success("Không phát hiện schema drift.")
else:
    st.warning("Phát hiện schema drift.")
    st.dataframe(schema_changes_df, use_container_width=True)

st.markdown('<div class="section-title">5. Numeric Drift: PSI + KS-test</div>', unsafe_allow_html=True)

if numeric_drift_df.empty:
    st.info("Không có cột numeric chung phù hợp để kiểm tra drift.")
else:
    st.dataframe(numeric_drift_df, use_container_width=True)

    numeric_chart_df = numeric_drift_df.sort_values(by="psi", ascending=False)

    fig_numeric = px.bar(
        numeric_chart_df,
        x="column_name",
        y="psi",
        color="drift_level",
        text="psi",
        title="PSI theo cột numeric",
    )
    fig_numeric.update_traces(textposition="outside")
    fig_numeric.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig_numeric, use_container_width=True)

    selected_numeric_col = st.selectbox(
        "Chọn cột numeric để xem phân phối baseline/current",
        numeric_drift_df["column_name"].tolist(),
    )

    if selected_numeric_col:
        dist_df = baseline_df[[selected_numeric_col]].copy()
        dist_df["dataset"] = "baseline"

        current_dist_df = current_df[[selected_numeric_col]].copy()
        current_dist_df["dataset"] = "current"

        combined_dist_df = px.data.tips().iloc[0:0].copy()
        combined_dist_df = None

        plot_df = __import__("pandas").concat(
            [dist_df, current_dist_df],
            ignore_index=True,
        )

        fig_dist = px.histogram(
            plot_df,
            x=selected_numeric_col,
            color="dataset",
            barmode="overlay",
            marginal="box",
            title=f"Phân phối baseline/current — {selected_numeric_col}",
        )
        st.plotly_chart(fig_dist, use_container_width=True)

st.markdown('<div class="section-title">6. Categorical Distribution Drift</div>', unsafe_allow_html=True)

if categorical_drift_df.empty:
    st.info("Không có cột categorical chung phù hợp để kiểm tra drift.")
else:
    st.dataframe(categorical_drift_df, use_container_width=True)

    categorical_chart_df = categorical_drift_df.sort_values(
        by="distribution_diff",
        ascending=False,
    )

    fig_cat = px.bar(
        categorical_chart_df,
        x="column_name",
        y="distribution_diff",
        color="drift_level",
        text="distribution_diff",
        title="Distribution difference theo cột categorical",
    )
    fig_cat.update_traces(textposition="outside")
    fig_cat.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig_cat, use_container_width=True)

    selected_cat_col = st.selectbox(
        "Chọn cột categorical để xem phân phối baseline/current",
        categorical_drift_df["column_name"].tolist(),
    )

    if selected_cat_col:
        cat_dist_df = build_categorical_distribution_df(
            baseline_df=baseline_df,
            current_df=current_df,
            column_name=selected_cat_col,
        )

        st.dataframe(cat_dist_df, use_container_width=True)

        melted_cat_df = cat_dist_df.melt(
            id_vars="value",
            value_vars=["baseline_pct", "current_pct"],
            var_name="dataset",
            value_name="percentage",
        )

        fig_cat_dist = px.bar(
            melted_cat_df,
            x="value",
            y="percentage",
            color="dataset",
            barmode="group",
            title=f"So sánh phân phối categorical — {selected_cat_col}",
        )
        fig_cat_dist.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig_cat_dist, use_container_width=True)

st.markdown('<div class="section-title">7. Danh sách cột bị drift</div>', unsafe_allow_html=True)

if all_drift_df.empty:
    st.info("Không có kết quả drift để hiển thị.")
else:
    drifted_only_df = all_drift_df[
        all_drift_df["drift_level"] != "No significant drift"
    ].copy()

    if drifted_only_df.empty:
        st.success("Không có cột nào bị drift đáng kể.")
    else:
        st.warning(f"Phát hiện {drifted_only_df['column_name'].nunique()} cột bị drift.")
        st.dataframe(drifted_only_df, use_container_width=True)

st.markdown('<div class="section-title">8. Diễn giải kết quả</div>', unsafe_allow_html=True)

st.markdown(
    f"""
- **Drift Score:** `{summary['drift_score']}/100`
- **Overall Drift Level:** `{summary['overall_drift_level']}`
- **Schema Drift Count:** `{summary['schema_drift_count']}`
- **Drifted Columns:** `{summary['drifted_columns']}`
- **High Drift Columns:** `{summary['high_drift_columns']}`
- **Moderate Drift Columns:** `{summary['moderate_drift_columns']}`

Version 0.8 dùng:
- **Schema drift** để kiểm tra cột thêm/xóa/đổi kiểu dữ liệu.
- **PSI** cho numeric drift.
- **KS-test** cho phân phối numeric.
- **Chi-square + distribution difference** cho categorical drift.
- **Drift chart** để trực quan hóa sự khác biệt giữa baseline và current.
"""
)