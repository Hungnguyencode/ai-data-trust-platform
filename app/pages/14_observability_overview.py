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

OBSERVABILITY_URL = (
    f"{API_BASE_URL}/api/observability"
)


def load_observability_overview(
    *,
    event_limit: int = 100,
    run_limit: int = 100,
) -> dict[str, Any]:
    response = requests.get(
        f"{OBSERVABILITY_URL}/overview",
        params={
            "event_limit": event_limit,
            "run_limit": run_limit,
        },
        timeout=15,
    )

    response.raise_for_status()

    return dict(
        response.json()
    )


def normalize_status(
    value: Any,
) -> str:
    if value is None:
        return "NO DATA"

    status = str(value).strip()

    if not status:
        return "NO DATA"

    return status.upper()


def metric_status(
    *,
    value: int,
    healthy_when_zero: bool = False,
) -> str:
    if healthy_when_zero:
        return (
            "low"
            if value == 0
            else "high"
        )

    return "low"


def freshness_card_status(
    status: str,
) -> str:
    if status == "FRESH":
        return "low"

    if status == "STALE":
        return "high"

    return "medium"


def volume_card_status(
    status: str,
) -> str:
    if status == "NORMAL":
        return "low"

    if status in {
        "DROP",
        "SPIKE",
    }:
        return "high"

    return "medium"


def pipeline_card_status(
    status: str,
) -> str:
    if status == "SUCCESS":
        return "low"

    if status == "FAILED":
        return "high"

    if status in {
        "RUNNING",
        "QUEUED",
    }:
        return "medium"

    return "medium"


def build_dataset_frame(
    datasets: list[dict[str, Any]],
) -> pd.DataFrame:
    if not datasets:
        return pd.DataFrame()

    records: list[dict[str, Any]] = []

    for item in datasets:
        freshness_status = normalize_status(
            item.get(
                "freshness_status"
            )
        )

        volume_status = normalize_status(
            item.get(
                "volume_status"
            )
        )

        pipeline_status = normalize_status(
            item.get(
                "latest_pipeline_status"
            )
        )

        records.append(
            {
                "catalog_id": item[
                    "catalog_id"
                ],
                "freshness_monitoring": (
                    "ENABLED"
                    if item.get(
                        "freshness_enabled"
                    )
                    else "DISABLED"
                ),
                "freshness_status": (
                    freshness_status
                ),
                "freshness_checked_at": (
                    item.get(
                        "freshness_checked_at"
                    )
                ),
                "volume_monitoring": (
                    "ENABLED"
                    if item.get(
                        "volume_enabled"
                    )
                    else "DISABLED"
                ),
                "volume_status": (
                    volume_status
                ),
                "volume_checked_at": (
                    item.get(
                        "volume_checked_at"
                    )
                ),
                "latest_pipeline_run_id": (
                    item.get(
                        "latest_pipeline_run_id"
                    )
                ),
                "latest_pipeline_status": (
                    pipeline_status
                ),
                "pipeline_finished_at": (
                    item.get(
                        "latest_pipeline_finished_at"
                    )
                ),
                "recent_events": int(
                    item.get(
                        "recent_operational_event_count",
                        0,
                    )
                    or 0
                ),
            }
        )

    return pd.DataFrame(
        records
    )


st.set_page_config(
    page_title="Observability Overview",
    page_icon="🔭",
    layout="wide",
)

inject_custom_css()

st.markdown(
    """
    <div class="main-title">
        🔭 Data Observability Overview
    </div>
    <div class="subtitle">
        Một control center tổng hợp trạng thái
        Freshness, Volume, Pipeline Runs
        và Operational Events của các dataset
        đang được monitoring.
    </div>
    """,
    unsafe_allow_html=True,
)

header_col1, header_col2 = st.columns(
    [5, 1]
)

with header_col1:
    st.caption(
        "Nguồn dữ liệu: "
        "FastAPI Observability Overview API. "
        "Trang này không query SQL Server trực tiếp."
    )

with header_col2:
    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):
        st.rerun()

try:
    overview = (
        load_observability_overview()
    )

except requests.RequestException as exc:
    st.error(
        "Không thể kết nối "
        "Observability Overview API."
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

summary = dict(
    overview.get(
        "summary",
        {},
    )
)

datasets = list(
    overview.get(
        "datasets",
        [],
    )
)

monitored_dataset_count = int(
    summary.get(
        "monitored_dataset_count",
        0,
    )
    or 0
)

freshness_policy_count = int(
    summary.get(
        "freshness_policy_count",
        0,
    )
    or 0
)

freshness_breach_count = int(
    summary.get(
        "freshness_breach_count",
        0,
    )
    or 0
)

volume_policy_count = int(
    summary.get(
        "volume_policy_count",
        0,
    )
    or 0
)

volume_breach_count = int(
    summary.get(
        "volume_breach_count",
        0,
    )
    or 0
)

operational_event_count = int(
    summary.get(
        "operational_event_count",
        0,
    )
    or 0
)

failed_pipeline_count = int(
    summary.get(
        "recent_failed_pipeline_run_count",
        0,
    )
    or 0
)

st.markdown(
    '<div class="section-title">'
    "1. Platform Observability Summary"
    "</div>",
    unsafe_allow_html=True,
)

(
    metric_col1,
    metric_col2,
    metric_col3,
    metric_col4,
) = st.columns(4)

with metric_col1:
    render_metric_card(
        "Monitored Datasets",
        str(monitored_dataset_count),
        "Freshness and/or volume policy",
        status="low",
    )

with metric_col2:
    render_metric_card(
        "Freshness Policies",
        str(freshness_policy_count),
        (
            f"{freshness_breach_count} "
            "current breach(es)"
        ),
        status=metric_status(
            value=freshness_breach_count,
            healthy_when_zero=True,
        ),
    )

with metric_col3:
    render_metric_card(
        "Volume Policies",
        str(volume_policy_count),
        (
            f"{volume_breach_count} "
            "current breach(es)"
        ),
        status=metric_status(
            value=volume_breach_count,
            healthy_when_zero=True,
        ),
    )

with metric_col4:
    render_metric_card(
        "Operational Events",
        str(operational_event_count),
        "Loaded recent event window",
        status=(
            "medium"
            if operational_event_count
            else "low"
        ),
    )

summary_col1, summary_col2 = (
    st.columns(2)
)

with summary_col1:
    render_metric_card(
        "Freshness Breaches",
        str(freshness_breach_count),
        "Datasets with latest status = STALE",
        status=metric_status(
            value=freshness_breach_count,
            healthy_when_zero=True,
        ),
    )

with summary_col2:
    render_metric_card(
        "Recent Failed Pipeline Runs",
        str(failed_pipeline_count),
        "Failures inside loaded run history",
        status=metric_status(
            value=failed_pipeline_count,
            healthy_when_zero=True,
        ),
    )

if (
    freshness_breach_count == 0
    and volume_breach_count == 0
):
    render_recommendation_box(
        (
            "Các latest observability check hiện "
            "không có <b>Freshness</b> hoặc "
            "<b>Volume breach</b>."
        ),
        level="success",
    )

else:
    render_recommendation_box(
        (
            "Có dataset đang vi phạm "
            "Freshness hoặc Volume policy. "
            "Xem chi tiết theo dataset bên dưới."
        ),
        level="danger",
    )

if failed_pipeline_count > 0:
    st.info(
        f"Có {failed_pipeline_count} pipeline run "
        "FAILED trong cửa sổ lịch sử gần đây. "
        "Con số này không có nghĩa pipeline hiện tại "
        "đang FAILED; hãy xem Latest Pipeline Status "
        "của từng dataset bên dưới."
    )

st.markdown(
    '<div class="section-title">'
    "2. Dataset Health"
    "</div>",
    unsafe_allow_html=True,
)

if not datasets:
    st.info(
        "Chưa có dataset nào đang được "
        "Freshness hoặc Volume monitoring."
    )

    st.stop()

catalog_options = [
    "ALL",
    *[
        str(
            item["catalog_id"]
        )
        for item in datasets
    ],
]

filter_col1, filter_col2 = (
    st.columns(2)
)

with filter_col1:
    selected_catalog = st.selectbox(
        "Catalog",
        catalog_options,
    )

with filter_col2:
    health_filter = st.selectbox(
        "Health filter",
        [
            "ALL",
            "HEALTHY",
            "ATTENTION",
        ],
    )

filtered_datasets = []

for item in datasets:
    catalog_matches = (
        selected_catalog == "ALL"
        or str(
            item["catalog_id"]
        )
        == selected_catalog
    )

    freshness_status = (
        normalize_status(
            item.get(
                "freshness_status"
            )
        )
    )

    volume_status = (
        normalize_status(
            item.get(
                "volume_status"
            )
        )
    )

    pipeline_status = (
        normalize_status(
            item.get(
                "latest_pipeline_status"
            )
        )
    )

    needs_attention = (
        freshness_status == "STALE"
        or volume_status
        in {
            "DROP",
            "SPIKE",
        }
        or pipeline_status == "FAILED"
    )

    health_matches = (
        health_filter == "ALL"
        or (
            health_filter == "ATTENTION"
            and needs_attention
        )
        or (
            health_filter == "HEALTHY"
            and not needs_attention
        )
    )

    if (
        catalog_matches
        and health_matches
    ):
        filtered_datasets.append(
            item
        )

if not filtered_datasets:
    st.info(
        "Không có dataset phù hợp "
        "với bộ lọc hiện tại."
    )

else:
    for item in filtered_datasets:
        catalog_id = int(
            item[
                "catalog_id"
            ]
        )

        freshness_status = (
            normalize_status(
                item.get(
                    "freshness_status"
                )
            )
        )

        volume_status = (
            normalize_status(
                item.get(
                    "volume_status"
                )
            )
        )

        pipeline_status = (
            normalize_status(
                item.get(
                    "latest_pipeline_status"
                )
            )
        )

        event_count = int(
            item.get(
                "recent_operational_event_count",
                0,
            )
            or 0
        )

        st.markdown(
            f"### Catalog {catalog_id}"
        )

        (
            dataset_col1,
            dataset_col2,
            dataset_col3,
            dataset_col4,
        ) = st.columns(4)

        with dataset_col1:
            render_metric_card(
                "Freshness",
                freshness_status,
                (
                    "Monitoring enabled"
                    if item.get(
                        "freshness_enabled"
                    )
                    else "Monitoring disabled"
                ),
                status=(
                    freshness_card_status(
                        freshness_status
                    )
                ),
            )

        with dataset_col2:
            render_metric_card(
                "Volume",
                volume_status,
                (
                    "Monitoring enabled"
                    if item.get(
                        "volume_enabled"
                    )
                    else "Monitoring disabled"
                ),
                status=(
                    volume_card_status(
                        volume_status
                    )
                ),
            )

        with dataset_col3:
            render_metric_card(
                "Latest Pipeline",
                pipeline_status,
                (
                    "Run ID: "
                    + str(
                        item.get(
                            "latest_pipeline_run_id"
                        )
                    )
                    if item.get(
                        "latest_pipeline_run_id"
                    )
                    is not None
                    else "No persisted run"
                ),
                status=(
                    pipeline_card_status(
                        pipeline_status
                    )
                ),
            )

        with dataset_col4:
            render_metric_card(
                "Recent Events",
                str(event_count),
                "Loaded operational events",
                status=(
                    "medium"
                    if event_count
                    else "low"
                ),
            )

        needs_attention = (
            freshness_status == "STALE"
            or volume_status
            in {
                "DROP",
                "SPIKE",
            }
            or pipeline_status == "FAILED"
        )

        if needs_attention:
            render_recommendation_box(
                (
                    f"Catalog <b>{catalog_id}</b> "
                    "có ít nhất một tín hiệu "
                    "cần kiểm tra."
                ),
                level="danger",
            )

        else:
            render_recommendation_box(
                (
                    f"Latest state của Catalog "
                    f"<b>{catalog_id}</b> "
                    "không có breach hoặc "
                    "pipeline failure."
                ),
                level="success",
            )

        detail_col1, detail_col2, detail_col3 = (
            st.columns(3)
        )

        with detail_col1:
            st.write(
                "**Freshness checked:**"
            )

            st.code(
                str(
                    item.get(
                        "freshness_checked_at"
                    )
                    or "N/A"
                ),
                language=None,
            )

        with detail_col2:
            st.write(
                "**Volume checked:**"
            )

            st.code(
                str(
                    item.get(
                        "volume_checked_at"
                    )
                    or "N/A"
                ),
                language=None,
            )

        with detail_col3:
            st.write(
                "**Pipeline finished:**"
            )

            st.code(
                str(
                    item.get(
                        "latest_pipeline_finished_at"
                    )
                    or "N/A"
                ),
                language=None,
            )

        st.divider()

st.markdown(
    '<div class="section-title">'
    "3. Observability Dataset Table"
    "</div>",
    unsafe_allow_html=True,
)

dataset_frame = build_dataset_frame(
    datasets
)

if dataset_frame.empty:
    st.info(
        "Không có observability records."
    )

else:
    st.dataframe(
        dataset_frame,
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "Freshness/Volume breach phản ánh latest persisted check. "
    "Failed Pipeline Runs và Operational Events là số liệu "
    "trong history window mà API đã tải."
)