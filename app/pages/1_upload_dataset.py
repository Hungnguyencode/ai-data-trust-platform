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
from database.repositories.catalog_repository import (
    get_dataset_version_history,
    get_ingestion_history,
    register_ingestion,
)
from src.ingestion.ingestion_service import (
    calculate_sha256,
    ingest_dataset,
)
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
    "current_catalog_registration",
    "current_catalog_error",
)


def clear_derived_dataset_state() -> None:
    for key in DERIVED_DATASET_STATE_KEYS:
        st.session_state.pop(key, None)


def get_cached_ingestion_metadata() -> dict[str, Any] | None:
    metadata = st.session_state.get(
        "current_ingestion_metadata"
    )

    return (
        metadata
        if isinstance(metadata, dict)
        else None
    )


def is_same_uploaded_dataset(
    *,
    file_name: str,
    content_sha256: str,
) -> bool:
    metadata = get_cached_ingestion_metadata()

    if metadata is None:
        return False

    return (
        metadata.get("file_name") == file_name
        and metadata.get("content_sha256")
        == content_sha256
        and "current_df" in st.session_state
        and "current_profile" in st.session_state
    )


def format_bytes(byte_size: int) -> str:
    size = float(byte_size)

    for unit in (
        "B",
        "KB",
        "MB",
        "GB",
    ):
        if size < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(size):,} {unit}"

            return f"{size:,.2f} {unit}"

        size /= 1024

    return f"{byte_size:,} B"


st.set_page_config(
    page_title="Upload Dataset",
    page_icon="📤",
    layout="wide",
)

st.title("📤 Upload Dataset")

st.caption(
    "Ingest dataset, lưu bản raw gốc, tạo metadata truy vết "
    "và đăng ký version vào SQL Server Dataset Catalog."
)


with st.expander("Database connection"):
    if st.button(
        "Test SQL Server connection",
        key="test_sql_connection",
    ):
        ok, message = test_connection()

        if ok:
            st.success(message)
        else:
            st.error(message)


uploaded_file = st.file_uploader(
    "Chọn file dữ liệu",
    type=[
        "csv",
        "xlsx",
        "xls",
        "json",
    ],
)


if uploaded_file is not None:
    try:
        uploaded_sha256 = calculate_sha256(
            uploaded_file.getvalue()
        )

        same_dataset = is_same_uploaded_dataset(
            file_name=uploaded_file.name,
            content_sha256=uploaded_sha256,
        )

        if same_dataset:
            df = st.session_state[
                "current_df"
            ]

            profile = st.session_state[
                "current_profile"
            ]

            ingestion_metadata = (
                get_cached_ingestion_metadata()
            )

            if ingestion_metadata is None:
                raise RuntimeError(
                    "Không tìm thấy ingestion metadata "
                    "trong session."
                )

            file_type = str(
                ingestion_metadata["file_type"]
            )

            is_new_ingestion = False

        else:
            ingestion_result = ingest_dataset(
                uploaded_file,
                persist_raw=True,
            )

            df = ingestion_result.dataframe

            ingestion_metadata = (
                ingestion_result.metadata.to_dict()
            )

            file_type = (
                ingestion_result.metadata.file_type
            )

            profile = profile_dataset(df)

            clear_derived_dataset_state()

            st.session_state[
                "current_df"
            ] = df

            st.session_state[
                "current_file_name"
            ] = ingestion_result.metadata.file_name

            st.session_state[
                "current_file_type"
            ] = file_type

            st.session_state[
                "current_profile"
            ] = profile

            st.session_state[
                "current_ingestion_metadata"
            ] = ingestion_metadata

            is_new_ingestion = True


        if is_new_ingestion:
            st.success(
                "Ingest dataset thành công. "
                "Raw artifact đã được lưu cho "
                f"'{ingestion_metadata['file_name']}'."
            )
        else:
            st.caption(
                "Dataset này đã được ingest trong session hiện tại; "
                "không tạo ingestion_id mới khi Streamlit rerun."
            )


        catalog_registration = st.session_state.get(
            "current_catalog_registration"
        )

        catalog_error = st.session_state.get(
            "current_catalog_error"
        )

        if catalog_registration is None:
            try:
                catalog_registration = register_ingestion(
                    ingestion_metadata
                )

                st.session_state[
                    "current_catalog_registration"
                ] = catalog_registration

                st.session_state.pop(
                    "current_catalog_error",
                    None,
                )

                catalog_error = None

            except Exception as exc:
                catalog_error = str(exc)

                st.session_state[
                    "current_catalog_error"
                ] = catalog_error


        st.subheader(
            "1. Ingestion provenance"
        )

        (
            ingestion_col1,
            ingestion_col2,
            ingestion_col3,
            ingestion_col4,
        ) = st.columns(4)

        ingestion_col1.metric(
            "Ingestion ID",
            str(
                ingestion_metadata[
                    "ingestion_id"
                ]
            )[:8],
            help=str(
                ingestion_metadata[
                    "ingestion_id"
                ]
            ),
        )

        ingestion_col2.metric(
            "SHA-256",
            str(
                ingestion_metadata[
                    "content_sha256"
                ]
            )[:12],
            help=str(
                ingestion_metadata[
                    "content_sha256"
                ]
            ),
        )

        ingestion_col3.metric(
            "Raw size",
            format_bytes(
                int(
                    ingestion_metadata[
                        "byte_size"
                    ]
                )
            ),
        )

        ingestion_col4.metric(
            "Source",
            str(
                ingestion_metadata[
                    "source_type"
                ]
            ),
        )


        with st.expander(
            "Xem ingestion metadata đầy đủ"
        ):
            st.json(
                ingestion_metadata
            )

            raw_path = (
                ingestion_metadata.get(
                    "raw_path"
                )
            )

            if raw_path:
                st.code(
                    str(raw_path),
                    language=None,
                )

                st.caption(
                    "Đây là bản Raw/Bronze gốc trên máy local. "
                    "Thư mục data/raw đã được gitignore."
                )


        st.subheader(
            "2. Dataset Catalog & Version"
        )

        if catalog_registration:
            (
                catalog_col1,
                catalog_col2,
                catalog_col3,
                catalog_col4,
            ) = st.columns(4)

            catalog_col1.metric(
                "Catalog ID",
                str(
                    catalog_registration[
                        "catalog_id"
                    ]
                ),
            )

            catalog_col2.metric(
                "Dataset version",
                "v"
                + str(
                    catalog_registration[
                        "version_number"
                    ]
                ),
            )

            version_state = (
                "NEW"
                if catalog_registration[
                    "is_new_version"
                ]
                else "EXISTING"
            )

            catalog_col3.metric(
                "Version state",
                version_state,
            )

            catalog_col4.metric(
                "Ingestion event",
                str(
                    catalog_registration[
                        "ingestion_event_id"
                    ]
                ),
            )

            if catalog_registration[
                "is_new_version"
            ]:
                st.success(
                    "SHA-256 mới được phát hiện. "
                    "SQL Server đã tạo một dataset version mới."
                )
            else:
                st.info(
                    "SHA-256 này đã tồn tại trong catalog. "
                    "Hệ thống tái sử dụng version cũ và chỉ ghi "
                    "thêm ingestion history."
                )

            st.caption(
                "Phiên bản catalog hiện tại nhận diện logical dataset "
                "theo tên file đã normalize. "
                "Cùng tên file + SHA khác => version mới."
            )


            catalog_id = int(
                catalog_registration[
                    "catalog_id"
                ]
            )

            with st.expander(
                "Xem lịch sử dataset versions"
            ):
                try:
                    version_history = (
                        get_dataset_version_history(
                            catalog_id
                        )
                    )

                    st.dataframe(
                        version_history,
                        use_container_width=True,
                    )

                except Exception as exc:
                    st.warning(
                        "Không đọc được version history: "
                        f"{exc}"
                    )


            with st.expander(
                "Xem ingestion history"
            ):
                try:
                    ingestion_history = (
                        get_ingestion_history(
                            catalog_id,
                            limit=50,
                        )
                    )

                    st.dataframe(
                        ingestion_history,
                        use_container_width=True,
                    )

                except Exception as exc:
                    st.warning(
                        "Không đọc được ingestion history: "
                        f"{exc}"
                    )

        else:
            st.warning(
                "Raw ingestion đã thành công nhưng chưa sync được "
                "Dataset Catalog vào SQL Server."
            )

            if catalog_error:
                st.code(
                    catalog_error,
                    language=None,
                )

            st.info(
                "Nếu đây là lần đầu chạy bản nâng cấp này, "
                "hãy chạy `python database/init_catalog.py`, "
                "sau đó bấm Retry catalog sync."
            )

            if st.button(
                "Retry catalog sync",
                key="retry_catalog_sync",
            ):
                st.session_state.pop(
                    "current_catalog_error",
                    None,
                )

                st.session_state.pop(
                    "current_catalog_registration",
                    None,
                )

                st.rerun()


        basic_info = profile[
            "basic_info"
        ]

        st.subheader(
            "3. Tổng quan dataset"
        )

        (
            col1,
            col2,
            col3,
            col4,
        ) = st.columns(4)

        col1.metric(
            "Số dòng",
            f"{basic_info['total_rows']:,}",
        )

        col2.metric(
            "Số cột",
            f"{basic_info['total_columns']:,}",
        )

        col3.metric(
            "Missing rate",
            f"{basic_info['missing_rate']}%",
        )

        col4.metric(
            "Duplicate rate",
            f"{basic_info['duplicate_rate']}%",
        )


        st.subheader(
            "4. Preview dữ liệu"
        )

        st.dataframe(
            df.head(50),
            use_container_width=True,
        )


        st.subheader(
            "5. Kiểu dữ liệu tự động nhận diện"
        )

        column_types = profile[
            "column_types"
        ]

        (
            type_col1,
            type_col2,
            type_col3,
            type_col4,
            type_col5,
        ) = st.columns(5)

        type_col1.metric(
            "Numeric",
            len(
                column_types[
                    "numeric_columns"
                ]
            ),
        )

        type_col2.metric(
            "Categorical",
            len(
                column_types[
                    "categorical_columns"
                ]
            ),
        )

        type_col3.metric(
            "Datetime",
            len(
                column_types[
                    "datetime_columns"
                ]
            ),
        )

        type_col4.metric(
            "Boolean",
            len(
                column_types[
                    "boolean_columns"
                ]
            ),
        )

        type_col5.metric(
            "Text",
            len(
                column_types[
                    "text_columns"
                ]
            ),
        )


        with st.expander(
            "Xem danh sách cột theo loại"
        ):
            st.write(
                "**Numeric columns:**",
                column_types[
                    "numeric_columns"
                ],
            )

            st.write(
                "**Categorical columns:**",
                column_types[
                    "categorical_columns"
                ],
            )

            st.write(
                "**Datetime columns:**",
                column_types[
                    "datetime_columns"
                ],
            )

            st.write(
                "**Boolean columns:**",
                column_types[
                    "boolean_columns"
                ],
            )

            st.write(
                "**Text columns:**",
                column_types[
                    "text_columns"
                ],
            )


        st.subheader(
            "6. Missing value theo cột"
        )

        missing_summary = profile[
            "missing_summary"
        ]

        st.dataframe(
            missing_summary,
            use_container_width=True,
        )

        missing_nonzero = (
            missing_summary[
                missing_summary[
                    "missing_count"
                ]
                > 0
            ]
        )

        if not missing_nonzero.empty:
            fig = px.bar(
                missing_nonzero,
                x="column_name",
                y="missing_rate (%)",
                title=(
                    "Tỷ lệ missing value theo cột"
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        else:
            st.success(
                "Không phát hiện missing value trong dataset."
            )


        st.subheader(
            "7. Duplicate rows"
        )

        duplicate_summary = profile[
            "duplicate_summary"
        ]

        dup_col1, dup_col2 = (
            st.columns(2)
        )

        dup_col1.metric(
            "Số dòng trùng",
            duplicate_summary[
                "duplicate_rows"
            ],
        )

        dup_col2.metric(
            "Tỷ lệ dòng trùng",
            f"{duplicate_summary['duplicate_rate']}%",
        )


        st.subheader(
            "8. Schema summary"
        )

        st.dataframe(
            profile[
                "schema_summary"
            ],
            use_container_width=True,
        )


        if catalog_registration:
            st.success(
                "Dataset đã có Raw/Bronze artifact, "
                "ingestion provenance và SQL Server catalog/version."
            )

        else:
            st.info(
                "Dataset đã có Raw/Bronze artifact. "
                "Catalog sẽ được nối sau khi SQL migration chạy thành công."
            )


        st.info(
            "Bạn có thể tiếp tục mở Data Profile, "
            "Quality Issues, Trust Score, Anomaly Detection "
            "hoặc Privacy Risk."
        )

    except Exception as exc:
        st.error(
            str(exc)
        )

else:
    st.warning(
        "Vui lòng upload một file CSV, Excel hoặc JSON."
    )