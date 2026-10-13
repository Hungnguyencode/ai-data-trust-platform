from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))




from app.ui.layout import build_journey_html, render_page_header

render_page_header(
    "Data Profile",
    'Xem chi tiết kết quả phân tích dataset đã upload.',
)

st.markdown(
    build_journey_html(active_step="Data Profile"),
    unsafe_allow_html=True,
)


if "current_df" not in st.session_state or "current_profile" not in st.session_state:
    st.warning("Bạn chưa upload dataset. Hãy vào trang Upload Dataset trước.")
    st.stop()


df = st.session_state["current_df"]
profile = st.session_state["current_profile"]
file_name = st.session_state.get("current_file_name", "Unknown file")
file_type = st.session_state.get("current_file_type", "Unknown type")


st.subheader("Thông tin file")

col1, col2, col3 = st.columns(3)
with col1.container(border=True):
    st.caption("T\u00ean file")
    st.write(file_name)
with col2.container(border=True):
    st.metric("Loại file", file_type)
with col3.container(border=True):
    st.metric("Kích thước DataFrame", f"{df.shape[0]:,} x {df.shape[1]:,}")


st.subheader("1. Basic information")

basic_info = profile["basic_info"]

info_col1, info_col2, info_col3, info_col4 = st.columns(4)
with info_col1.container(border=True):
    st.metric("Total rows", f"{basic_info['total_rows']:,}")
with info_col2.container(border=True):
    st.metric("Total columns", f"{basic_info['total_columns']:,}")
with info_col3.container(border=True):
    st.metric("Missing cells", f"{basic_info['missing_cells']:,}")
with info_col4.container(border=True):
    st.metric("Duplicate rows", f"{basic_info['duplicate_rows']:,}")


st.subheader("2. Schema summary")
st.dataframe(profile["schema_summary"], use_container_width=True)


st.subheader("3. Missing value summary")

missing_summary = profile["missing_summary"]
st.dataframe(missing_summary, use_container_width=True)

missing_nonzero = missing_summary[missing_summary["missing_count"] > 0]

if not missing_nonzero.empty:
    fig = px.bar(
        missing_nonzero,
        x="column_name",
        y="missing_count",
        title="Số lượng missing value theo cột",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.success("Không phát hiện missing value.")


st.subheader("4. Numeric summary")

numeric_summary = profile["numeric_summary"]

if numeric_summary.empty:
    st.info("Dataset không có cột numeric.")
else:
    st.dataframe(numeric_summary, use_container_width=True)

    numeric_columns = profile["column_types"]["numeric_columns"]
    selected_numeric_col = st.selectbox(
        "Chọn cột numeric để xem phân phối",
        numeric_columns,
    )

    if selected_numeric_col:
        fig = px.histogram(
            df,
            x=selected_numeric_col,
            title=f"Phân phối của cột {selected_numeric_col}",
        )
        st.plotly_chart(fig, use_container_width=True)


st.subheader("5. Categorical summary")

categorical_summary = profile["categorical_summary"]

if categorical_summary.empty:
    st.info("Dataset không có cột categorical/text.")
else:
    st.dataframe(categorical_summary, use_container_width=True)

    categorical_columns = (
        profile["column_types"]["categorical_columns"]
        + profile["column_types"]["text_columns"]
        + profile["column_types"]["boolean_columns"]
    )

    if categorical_columns:
        selected_cat_col = st.selectbox(
            "Chọn cột categorical để xem top giá trị",
            categorical_columns,
        )

        if selected_cat_col:
            value_counts = (
                df[selected_cat_col]
                .value_counts(dropna=False)
                .head(20)
                .reset_index()
            )
            value_counts.columns = [selected_cat_col, "count"]

            fig = px.bar(
                value_counts,
                x=selected_cat_col,
                y="count",
                title=f"Top giá trị phổ biến của cột {selected_cat_col}",
            )
            st.plotly_chart(fig, use_container_width=True)


st.subheader("6. Data preview")
st.dataframe(df.head(100), use_container_width=True)