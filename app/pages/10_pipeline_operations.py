from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
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

PIPELINE_RUNS_URL = (
    f"{API_BASE_URL}/api/pipeline-runs"
)


def load_pipeline_runs(
    limit: int = 100,
) -> list[dict[str, Any]]:
    response = requests.get(
        PIPELINE_RUNS_URL,
        params={
            "limit": limit,
        },
        timeout=10,
    )

    response.raise_for_status()

    payload = response.json()

    return list(
        payload.get(
            "items",
            [],
        )
    )


def load_pipeline_run(
    pipeline_run_id: int,
) -> dict[str, Any]:
    response = requests.get(
        (
            f"{PIPELINE_RUNS_URL}/"
            f"{pipeline_run_id}"
        ),
        timeout=10,
    )

    response.raise_for_status()

    return dict(
        response.json()
    )


def format_duration(
    duration_ms: Any,
) -> str:
    if duration_ms is None:
        return "N/A"

    try:
        milliseconds = float(
            duration_ms
        )
    except (
        TypeError,
        ValueError,
    ):
        return "N/A"

    seconds = milliseconds / 1000

    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(
        seconds // 60
    )

    remaining_seconds = (
        seconds % 60
    )

    return (
        f"{minutes}m "
        f"{remaining_seconds:.1f}s"
    )


def display_value(
    value: Any,
) -> Any:
    return (
        value
        if value is not None
        else "N/A"
    )


st.set_page_config(
    page_title="Pipeline Operations",
    page_icon="🛠️",
    layout="wide",
)

inject_custom_css()

st.markdown(
    """
    <div class="main-title">
        🛠️ Pipeline Operations
    </div>
    <div class="subtitle">
        Theo dõi Airflow pipeline runs,
        retries, failures và governance
        metadata.
    </div>
    """,
    unsafe_allow_html=True,
)

header_col1, header_col2 = (
    st.columns(
        [4, 1]
    )
)

with header_col2:
    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):
        st.rerun()

try:
    pipeline_runs = (
        load_pipeline_runs(
            limit=100
        )
    )

except requests.RequestException as exc:
    st.error(
        "Không thể kết nối Pipeline "
        "Operations API."
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

if not pipeline_runs:
    st.info(
        "Chưa có pipeline run nào "
        "được ghi nhận."
    )

    st.stop()

runs_df = pd.DataFrame(
    pipeline_runs
)

total_runs = len(
    runs_df
)

success_runs = int(
    (
        runs_df["run_status"]
        == "SUCCESS"
    ).sum()
)

failed_runs = int(
    (
        runs_df["run_status"]
        == "FAILED"
    ).sum()
)

running_runs = int(
    (
        runs_df["run_status"]
        == "RUNNING"
    ).sum()
)

completed_runs = (
    success_runs
    + failed_runs
)

success_rate = (
    (
        success_runs
        / completed_runs
        * 100
    )
    if completed_runs
    else 0.0
)

duration_series = pd.to_numeric(
    runs_df["duration_ms"],
    errors="coerce",
)

average_duration_ms = (
    duration_series
    .dropna()
    .mean()
)

st.markdown(
    '<div class="section-title">'
    "1. Operations Overview"
    "</div>",
    unsafe_allow_html=True,
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
        "Total Runs",
        str(total_runs),
        "Persisted Airflow runs",
    )

with metric_col2:
    render_metric_card(
        "Success",
        str(success_runs),
        "Completed successfully",
        status="low",
    )

with metric_col3:
    render_metric_card(
        "Failed",
        str(failed_runs),
        "Runs requiring attention",
        status=(
            "high"
            if failed_runs
            else "low"
        ),
    )

with metric_col4:
    render_metric_card(
        "Success Rate",
        f"{success_rate:.1f}%",
        "Successful / completed runs",
        status=(
            "low"
            if success_rate >= 90
            else "medium"
        ),
    )

with metric_col5:
    render_metric_card(
        "Avg Duration",
        format_duration(
            average_duration_ms
        ),
        "Finished runs",
    )

if running_runs:
    render_recommendation_box(
        (
            f"Có <b>{running_runs}</b> "
            "pipeline run đang RUNNING."
        ),
        level="warning",
    )

elif failed_runs:
    render_recommendation_box(
        (
            f"Có <b>{failed_runs}</b> "
            "failed run trong lịch sử. "
            "Xem Error Diagnostics bên dưới."
        ),
        level="danger",
    )

else:
    render_recommendation_box(
        "Không có failed pipeline run.",
        level="success",
    )

st.markdown(
    '<div class="section-title">'
    "2. Run Status Distribution"
    "</div>",
    unsafe_allow_html=True,
)

chart_col1, chart_col2 = (
    st.columns(2)
)

status_counts = (
    runs_df[
        "run_status"
    ]
    .value_counts()
    .rename_axis(
        "run_status"
    )
    .reset_index(
        name="count"
    )
)

with chart_col1:
    status_fig = px.pie(
        status_counts,
        names="run_status",
        values="count",
        hole=0.45,
        title=(
            "Pipeline runs by status"
        ),
        color="run_status",
        color_discrete_map={
            "SUCCESS": "#22c55e",
            "FAILED": "#ef4444",
            "RUNNING": "#f59e0b",
        },
    )

    st.plotly_chart(
        status_fig,
        use_container_width=True,
    )

with chart_col2:
    attempts_df = (
        runs_df[
            [
                "pipeline_run_id",
                "attempt_count",
            ]
        ]
        .copy()
    )

    attempts_df[
        "pipeline_run_id"
    ] = (
        attempts_df[
            "pipeline_run_id"
        ].astype(str)
    )

    attempts_fig = px.bar(
        attempts_df,
        x="pipeline_run_id",
        y="attempt_count",
        title=(
            "Workflow attempts per run"
        ),
        labels={
            "pipeline_run_id": (
                "Pipeline Run ID"
            ),
            "attempt_count": (
                "Attempts"
            ),
        },
    )

    st.plotly_chart(
        attempts_fig,
        use_container_width=True,
    )

st.markdown(
    '<div class="section-title">'
    "3. Pipeline Run History"
    "</div>",
    unsafe_allow_html=True,
)

filter_col1, filter_col2 = (
    st.columns(
        [1, 2]
    )
)

status_options = [
    "ALL",
    *sorted(
        runs_df[
            "run_status"
        ]
        .dropna()
        .unique()
        .tolist()
    ),
]

selected_status = (
    filter_col1.selectbox(
        "Run status",
        status_options,
    )
)

search_text = (
    filter_col2.text_input(
        "Search source path",
        placeholder=(
            "sample_customers.csv"
        ),
    )
)

filtered_df = (
    runs_df.copy()
)

if selected_status != "ALL":
    filtered_df = (
        filtered_df[
            filtered_df[
                "run_status"
            ]
            == selected_status
        ]
    )

if search_text.strip():
    filtered_df = (
        filtered_df[
            filtered_df[
                "source_path"
            ]
            .astype(str)
            .str.contains(
                search_text,
                case=False,
                na=False,
            )
        ]
    )

history_columns = [
    "pipeline_run_id",
    "run_status",
    "attempt_count",
    "source_path",
    "validation_status",
    "governance_decision",
    "trust_score",
    "lifecycle_state",
    "duration_ms",
    "started_at",
    "finished_at",
]

st.dataframe(
    filtered_df[
        history_columns
    ],
    use_container_width=True,
    hide_index=True,
)

st.markdown(
    '<div class="section-title">'
    "4. Pipeline Run Detail"
    "</div>",
    unsafe_allow_html=True,
)

available_run_ids = (
    runs_df[
        "pipeline_run_id"
    ]
    .astype(int)
    .tolist()
)

selected_run_id = (
    st.selectbox(
        "Select Pipeline Run ID",
        available_run_ids,
        format_func=(
            lambda run_id: (
                f"Run #{run_id}"
            )
        ),
    )
)

try:
    selected_run = (
        load_pipeline_run(
            int(
                selected_run_id
            )
        )
    )

except requests.RequestException as exc:
    st.error(
        "Không thể tải pipeline "
        "run detail."
    )

    st.code(
        str(exc),
        language=None,
    )

    st.stop()

(
    detail_col1,
    detail_col2,
    detail_col3,
    detail_col4,
) = st.columns(4)

detail_col1.metric(
    "Status",
    str(
        selected_run[
            "run_status"
        ]
    ),
)

detail_col2.metric(
    "Attempts",
    int(
        selected_run[
            "attempt_count"
        ]
    ),
)

detail_col3.metric(
    "Duration",
    format_duration(
        selected_run.get(
            "duration_ms"
        )
    ),
)

detail_col4.metric(
    "Trust Score",
    (
        selected_run.get(
            "trust_score"
        )
        if selected_run.get(
            "trust_score"
        )
        is not None
        else "N/A"
    ),
)

st.markdown(
    "**Source Path**"
)

st.code(
    str(
        selected_run[
            "source_path"
        ]
    ),
    language=None,
)

metadata_col1, metadata_col2 = (
    st.columns(2)
)

with metadata_col1:
    st.markdown(
        "**Airflow metadata**"
    )

    st.write(
        "DAG ID:",
        selected_run[
            "dag_id"
        ],
    )

    st.write(
        "Airflow Run ID:",
        selected_run[
            "airflow_run_id"
        ],
    )

    st.write(
        "Started:",
        selected_run[
            "started_at"
        ],
    )

    st.write(
        "Finished:",
        display_value(
            selected_run.get(
                "finished_at"
            )
        ),
    )

with metadata_col2:
    st.markdown(
        "**Governance metadata**"
    )

    st.write(
        "Catalog ID:",
        display_value(
            selected_run.get(
                "catalog_id"
            )
        ),
    )

    st.write(
        "Version ID:",
        display_value(
            selected_run.get(
                "version_id"
            )
        ),
    )

    st.write(
        "Validation:",
        display_value(
            selected_run.get(
                "validation_status"
            )
        ),
    )

    st.write(
        "Governance:",
        display_value(
            selected_run.get(
                "governance_decision"
            )
        ),
    )

    st.write(
        "Lifecycle:",
        display_value(
            selected_run.get(
                "lifecycle_state"
            )
        ),
    )
    
st.markdown(
    '<div class="section-title">'
    "5. Error Diagnostics"
    "</div>",
    unsafe_allow_html=True,
)

error_type = (
    selected_run.get(
        "error_type"
    )
)

error_message = (
    selected_run.get(
        "error_message"
    )
)

if error_type:
    st.error(
        f"{error_type}"
    )

    if error_message:
        st.code(
            str(
                error_message
            ),
            language=None,
        )

    if (
        selected_run.get(
            "attempt_count",
            0,
        )
        > 1
    ):
        st.warning(
            "Run này đã retry "
            f"{selected_run['attempt_count']} "
            "workflow attempts."
        )

else:
    st.success(
        "Run này không có persisted error."
    )

with st.expander(
    "Raw Pipeline Run JSON"
):
    st.json(
        selected_run
    )