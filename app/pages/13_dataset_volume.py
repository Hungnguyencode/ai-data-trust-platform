from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from app.services.volume_api import (
    VolumeApiError,
    load_volume_history,
    load_volume_policy,
    run_volume_check,
    save_volume_policy,
)
from src.utils.ui import (
    inject_custom_css,
    render_metric_card,
    render_recommendation_box,
)


def format_percentage(
    value: Any,
) -> str:
    if value is None:
        return "N/A"

    try:
        percentage = float(value)
    except (TypeError, ValueError):
        return "N/A"

    return f"{percentage:+.2f}%"


def format_row_count(
    value: Any,
) -> str:
    if value is None:
        return "N/A"

    try:
        row_count = int(value)
    except (TypeError, ValueError):
        return "N/A"

    return f"{row_count:,}"


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
                    "volume_check_id"
                ],
                "status": item[
                    "volume_status"
                ],
                "baseline_rows": item.get(
                    "baseline_row_count"
                ),
                "current_rows": item[
                    "current_row_count"
                ],
                "change": format_percentage(
                    item.get(
                        "row_change_pct"
                    )
                ),
                "row_change_pct": item.get(
                    "row_change_pct"
                ),
                "drop_threshold": (
                    f"{float(item['drop_threshold_pct']):.2f}%"
                ),
                "spike_threshold": (
                    f"{float(item['spike_threshold_pct']):.2f}%"
                ),
                "version_id": item[
                    "version_id"
                ],
                "ingestion_event_id": item[
                    "ingestion_event_id"
                ],
                "baseline_version_id": item.get(
                    "baseline_version_id"
                ),
                "baseline_ingestion_event_id": (
                    item.get(
                        "baseline_ingestion_event_id"
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
    page_title="Dataset Volume",
    page_icon="📦",
    layout="wide",
)

inject_custom_css()

st.markdown(
    """
    <div class="main-title">
        📦 Dataset Volume Monitoring
    </div>
    <div class="subtitle">
        Theo dõi số lượng dòng giữa các ingestion,
        phát hiện volume drop hoặc spike
        và quản lý monitoring policy.
    </div>
    """,
    unsafe_allow_html=True,
)

flash_message = st.session_state.pop(
    "volume_flash",
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
    policy = load_volume_policy(
        catalog_id
    )

    history_payload = (
        load_volume_history(
            catalog_id,
            limit=100,
        )
    )

except VolumeApiError as exc:
    st.error(
        "Không thể kết nối "
        "Dataset Volume API."
    )

    st.code(
        str(exc),
        language=None,
    )

    st.info(
        "Hãy kiểm tra FastAPI service "
        "và cấu hình API_BASE_URL."
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
    "1. Current Volume Status"
    "</div>",
    unsafe_allow_html=True,
)

status_value = (
    str(
        latest_check[
            "volume_status"
        ]
    )
    if latest_check
    else "NO CHECK"
)

baseline_value = (
    format_row_count(
        latest_check.get(
            "baseline_row_count"
        )
    )
    if latest_check
    else "N/A"
)

current_value = (
    format_row_count(
        latest_check.get(
            "current_row_count"
        )
    )
    if latest_check
    else "N/A"
)

change_value = (
    format_percentage(
        latest_check.get(
            "row_change_pct"
        )
    )
    if latest_check
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
    metric_col5,
) = st.columns(5)

with metric_col1:
    render_metric_card(
        "Volume Status",
        status_value,
        "Latest persisted check",
        status=(
            "low"
            if status_value == "NORMAL"
            else (
                "high"
                if status_value
                in {
                    "DROP",
                    "SPIKE",
                }
                else "medium"
            )
        ),
    )

with metric_col2:
    render_metric_card(
        "Baseline Rows",
        baseline_value,
        "Previous ingestion",
    )

with metric_col3:
    render_metric_card(
        "Current Rows",
        current_value,
        "Latest ingestion",
    )

with metric_col4:
    render_metric_card(
        "Row Change",
        change_value,
        "Current vs baseline",
        status=(
            "high"
            if status_value
            in {
                "DROP",
                "SPIKE",
            }
            else "low"
        ),
    )

with metric_col5:
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
            "<b>Volume Policy</b>. "
            "Tạo policy bên dưới để "
            "bắt đầu monitoring."
        ),
        level="warning",
    )

elif not policy["is_enabled"]:
    render_recommendation_box(
        (
            "Volume monitoring hiện "
            "<b>DISABLED</b> cho catalog này."
        ),
        level="warning",
    )

elif latest_check is None:
    render_recommendation_box(
        (
            "Policy đã bật nhưng chưa có "
            "Volume Check nào."
        ),
        level="warning",
    )

elif status_value == "NORMAL":
    render_recommendation_box(
        (
            "Dataset volume hiện "
            "<b>NORMAL</b>. "
            "Biến động row count vẫn nằm "
            "trong threshold đã cấu hình."
        ),
        level="success",
    )

elif status_value == "DROP":
    render_recommendation_box(
        (
            "Dataset đang có "
            "<b>VOLUME DROP</b>. "
            "Số lượng row giảm vượt "
            "ngưỡng policy."
        ),
        level="danger",
    )

elif status_value == "SPIKE":
    render_recommendation_box(
        (
            "Dataset đang có "
            "<b>VOLUME SPIKE</b>. "
            "Số lượng row tăng vượt "
            "ngưỡng policy."
        ),
        level="danger",
    )

else:
    render_recommendation_box(
        (
            "Chưa có baseline ingestion "
            "để so sánh volume."
        ),
        level="warning",
    )

if latest_check:
    detail_col1, detail_col2 = (
        st.columns(2)
    )

    with detail_col1:
        st.write(
            "**Current ingestion event:**"
        )

        st.code(
            str(
                latest_check.get(
                    "ingestion_event_id",
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
    "2. Volume Policy"
    "</div>",
    unsafe_allow_html=True,
)

st.caption(
    "Drop threshold là phần trăm giảm row count "
    "tối đa cho phép. Spike threshold là phần trăm "
    "tăng row count tối đa cho phép."
)

default_drop_threshold = (
    float(
        policy[
            "drop_threshold_pct"
        ]
    )
    if policy
    else 20.0
)

default_spike_threshold = (
    float(
        policy[
            "spike_threshold_pct"
        ]
    )
    if policy
    else 20.0
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
    "volume_policy_form"
):
    drop_threshold_pct = float(
        st.number_input(
            "Drop threshold (%)",
            min_value=0.1,
            max_value=100.0,
            value=default_drop_threshold,
            step=0.5,
        )
    )

    spike_threshold_pct = float(
        st.number_input(
            "Spike threshold (%)",
            min_value=0.1,
            value=default_spike_threshold,
            step=0.5,
        )
    )

    is_enabled = st.checkbox(
        "Enable scheduled volume monitoring",
        value=default_enabled,
    )

    save_policy_button = (
        st.form_submit_button(
            "Save Volume Policy",
            type="primary",
        )
    )

if save_policy_button:
    try:
        saved_policy = (
            save_volume_policy(
                catalog_id=catalog_id,
                drop_threshold_pct=(
                    drop_threshold_pct
                ),
                spike_threshold_pct=(
                    spike_threshold_pct
                ),
                is_enabled=is_enabled,
            )
        )

    except VolumeApiError as exc:
        st.error(
            "Không thể lưu "
            "Volume Policy."
        )

        st.code(
            str(exc),
            language=None,
        )

    else:
        st.session_state[
            "volume_flash"
        ] = (
            "Đã lưu Volume Policy: "
            f"drop={saved_policy['drop_threshold_pct']}%, "
            f"spike={saved_policy['spike_threshold_pct']}%, "
            "monitoring "
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
    "3. Run Volume Check"
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
        result = run_volume_check(
            catalog_id
        )

    except VolumeApiError as exc:
        st.error(
            "Không thể chạy "
            "Volume Check."
        )

        st.code(
            str(exc),
            language=None,
        )

    else:
        st.session_state[
            "volume_last_manual_check"
        ] = result

        status = result[
            "check"
        ][
            "volume_status"
        ]

        st.session_state[
            "volume_flash"
        ] = (
            "Volume Check hoàn tất: "
            f"{status}."
        )

        st.rerun()

last_manual_check = (
    st.session_state.get(
        "volume_last_manual_check"
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
    "4. Volume History"
    "</div>",
    unsafe_allow_html=True,
)

history_df = build_history_frame(
    history_items
)

if history_df.empty:
    st.info(
        "Chưa có Volume Check history."
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
        "Volume status",
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
        "baseline_rows",
        "current_rows",
        "change",
        "drop_threshold",
        "spike_threshold",
        "version_id",
        "ingestion_event_id",
        "checked_at",
    ]

    st.dataframe(
        filtered_history[
            display_columns
        ],
        use_container_width=True,
        hide_index=True,
    )

    normal_count = int(
        (
            history_df["status"]
            == "NORMAL"
        ).sum()
    )

    drop_count = int(
        (
            history_df["status"]
            == "DROP"
        ).sum()
    )

    spike_count = int(
        (
            history_df["status"]
            == "SPIKE"
        ).sum()
    )

    no_baseline_count = int(
        (
            history_df["status"]
            == "NO_BASELINE"
        ).sum()
    )

    (
        history_col1,
        history_col2,
        history_col3,
        history_col4,
        history_col5,
    ) = st.columns(5)

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
            "Normal",
            str(normal_count),
            "Within thresholds",
            status="low",
        )

    with history_col3:
        render_metric_card(
            "Drop",
            str(drop_count),
            "Volume drops",
            status=(
                "high"
                if drop_count
                else "low"
            ),
        )

    with history_col4:
        render_metric_card(
            "Spike",
            str(spike_count),
            "Volume spikes",
            status=(
                "high"
                if spike_count
                else "low"
            ),
        )

    with history_col5:
        render_metric_card(
            "No Baseline",
            str(no_baseline_count),
            "First ingestion",
            status="medium",
        )