from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from database.db import test_connection
from database.repositories.scan_repository import save_dataset_metadata
from src.ingestion.file_loader import load_dataset
from src.profiling.profiler import profile_dataset

st.set_page_config(
    page_title="Upload Dataset",
    page_icon="📤",
    layout="wide",
)


st.title("📤 Upload Dataset")
st.caption("Upload dataset để hệ thống phân tích tổng quan chất lượng dữ liệu.")


with st.expander("Database connection"):
    if st.button("Test SQL Server connection"):
        ok, message = test_connection()

        if ok:
            st.success(message)
        else:
            st.error(message)


uploaded_file = st.file_uploader(
    "Chọn file dữ liệu",
    type=["csv", "xlsx", "xls", "json"],
)


if uploaded_file is not None:
    try:
        df, file_type = load_dataset(uploaded_file)
        profile = profile_dataset(df)

        st.session_state["current_df"] = df
        st.session_state["current_file_name"] = uploaded_file.name
        st.session_state["current_file_type"] = file_type
        st.session_state["current_profile"] = profile

        st.success(f"Đã đọc file thành công: {uploaded_file.name}")

        basic_info = profile["basic_info"]

        st.subheader("1. Tổng quan dataset")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Số dòng", f"{basic_info['total_rows']:,}")
        col2.metric("Số cột", f"{basic_info['total_columns']:,}")
        col3.metric("Missing rate", f"{basic_info['missing_rate']}%")
        col4.metric("Duplicate rate", f"{basic_info['duplicate_rate']}%")

        save_col1, save_col2 = st.columns([1, 3])

        with save_col1:
            if st.button("Save dataset metadata"):
                try:
                    dataset_id = save_dataset_metadata(
                        file_name=uploaded_file.name,
                        file_type=file_type,
                        df=df,
                        profile=profile,
                    )

                    st.session_state["current_dataset_id"] = dataset_id
                    st.success(f"Đã lưu dataset metadata. dataset_id = {dataset_id}")

                except Exception as exc:
                    st.error(f"Không thể lưu dataset metadata vào SQL Server: {exc}")

        with save_col2:
            st.info(
                "Nút này chỉ lưu metadata dataset. Sau khi mở tab Trust Score, hệ thống sẽ có thể lưu full scan gồm score và quality issues."
            )

        st.subheader("2. Preview dữ liệu")
        st.dataframe(df.head(50), use_container_width=True)

        st.subheader("3. Kiểu dữ liệu tự động nhận diện")

        column_types = profile["column_types"]

        type_col1, type_col2, type_col3, type_col4, type_col5 = st.columns(5)

        type_col1.metric("Numeric", len(column_types["numeric_columns"]))
        type_col2.metric("Categorical", len(column_types["categorical_columns"]))
        type_col3.metric("Datetime", len(column_types["datetime_columns"]))
        type_col4.metric("Boolean", len(column_types["boolean_columns"]))
        type_col5.metric("Text", len(column_types["text_columns"]))

        with st.expander("Xem danh sách cột theo loại"):
            st.write("**Numeric columns:**", column_types["numeric_columns"])
            st.write("**Categorical columns:**", column_types["categorical_columns"])
            st.write("**Datetime columns:**", column_types["datetime_columns"])
            st.write("**Boolean columns:**", column_types["boolean_columns"])
            st.write("**Text columns:**", column_types["text_columns"])

        st.subheader("4. Missing value theo cột")

        missing_summary = profile["missing_summary"]

        st.dataframe(missing_summary, use_container_width=True)

        missing_nonzero = missing_summary[missing_summary["missing_count"] > 0]

        if not missing_nonzero.empty:
            fig = px.bar(
                missing_nonzero,
                x="column_name",
                y="missing_rate (%)",
                title="Tỷ lệ missing value theo cột",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("Không phát hiện missing value trong dataset.")

        st.subheader("5. Duplicate rows")

        duplicate_summary = profile["duplicate_summary"]

        dup_col1, dup_col2 = st.columns(2)
        dup_col1.metric("Số dòng trùng", duplicate_summary["duplicate_rows"])
        dup_col2.metric("Tỷ lệ dòng trùng", f"{duplicate_summary['duplicate_rate']}%")

        st.subheader("6. Schema summary")

        st.dataframe(profile["schema_summary"], use_container_width=True)

        st.info("Dataset đã được lưu trong session. Bạn có thể mở trang Data Profile, Quality Issues hoặc Trust Score.")

    except Exception as exc:
        st.error(str(exc))

else:
    st.warning("Vui lòng upload một file CSV, Excel hoặc JSON.")