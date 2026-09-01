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
from database.repositories.validation_repository import (
    get_validation_history,
    register_validation,
)
from database.repositories.version_repository import (
    apply_validation_lifecycle,
    get_catalog_lifecycle,
    get_lifecycle_history,
    promote_version,
)
from src.ingestion.ingestion_service import (
    calculate_sha256,
    ingest_dataset,
)
from src.profiling.profiler import profile_dataset
from src.validation.validation_gate import (
    validate_and_route_dataset,
)

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
    "current_validation_result",
    "current_validation_registration",
    "current_validation_error",
    "current_lifecycle_result",
    "current_lifecycle_error",
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
                "Catalog registration",
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

        validation_result = st.session_state.get(
            "current_validation_result"
        )

        validation_registration = st.session_state.get(
            "current_validation_registration"
        )

        validation_error = st.session_state.get(
            "current_validation_error"
        )

        if (
            validation_result is None
            and validation_error is None
        ):
            try:
                gate_result = (
                    validate_and_route_dataset(
                        df=df,
                        ingestion_metadata=(
                            ingestion_metadata
                        ),
                    )
                )

                validation_result = (
                    gate_result.to_dict()
                )

                st.session_state[
                    "current_validation_result"
                ] = validation_result

            except Exception as exc:
                validation_error = str(
                    exc
                )

                st.session_state[
                    "current_validation_error"
                ] = validation_error

        if (
            validation_result
            and catalog_registration
            and validation_registration is None
        ):
            try:
                validation_registration = (
                    register_validation(
                        validation_result,
                        catalog_registration,
                    )
                )

                st.session_state[
                    "current_validation_registration"
                ] = validation_registration

                st.session_state.pop(
                    "current_validation_error",
                    None,
                )

                validation_error = None

            except Exception as exc:
                validation_error = str(
                    exc
                )

                st.session_state[
                    "current_validation_error"
                ] = validation_error

        lifecycle_result = st.session_state.get(
            "current_lifecycle_result"
        )

        lifecycle_error = st.session_state.get(
            "current_lifecycle_error"
        )

        if (
            validation_result
            and validation_registration
            and catalog_registration
            and lifecycle_result is None
            and lifecycle_error is None
        ):
            try:
                lifecycle_result = (
                    apply_validation_lifecycle(
                        catalog_registration,
                        validation_result,
                    )
                )

                st.session_state[
                    "current_lifecycle_result"
                ] = lifecycle_result

                st.session_state.pop(
                    "current_lifecycle_error",
                    None,
                )

                lifecycle_error = None

            except Exception as exc:
                lifecycle_error = str(exc)

                st.session_state[
                    "current_lifecycle_error"
                ] = lifecycle_error

        st.subheader(
            "3. Validation Gate"
        )

        if validation_result:
            validation_status = str(
                validation_result[
                    "status"
                ]
            )

            (
                validation_col1,
                validation_col2,
                validation_col3,
                validation_col4,
                validation_col5,
            ) = st.columns(5)

            validation_col1.metric(
                "Validation",
                validation_status,
            )

            validation_col2.metric(
                "High",
                validation_result[
                    "high_issues"
                ],
            )

            validation_col3.metric(
                "Medium",
                validation_result[
                    "medium_issues"
                ],
            )

            validation_col4.metric(
                "Low",
                validation_result[
                    "low_issues"
                ],
            )

            validation_col5.metric(
                "Blocking",
                validation_result[
                    "blocking_issue_count"
                ],
            )

            if (
                validation_status
                == "ACCEPTED"
            ):
                st.success(
                    "ACCEPTED — dataset đã qua Validation Gate "
                    "và được route sang data/processed (Silver)."
                )

            else:
                st.error(
                    "REJECTED — dataset có High severity issue "
                    "và đã được route sang data/quarantine."
                )

            st.caption(
                "Policy v1: High severity sẽ block dataset. "
                "Medium và Low vẫn được ghi nhận nhưng không block."
            )

            with st.expander(
                "Xem validation artifact"
            ):
                st.write(
                    "**Policy version:**",
                    validation_result[
                        "policy_version"
                    ],
                )

                st.write(
                    "**Validated at:**",
                    validation_result[
                        "validated_at"
                    ],
                )

                st.write(
                    "**Dataset artifact:**"
                )

                st.code(
                    validation_result[
                        "artifact_path"
                    ],
                    language=None,
                )

                st.write(
                    "**Validation metadata:**"
                )

                st.code(
                    validation_result[
                        "validation_metadata_path"
                    ],
                    language=None,
                )

            blocking_issues = (
                validation_result.get(
                    "blocking_issues",
                    [],
                )
            )

            if blocking_issues:
                st.warning(
                    "Các lỗi khiến dataset bị reject:"
                )

                st.dataframe(
                    blocking_issues,
                    use_container_width=True,
                )

            if validation_registration:
                validation_id = (
                    validation_registration.get(
                        "validation_id"
                    )
                )

                if validation_id is not None:
                    st.caption(
                        "Validation đã được lưu vào SQL Server. "
                        f"validation_id={validation_id}"
                    )

            if catalog_registration:
                with st.expander(
                    "Xem validation history"
                ):
                    try:
                        validation_history = (
                            get_validation_history(
                                int(
                                    catalog_registration[
                                        "catalog_id"
                                    ]
                                ),
                                limit=50,
                            )
                        )

                        st.dataframe(
                            validation_history,
                            use_container_width=True,
                        )

                    except Exception as exc:
                        st.warning(
                            "Không đọc được validation history: "
                            f"{exc}"
                        )

        else:
            st.warning(
                "Validation Gate chưa chạy thành công."
            )

            if validation_error:
                st.code(
                    validation_error,
                    language=None,
                )

            st.info(
                "Nếu lỗi báo thiếu validation_history, "
                "hãy chạy lại migration database."
            )

            if st.button(
                "Retry validation",
                key="retry_validation",
            ):
                st.session_state.pop(
                    "current_validation_result",
                    None,
                )

                st.session_state.pop(
                    "current_validation_registration",
                    None,
                )

                st.session_state.pop(
                    "current_validation_error",
                    None,
                )

                st.rerun()


        st.subheader(
            "4. Dataset Lifecycle"
        )

        lifecycle_state = None
        lifecycle_table = None

        if catalog_registration:
            catalog_id = int(
                catalog_registration[
                    "catalog_id"
                ]
            )

            version_id = int(
                catalog_registration[
                    "version_id"
                ]
            )

            version_number = int(
                catalog_registration[
                    "version_number"
                ]
            )

            try:
                lifecycle_table = (
                    get_catalog_lifecycle(
                        catalog_id
                    )
                )

                current_version_rows = (
                    lifecycle_table[
                        lifecycle_table[
                            "version_id"
                        ]
                        == version_id
                    ]
                )

                if not current_version_rows.empty:
                    lifecycle_state = str(
                        current_version_rows.iloc[
                            0
                        ][
                            "lifecycle_state"
                        ]
                    ).upper()

            except Exception as exc:
                lifecycle_error = str(exc)

        if lifecycle_state:
            (
                lifecycle_col1,
                lifecycle_col2,
                lifecycle_col3,
                lifecycle_col4,
            ) = st.columns(4)

            lifecycle_col1.metric(
                "Dataset version",
                f"v{version_number}",
            )

            lifecycle_col2.metric(
                "Lifecycle state",
                lifecycle_state,
            )

            lifecycle_col3.metric(
                "Promotion eligible",
                (
                    "YES"
                    if lifecycle_state
                    == "VALIDATED"
                    else "NO"
                ),
            )

            lifecycle_col4.metric(
                "Catalog ID",
                str(catalog_id),
            )

            if lifecycle_state == "NEW":
                st.info(
                    "Version mới được ingest nhưng "
                    "chưa có kết luận Validation Gate."
                )

            elif lifecycle_state == "VALIDATED":
                st.success(
                    "Version đã vượt qua Validation Gate "
                    "và đủ điều kiện promote thành ACTIVE."
                )

                if st.button(
                    f"Promote v{version_number} to ACTIVE",
                    key=(
                        "promote_version_"
                        f"{version_id}"
                    ),
                    type="primary",
                ):
                    try:
                        promotion_result = (
                            promote_version(
                                catalog_id=catalog_id,
                                version_id=version_id,
                            )
                        )

                        st.session_state[
                            "current_lifecycle_result"
                        ] = promotion_result

                        st.session_state.pop(
                            "current_lifecycle_error",
                            None,
                        )

                        st.rerun()

                    except Exception as exc:
                        st.error(
                            "Không thể promote version: "
                            f"{exc}"
                        )

            elif lifecycle_state == "QUARANTINED":
                st.error(
                    "Version này đang QUARANTINED "
                    "do không vượt qua Validation Gate. "
                    "Không được phép promote thành ACTIVE."
                )

            elif lifecycle_state == "ACTIVE":
                st.success(
                    "Đây là version ACTIVE hiện tại "
                    "của dataset."
                )

            elif lifecycle_state == "SUPERSEDED":
                st.info(
                    "Version này từng ACTIVE nhưng "
                    "đã được thay thế bởi version mới hơn."
                )

            if lifecycle_table is not None:
                with st.expander(
                    "Xem lifecycle của tất cả versions"
                ):
                    st.dataframe(
                        lifecycle_table,
                        use_container_width=True,
                    )

            with st.expander(
                "Xem lifecycle history của version hiện tại"
            ):
                try:
                    lifecycle_history = (
                        get_lifecycle_history(
                            version_id
                        )
                    )

                    if lifecycle_history.empty:
                        st.info(
                            "Version này chưa có lifecycle "
                            "transition nào được ghi nhận."
                        )

                    else:
                        st.dataframe(
                            lifecycle_history,
                            use_container_width=True,
                        )

                except Exception as exc:
                    st.warning(
                        "Không đọc được lifecycle history: "
                        f"{exc}"
                    )

        else:
            st.warning(
                "Chưa đọc được lifecycle state "
                "của dataset version."
            )

            if lifecycle_error:
                st.code(
                    lifecycle_error,
                    language=None,
                )

        st.subheader(
            "5. Tổng quan dataset"
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
            "6. Preview dữ liệu"
        )

        st.dataframe(
            df.head(50),
            use_container_width=True,
        )


        st.subheader(
            "7. Kiểu dữ liệu tự động nhận diện"
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
            "8. Missing value theo cột"
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
            "9. Duplicate rows"
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
            "10. Schema summary"
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