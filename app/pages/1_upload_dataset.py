from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import test_connection
from database.repositories.scan_repository import save_dataset_metadata
from src.ingestion.ingestion_service import calculate_sha256, ingest_dataset
from src.profiling.profiler import profile_dataset

DERIVED_DATASET_STATE_KEYS = (
    "current_dataset_id",
    "current_quality_report",
    "current_trust_score_report",
    "current_anomaly_report",
    "current_privacy_report",
    "current_drift_report",
    "drift_baseline_file_name",
    "drift_current_file_name",
    "last_saved_scan",
)


def clear_derived_dataset_state() -> None:
    for key in DERIVED_DATASET_STATE_KEYS:
        st.session_state.pop(key, None)


def get_cached_ingestion_metadata() -> dict[str, Any] | None:
    metadata = st.session_state.get("current_ingestion_metadata")
    return metadata if isinstance(metadata, dict) else None


def is_same_uploaded_dataset(*, file_name: str, content_sha256: str) -> bool:
    metadata = get_cached_ingestion_metadata()
    if metadata is None:
        return False

    return (
        metadata.get("file_name") == file_name
        and metadata.get("content_sha256") == content_sha256
        and "current_df" in st.session_state
        and "current_profile" in st.session_state
    )


def format_bytes(byte_size: int) -> str:
    size = float(byte_size)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size):,} {unit}" if unit == "B" else f"{size:,.2f} {unit}"
        size /= 1024
    return f"{byte_size:,} B"


st.set_page_config(
    page_title="Upload Dataset",
    page_icon="📤",
    layout="wide",
)

st.title("📤 Upload Dataset")
st.caption(
    "Ingest dataset, lưu bản raw gốc và tạo metadata truy vết "
    "trước khi phân tích chất lượng dữ liệu."
)

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
        uploaded_sha256 = calculate_sha256(uploaded_file.getvalue())
        same_dataset = is_same_uploaded_dataset(
            file_name=uploaded_file.name,
            content_sha256=uploaded_sha256,
        )

        if same_dataset:
            df = st.session_state["current_df"]
            profile = st.session_state["current_profile"]
            ingestion_metadata = get_cached_ingestion_metadata()
            if ingestion_metadata is None:
                raise RuntimeError("Không tìm thấy ingestion metadata trong session.")
            file_type = str(ingestion_metadata["file_type"])
            is_new_ingestion = False
        else:
            ingestion_result = ingest_dataset(uploaded_file, persist_raw=True)
            df = ingestion_result.dataframe
            ingestion_metadata = ingestion_result.metadata.to_dict()
            file_type = ingestion_result.metadata.file_type
            profile = profile_dataset(df)

            clear_derived_dataset_state()

            st.session_state["current_df"] = df
            st.session_state["current_file_name"] = ingestion_result.metadata.file_name
            st.session_state["current_file_type"] = file_type
            st.session_state["current_profile"] = profile
            st.session_state["current_ingestion_metadata"] = ingestion_metadata
            is_new_ingestion = True

        if is_new_ingestion:
            st.success(
                "Ingest dataset thành công. "
                f"Raw artifact đã được lưu cho '{ingestion_metadata['file_name']}'."
            )
        else:
            st.caption(
                "Dataset này đã được ingest trong session hiện tại; "
                "không tạo ingestion_id mới khi Streamlit rerun."
            )

        st.subheader("1. Ingestion provenance")
        ingestion_col1, ingestion_col2, ingestion_col3, ingestion_col4 = st.columns(4)

        ingestion_col1.metric(
            "Ingestion ID",
            str(ingestion_metadata["ingestion_id"])[:8],
            help=str(ingestion_metadata["ingestion_id"]),
        )
        ingestion_col2.metric(
            "SHA-256",
            str(ingestion_metadata["content_sha256"])[:12],
            help=str(ingestion_metadata["content_sha256"]),
        )
        ingestion_col3.metric(
            "Raw size",
            format_bytes(int(ingestion_metadata["byte_size"])),
        )
        ingestion_col4.metric("Source", str(ingestion_metadata["source_type"]))

        with st.expander("Xem ingestion metadata đầy đủ"):
            st.json(ingestion_metadata)
            raw_path = ingestion_metadata.get("raw_path")
            if raw_path:
                st.code(str(raw_path), language=None)
                st.caption(
                    "Đây là bản raw/bronze gốc trên máy local. "
                    "Thư mục data/raw đã được gitignore."
                )

        basic_info = profile["basic_info"]

        st.subheader("2. Tổng quan dataset")
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
                        file_name=str(ingestion_metadata["file_name"]),
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
                "SQL Server hiện vẫn dùng schema metadata cũ. "
                "Ingestion ID, SHA-256 và raw lineage đang được giữ trong "
                "session/raw storage; bước kế tiếp sẽ nối chúng vào catalog/history."
            )

        st.subheader("3. Preview dữ liệu")
        st.dataframe(df.head(50), use_container_width=True)

        st.subheader("4. Kiểu dữ liệu tự động nhận diện")
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

        st.subheader("5. Missing value theo cột")
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

        st.subheader("6. Duplicate rows")
        duplicate_summary = profile["duplicate_summary"]
        dup_col1, dup_col2 = st.columns(2)
        dup_col1.metric("Số dòng trùng", duplicate_summary["duplicate_rows"])
        dup_col2.metric(
            "Tỷ lệ dòng trùng",
            f"{duplicate_summary['duplicate_rate']}%",
        )

        st.subheader("7. Schema summary")
        st.dataframe(profile["schema_summary"], use_container_width=True)

        st.info(
            "Dataset đã được đưa vào ingestion session. "
            "Bạn có thể mở Data Profile, Quality Issues, Trust Score, "
            "Anomaly Detection hoặc Privacy Risk để tiếp tục."
        )

    except Exception as exc:
        st.error(str(exc))
else:
    st.warning("Vui lòng upload một file CSV, Excel hoặc JSON.")
