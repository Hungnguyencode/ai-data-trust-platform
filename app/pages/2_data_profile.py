from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


st.set_page_config(
    page_title="Data Profile",
    page_icon="📊",
    layout="wide",
)


st.title("📊 Data Profile")
st.caption("Xem chi tiết kết quả phân tích dataset đã upload.")


if "current_df" not in st.session_state or "current_profile" not in st.session_state:
    st.warning("Bạn chưa upload dataset. Hãy vào trang Upload Dataset trước.")
    st.stop()


df = st.session_state["current_df"]
profile = st.session_state["current_profile"]
file_name = st.session_state.get("current_file_name", "Unknown file")
file_type = st.session_state.get("current_file_type", "Unknown type")


st.subheader("Thông tin file")

col1, col2, col3 = st.columns(3)
col1.metric("Tên file", file_name)
col2.metric("Loại file", file_type)
col3.metric("Kích thước DataFrame", f"{df.shape[0]:,} x {df.shape[1]:,}")


st.subheader("1. Basic information")

basic_info = profile["basic_info"]

info_col1, info_col2, info_col3, info_col4 = st.columns(4)
info_col1.metric("Total rows", f"{basic_info['total_rows']:,}")
info_col2.metric("Total columns", f"{basic_info['total_columns']:,}")
info_col3.metric("Missing cells", f"{basic_info['missing_cells']:,}")
info_col4.metric("Duplicate rows", f"{basic_info['duplicate_rows']:,}")


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