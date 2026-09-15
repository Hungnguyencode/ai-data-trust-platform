from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st

PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.utils.ui import (
    inject_custom_css,
    render_metric_card,
    render_recommendation_box,
)

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

DATA_CONTRACTS_URL = (
    f"{API_BASE_URL}/api/data-contracts"
)


def load_contract_history(
    catalog_id: int,
) -> dict[str, Any]:
    response = requests.get(
        (
            f"{DATA_CONTRACTS_URL}/"
            f"catalog/{catalog_id}"
        ),
        timeout=10,
    )

    response.raise_for_status()

    return dict(
        response.json()
    )


def load_active_contract(
    catalog_id: int,
) -> dict[str, Any] | None:
    response = requests.get(
        (
            f"{DATA_CONTRACTS_URL}/"
            f"catalog/{catalog_id}/active"
        ),
        timeout=10,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return dict(
        response.json()
    )


def activate_contract(
    contract_id: int,
) -> dict[str, Any]:
    response = requests.post(
        (
            f"{DATA_CONTRACTS_URL}/"
            f"{contract_id}/activate"
        ),
        timeout=10,
    )

    response.raise_for_status()

    return dict(
        response.json()
    )


def create_contract(
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = requests.post(
        DATA_CONTRACTS_URL,
        json=payload,
        timeout=10,
    )

    response.raise_for_status()

    return dict(
        response.json()
    )


def build_history_frame(
    contracts: list[dict[str, Any]],
) -> pd.DataFrame:
    records = []

    for contract in contracts:
        records.append(
            {
                "contract_id": contract[
                    "contract_id"
                ],
                "version": (
                    "v"
                    + str(
                        contract[
                            "contract_version"
                        ]
                    )
                ),
                "name": contract[
                    "contract_name"
                ],
                "enforcement": contract[
                    "enforcement_mode"
                ],
                "active": contract[
                    "is_active"
                ],
                "columns": len(
                    contract.get(
                        "columns",
                        [],
                    )
                ),
                "created_at": contract.get(
                    "created_at"
                ),
                "updated_at": contract.get(
                    "updated_at"
                ),
            }
        )

    return pd.DataFrame(
        records
    )


st.set_page_config(
    page_title="Data Contracts",
    page_icon="📜",
    layout="wide",
)

inject_custom_css()

st.markdown(
    """
    <div class="main-title">
        📜 Data Contract Management
    </div>
    <div class="subtitle">
        Xem contract history, active contract
        và quản lý version được dùng bởi
        Data Contract Gate.
    </div>
    """,
    unsafe_allow_html=True,
)

flash_message = (
    st.session_state.pop(
        "data_contract_flash",
        None,
    )
)

if flash_message:
    st.success(
        flash_message
    )

header_col1, header_col2 = st.columns(
    [4, 1]
)

with header_col1:
    catalog_id = int(
        st.number_input(
            "Catalog ID",
            min_value=1,
            value=1,
            step=1,
        )
    )

with header_col2:
    st.write("")

    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):
        st.rerun()

try:
    history_payload = (
        load_contract_history(
            catalog_id
        )
    )

    active_contract = (
        load_active_contract(
            catalog_id
        )
    )

except requests.RequestException as exc:
    st.error(
        "Không thể kết nối "
        "Data Contract Management API."
    )

    st.code(
        str(exc),
        language=None,
    )

    st.info(
        "Hãy kiểm tra FastAPI đang chạy "
        f"tại {API_BASE_URL}."
    )

    st.stop()

contracts = list(
    history_payload.get(
        "items",
        [],
    )
)

st.markdown(
    '<div class="section-title">'
    "1. Active Contract"
    "</div>",
    unsafe_allow_html=True,
)

if active_contract is None:
    render_recommendation_box(
        (
            "Dataset catalog này chưa có "
            "active Data Contract."
        ),
        level="warning",
    )

else:
    (
        active_col1,
        active_col2,
        active_col3,
        active_col4,
    ) = st.columns(4)

    with active_col1:
        render_metric_card(
            "Version",
            (
                "v"
                + str(
                    active_contract[
                        "contract_version"
                    ]
                )
            ),
            "Active contract version",
            status="low",
        )

    with active_col2:
        render_metric_card(
            "Contract",
            str(
                active_contract[
                    "contract_name"
                ]
            ),
            (
                "ID "
                + str(
                    active_contract[
                        "contract_id"
                    ]
                )
            ),
        )

    with active_col3:
        render_metric_card(
            "Enforcement",
            str(
                active_contract[
                    "enforcement_mode"
                ]
            ),
            "Current gate behavior",
        )

    with active_col4:
        render_metric_card(
            "Columns",
            str(
                len(
                    active_contract.get(
                        "columns",
                        [],
                    )
                )
            ),
            "Schema rules",
        )

    render_recommendation_box(
        (
            "Workflow sẽ enforce "
            "<b>Data Contract v"
            + str(
                active_contract[
                    "contract_version"
                ]
            )
            + "</b> ở chế độ <b>"
            + str(
                active_contract[
                    "enforcement_mode"
                ]
            )
            + "</b>."
        ),
        level="success",
    )

st.markdown(
    '<div class="section-title">'
    "2. Contract History"
    "</div>",
    unsafe_allow_html=True,
)

if not contracts:
    st.info(
        "Catalog này chưa có "
        "Data Contract nào."
    )

history_df = build_history_frame(
    contracts
)

st.dataframe(
    history_df,
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Contract version mới nhất được "
    "hiển thị trước. Chỉ một version "
    "được active tại một thời điểm."
)

st.markdown(
    '<div class="section-title">'
    "3. Activate Contract Version"
    "</div>",
    unsafe_allow_html=True,
)

inactive_contracts = [
    contract
    for contract in contracts
    if not bool(
        contract["is_active"]
    )
]

if not inactive_contracts:
    st.info(
        "Không có inactive contract "
        "để activate."
    )

else:
    contract_options = {
        (
            "v"
            + str(
                contract[
                    "contract_version"
                ]
            )
            + " | "
            + str(
                contract[
                    "contract_name"
                ]
            )
            + " | "
            + str(
                contract[
                    "enforcement_mode"
                ]
            )
        ): int(
            contract[
                "contract_id"
            ]
        )
        for contract in inactive_contracts
    }

    selected_label = st.selectbox(
        "Chọn contract version",
        options=list(
            contract_options.keys()
        ),
        index=None,
        placeholder=(
            "Chọn một inactive contract..."
        ),
    )

    selected_contract_id = (
        contract_options.get(
            selected_label
        )
    )

    st.warning(
        "Activate version này sẽ "
        "deactivate active contract "
        "hiện tại của cùng catalog."
    )

    if st.button(
        "Activate selected contract",
        type="primary",
        disabled=(
            selected_contract_id
            is None
        ),
    ):
        try:
            activated = (
                activate_contract(
                    selected_contract_id
                )
            )

        except requests.RequestException as exc:
            st.error(
                "Không thể activate "
                "Data Contract."
            )

            st.code(
                str(exc),
                language=None,
            )

        else:
            st.success(
                "Đã activate Data Contract "
                "v"
                + str(
                    activated[
                        "contract_version"
                    ]
                )
                + "."
            )

            st.rerun()

st.markdown(
    '<div class="section-title">'
    "4. Active Contract Schema"
    "</div>",
    unsafe_allow_html=True,
)

if active_contract is None:
    st.info(
        "Không có active contract "
        "để hiển thị schema."
    )

else:
    columns = active_contract.get(
        "columns",
        [],
    )

    if not columns:
        st.info(
            "Active contract không có "
            "column rules."
        )

    else:
        schema_df = pd.DataFrame(
            columns
        )

        display_columns = [
            "column_name",
            "expected_type",
            "is_required",
            "is_nullable",
        ]

        st.dataframe(
            schema_df[
                display_columns
            ],
            use_container_width=True,
            hide_index=True,
        )

st.markdown(
    '<div class="section-title">'
    "5. Create New Contract Version"
    "</div>",
    unsafe_allow_html=True,
)

st.caption(
    "Tạo version mới cho catalog hiện tại. "
    "Schema của active contract được dùng "
    "làm template ban đầu."
)

expected_types = [
    "NUMERIC",
    "CATEGORICAL",
    "DATETIME",
    "BOOLEAN",
    "TEXT",
]

template_rows = []

if active_contract is not None:
    for column in active_contract.get(
        "columns",
        [],
    ):
        template_rows.append(
            {
                "column_name": column[
                    "column_name"
                ],
                "expected_type": column[
                    "expected_type"
                ],
                "is_required": column[
                    "is_required"
                ],
                "is_nullable": column[
                    "is_nullable"
                ],
            }
        )

if not template_rows:
    template_rows = [
        {
            "column_name": "",
            "expected_type": "TEXT",
            "is_required": True,
            "is_nullable": True,
        }
    ]

template_df = pd.DataFrame(
    template_rows
)

active_version = (
    active_contract[
        "contract_version"
    ]
    if active_contract is not None
    else 0
)

with st.form(
    "create_data_contract_form"
):
    contract_name = st.text_input(
        "Contract name",
        value=(
            f"catalog_{catalog_id}_contract"
        ),
    )

    (
        create_col1,
        create_col2,
    ) = st.columns(2)

    with create_col1:
        enforcement_mode = (
            st.selectbox(
                "Enforcement mode",
                [
                    "BLOCK",
                    "WARN",
                ],
            )
        )

    with create_col2:
        activate_new_contract = (
            st.checkbox(
                "Activate immediately",
                value=False,
            )
        )

    edited_columns = st.data_editor(
        template_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key=(
            "contract_columns_"
            f"{catalog_id}_"
            f"{active_version}"
        ),
        column_config={
            "column_name": (
                st.column_config.TextColumn(
                    "Column name"
                )
            ),
            "expected_type": (
                st.column_config.SelectboxColumn(
                    "Expected type",
                    options=expected_types,
                )
            ),
            "is_required": (
                st.column_config.CheckboxColumn(
                    "Required"
                )
            ),
            "is_nullable": (
                st.column_config.CheckboxColumn(
                    "Nullable"
                )
            ),
        },
    )

    create_submitted = (
        st.form_submit_button(
            "Create contract version",
            type="primary",
        )
    )

if create_submitted:
    clean_contract_name = (
        contract_name.strip()
    )

    contract_columns = []
    invalid_type = False

    for row in edited_columns.to_dict(
        orient="records"
    ):
        raw_name = row.get(
            "column_name"
        )

        if (
            raw_name is None
            or pd.isna(raw_name)
        ):
            continue

        column_name = str(
            raw_name
        ).strip()

        if not column_name:
            continue

        raw_type = row.get(
            "expected_type"
        )

        if (
            raw_type is None
            or pd.isna(raw_type)
            or str(raw_type)
            not in expected_types
        ):
            invalid_type = True
            break

        required_value = row.get(
            "is_required"
        )

        nullable_value = row.get(
            "is_nullable"
        )

        is_required = (
            True
            if (
                required_value is None
                or pd.isna(
                    required_value
                )
            )
            else bool(
                required_value
            )
        )

        is_nullable = (
            True
            if (
                nullable_value is None
                or pd.isna(
                    nullable_value
                )
            )
            else bool(
                nullable_value
            )
        )

        contract_columns.append(
            {
                "column_name": column_name,
                "expected_type": str(
                    raw_type
                ),
                "is_required": is_required,
                "is_nullable": is_nullable,
            }
        )

    column_names = [
        column["column_name"]
        for column in contract_columns
    ]

    if not clean_contract_name:
        st.error(
            "Contract name không được trống."
        )

    elif not contract_columns:
        st.error(
            "Contract phải có ít nhất "
            "một column rule."
        )

    elif invalid_type:
        st.error(
            "Mỗi column phải có "
            "expected type hợp lệ."
        )

    elif (
        len(column_names)
        != len(set(column_names))
    ):
        st.error(
            "Không được khai báo "
            "trùng column name."
        )

    else:
        payload = {
            "catalog_id": catalog_id,
            "contract_name": (
                clean_contract_name
            ),
            "enforcement_mode": (
                enforcement_mode
            ),
            "activate": (
                activate_new_contract
            ),
            "columns": contract_columns,
        }

        try:
            created_contract = (
                create_contract(
                    payload
                )
            )

        except requests.RequestException as exc:
            st.error(
                "Không thể tạo "
                "Data Contract."
            )

            st.code(
                str(exc),
                language=None,
            )

        else:
            st.session_state[
                "data_contract_flash"
            ] = (
                "Đã tạo Data Contract v"
                + str(
                    created_contract[
                        "contract_version"
                    ]
                )
                + " thành công."
            )

            st.rerun()

with st.expander(
    "Raw API response"
):
    st.json(
        history_payload
    )