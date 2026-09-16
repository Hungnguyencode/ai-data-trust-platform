from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

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

FRESHNESS_URL = (
    f"{API_BASE_URL}/api/freshness"
)


def load_freshness_policy(
    catalog_id: int,
) -> dict[str, Any] | None:
    response = requests.get(
        (
            f"{FRESHNESS_URL}/catalog/"
            f"{catalog_id}/policy"
        ),
        timeout=10,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return dict(
        response.json()
    )


def save_freshness_policy(
    *,
    catalog_id: int,
    max_age_minutes: int,
    is_enabled: bool,
) -> dict[str, Any]:
    response = requests.put(
        (
            f"{FRESHNESS_URL}/catalog/"
            f"{catalog_id}/policy"
        ),
        json={
            "max_age_minutes": (
                max_age_minutes
            ),
            "is_enabled": is_enabled,
        },
        timeout=10,
    )

    response.raise_for_status()

    return dict(
        response.json()
    )


def load_freshness_history(
    catalog_id: int,
    *,
    limit: int = 100,
) -> dict[str, Any]:
    response = requests.get(
        (
            f"{FRESHNESS_URL}/catalog/"
            f"{catalog_id}/history"
        ),
        params={
            "limit": limit,
        },
        timeout=10,
    )

    response.raise_for_status()

    return dict(
        response.json()
    )


def run_freshness_check(
    catalog_id: int,
) -> dict[str, Any]:
    response = requests.post(
        (
            f"{FRESHNESS_URL}/catalog/"
            f"{catalog_id}/check"
        ),
        timeout=15,
    )

    response.raise_for_status()

    return dict(
        response.json()
    )


def format_minutes(
    value: Any,
) -> str:
    if value is None:
        return "N/A"

    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return "N/A"

    if minutes < 60:
        return f"{minutes} min"

    hours = minutes / 60

    if hours < 24:
        return f"{hours:.1f} h"

    days = hours / 24

    return f"{days:.1f} days"


def build_history_frame(
    items: list[dict[str, Any]],
) -> pd.DataFrame:
    if not items:
        return pd.DataFrame()

    records = []

    for item in items:
        records.append(
            {
                "check_id": item[
                    "freshness_check_id"
                ],
                "status": item[
                    "freshness_status"
                ],
                "age": format_minutes(
                    item.get(
                        "age_minutes"
                    )
                ),
                "age_minutes": item.get(
                    "age_minutes"
                ),
                "sla": format_minutes(
                    item[
                        "max_age_minutes"
                    ]
                ),
                "max_age_minutes": item[
                    "max_age_minutes"
                ],
                "version_id": item.get(
                    "version_id"
                ),
                "ingestion_event_id": (
                    item.get(
                        "ingestion_event_id"
                    )
                ),
                "latest_ingested_at": (
                    item.get(
                        "latest_ingested_at"
                    )
                ),
                "checked_at": item[
                    "checked_at"
                ],
            }
        )

    return pd.DataFrame(
        records
    )


st.set_page_config(
    page_title="Dataset Freshness",
    page_icon="⏱️",
    layout="wide",
)

inject_custom_css()

st.markdown(
    """
    <div class="main-title">
        ⏱️ Dataset Freshness Monitoring
    </div>
    <div class="subtitle">
        Quản lý freshness SLA, theo dõi tuổi dữ liệu
        và lịch sử kiểm tra tự động bởi Airflow.
    </div>
    """,
    unsafe_allow_html=True,
)

flash_message = st.session_state.pop(
    "freshness_flash",
    None,
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
    policy = load_freshness_policy(
        catalog_id
    )

    history_payload = (
        load_freshness_history(
            catalog_id,
            limit=100,
        )
    )

except requests.RequestException as exc:
    st.error(
        "Không thể kết nối "
        "Dataset Freshness API."
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


history_items = list(
    history_payload.get(
        "items",
        [],
    )
)

latest_check = (
    history_items[0]
    if history_items
    else None
)


st.markdown(
    '<div class="section-title">'
    "1. Current Freshness Status"
    "</div>",
    unsafe_allow_html=True,
)

status_value = (
    str(
        latest_check[
            "freshness_status"
        ]
    )
    if latest_check
    else "NO CHECK"
)

age_value = (
    format_minutes(
        latest_check.get(
            "age_minutes"
        )
    )
    if latest_check
    else "N/A"
)

sla_value = (
    format_minutes(
        policy[
            "max_age_minutes"
        ]
    )
    if policy
    else "N/A"
)

monitoring_value = (
    (
        "ENABLED"
        if policy["is_enabled"]
        else "DISABLED"
    )
    if policy
    else "NOT CONFIGURED"
)

(
    metric_col1,
    metric_col2,
    metric_col3,
    metric_col4,
) = st.columns(4)

with metric_col1:
    render_metric_card(
        "Freshness Status",
        status_value,
        "Latest persisted check",
        status=(
            "low"
            if status_value == "FRESH"
            else (
                "high"
                if status_value
                == "STALE"
                else "medium"
            )
        ),
    )

with metric_col2:
    render_metric_card(
        "Current Age",
        age_value,
        "Age of latest ingestion",
    )

with metric_col3:
    render_metric_card(
        "Freshness SLA",
        sla_value,
        "Maximum allowed age",
    )

with metric_col4:
    render_metric_card(
        "Monitoring",
        monitoring_value,
        (
            "Airflow scheduled monitor"
            if policy
            else "Policy required"
        ),
        status=(
            "low"
            if (
                policy
                and policy[
                    "is_enabled"
                ]
            )
            else "medium"
        ),
    )


if policy is None:
    render_recommendation_box(
        (
            "Catalog này chưa có "
            "<b>Freshness Policy</b>. "
            "Tạo policy bên dưới để "
            "bắt đầu monitoring."
        ),
        level="warning",
    )

elif not policy["is_enabled"]:
    render_recommendation_box(
        (
            "Freshness monitoring hiện "
            "<b>DISABLED</b> cho catalog này."
        ),
        level="warning",
    )

elif latest_check is None:
    render_recommendation_box(
        (
            "Policy đã bật nhưng chưa có "
            "freshness check nào."
        ),
        level="warning",
    )

elif status_value == "FRESH":
    render_recommendation_box(
        (
            "Dataset hiện đang "
            "<b>FRESH</b>: tuổi dữ liệu "
            "chưa vượt quá Freshness SLA."
        ),
        level="success",
    )

elif status_value == "STALE":
    render_recommendation_box(
        (
            "Dataset đang <b>STALE</b>. "
            "Operational Alert sẽ được "
            "phát cho stale incident này."
        ),
        level="danger",
    )

else:
    render_recommendation_box(
        (
            "Không tìm thấy ingestion "
            "để đánh giá freshness."
        ),
        level="warning",
    )


if latest_check:
    detail_col1, detail_col2 = (
        st.columns(2)
    )

    with detail_col1:
        st.write(
            "**Latest ingestion:**"
        )

        st.code(
            str(
                latest_check.get(
                    "latest_ingested_at",
                    "N/A",
                )
            ),
            language=None,
        )

    with detail_col2:
        st.write(
            "**Last checked:**"
        )

        st.code(
            str(
                latest_check.get(
                    "checked_at",
                    "N/A",
                )
            ),
            language=None,
        )


st.markdown(
    '<div class="section-title">'
    "2. Freshness Policy"
    "</div>",
    unsafe_allow_html=True,
)

st.caption(
    "max_age_minutes là thời gian tối đa "
    "dataset được phép không có ingestion mới."
)

default_max_age = (
    int(
        policy[
            "max_age_minutes"
        ]
    )
    if policy
    else 1440
)

default_enabled = (
    bool(
        policy[
            "is_enabled"
        ]
    )
    if policy
    else True
)

with st.form(
    "freshness_policy_form"
):
    max_age_minutes = int(
        st.number_input(
            "Maximum age (minutes)",
            min_value=1,
            value=default_max_age,
            step=1,
            help=(
                "Ví dụ: 60 = 1 giờ, "
                "1440 = 24 giờ."
            ),
        )
    )

    is_enabled = st.checkbox(
        "Enable scheduled freshness monitoring",
        value=default_enabled,
    )

    save_policy_button = (
        st.form_submit_button(
            "Save Freshness Policy",
            type="primary",
        )
    )


if save_policy_button:
    try:
        saved_policy = (
            save_freshness_policy(
                catalog_id=catalog_id,
                max_age_minutes=(
                    max_age_minutes
                ),
                is_enabled=is_enabled,
            )
        )

    except requests.RequestException as exc:
        st.error(
            "Không thể lưu "
            "Freshness Policy."
        )

        st.code(
            str(exc),
            language=None,
        )

    else:
        st.session_state[
            "freshness_flash"
        ] = (
            "Đã lưu Freshness Policy: "
            f"{saved_policy['max_age_minutes']} "
            "phút, monitoring "
            + (
                "ENABLED."
                if saved_policy[
                    "is_enabled"
                ]
                else "DISABLED."
            )
        )

        st.rerun()


st.markdown(
    '<div class="section-title">'
    "3. Run Freshness Check"
    "</div>",
    unsafe_allow_html=True,
)

st.caption(
    "Airflow kiểm tra tự động theo schedule. "
    "Nút dưới đây dùng khi muốn kiểm tra ngay."
)

check_disabled = (
    policy is None
    or not bool(
        policy.get(
            "is_enabled",
            False,
        )
    )
)

if st.button(
    "▶ Run Check Now",
    type="primary",
    disabled=check_disabled,
):
    try:
        result = run_freshness_check(
            catalog_id
        )

    except requests.RequestException as exc:
        st.error(
            "Không thể chạy "
            "Freshness Check."
        )

        st.code(
            str(exc),
            language=None,
        )

    else:
        st.session_state[
            "freshness_last_manual_check"
        ] = result

        status = result[
            "check"
        ][
            "freshness_status"
        ]

        st.session_state[
            "freshness_flash"
        ] = (
            "Freshness Check hoàn tất: "
            f"{status}."
        )

        st.rerun()


last_manual_check = (
    st.session_state.get(
        "freshness_last_manual_check"
    )
)

if last_manual_check:
    with st.expander(
        "Latest Manual Check Result"
    ):
        st.json(
            last_manual_check
        )


st.markdown(
    '<div class="section-title">'
    "4. Freshness History"
    "</div>",
    unsafe_allow_html=True,
)

history_df = build_history_frame(
    history_items
)

if history_df.empty:
    st.info(
        "Chưa có Freshness Check history."
    )

else:
    status_filter_options = [
        "ALL",
        *sorted(
            history_df[
                "status"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        ),
    ]

    selected_status = st.selectbox(
        "Freshness status",
        status_filter_options,
    )

    filtered_history = (
        history_df.copy()
    )

    if selected_status != "ALL":
        filtered_history = (
            filtered_history[
                filtered_history[
                    "status"
                ]
                == selected_status
            ]
        )

    display_columns = [
        "check_id",
        "status",
        "age",
        "sla",
        "version_id",
        "ingestion_event_id",
        "latest_ingested_at",
        "checked_at",
    ]

    st.dataframe(
        filtered_history[
            display_columns
        ],
        use_container_width=True,
        hide_index=True,
    )

    fresh_count = int(
        (
            history_df["status"]
            == "FRESH"
        ).sum()
    )

    stale_count = int(
        (
            history_df["status"]
            == "STALE"
        ).sum()
    )

    no_data_count = int(
        (
            history_df["status"]
            == "NO_DATA"
        ).sum()
    )

    (
        history_col1,
        history_col2,
        history_col3,
        history_col4,
    ) = st.columns(4)

    with history_col1:
        render_metric_card(
            "Checks",
            str(
                len(history_df)
            ),
            "Loaded history",
        )

    with history_col2:
        render_metric_card(
            "Fresh",
            str(fresh_count),
            "Within SLA",
            status="low",
        )

    with history_col3:
        render_metric_card(
            "Stale",
            str(stale_count),
            "SLA breaches",
            status=(
                "high"
                if stale_count
                else "low"
            ),
        )

    with history_col4:
        render_metric_card(
            "No Data",
            str(no_data_count),
            "No ingestion available",
            status=(
                "medium"
                if no_data_count
                else "low"
            ),
        )


st.markdown(
    '<div class="section-title">'
    "5. Monitoring Behavior"
    "</div>",
    unsafe_allow_html=True,
)

st.info(
    "Airflow DAG `data_freshness_monitor` "
    "được cấu hình kiểm tra các enabled "
    "Freshness Policies mỗi 5 phút. "
    "Nếu cùng một ingestion vẫn STALE, "
    "history vẫn được ghi lại nhưng "
    "Operational Alert không bị spam."
)