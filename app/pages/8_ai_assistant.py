from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

from app.services.assistant_api import (
    AssistantApiError,
    ask_catalog_copilot,
)
from src.assistant.ai_explainer import generate_quick_insight
from src.assistant.fallback_rules import priority_action_plan, smart_diagnosis
from src.assistant.prompt_builder import (
    build_available_result_names,
    build_grounding_notice,
    build_missing_result_names,
)

st.set_page_config(
    page_title="Data Trust Copilot",
    page_icon="🤖",
    layout="wide",
)


def inject_chat_css() -> None:
    st.markdown(
        """
        <style>
        .assistant-page-title {
            font-size: 44px;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .assistant-subtitle {
            color: #64748b;
            font-size: 17px;
            margin-bottom: 28px;
        }

        .metric-card {
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 22px 24px;
            background: #ffffff;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            min-height: 145px;
        }

        .metric-card.good {
            background: #dcfce7;
            border-color: #86efac;
        }

        .metric-card.warn {
            background: #fef3c7;
            border-color: #facc15;
        }

        .metric-label {
            color: #64748b;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .metric-value {
            color: #020617;
            font-size: 32px;
            font-weight: 850;
            line-height: 1.15;
        }

        .metric-help {
            color: #64748b;
            font-size: 14px;
            margin-top: 10px;
        }

        .notice-box {
            padding: 18px 22px;
            border-radius: 16px;
            margin: 18px 0;
            border-left: 6px solid #f97316;
            background: #fff7ed;
            color: #9a3412;
            font-size: 16px;
        }

        .info-box {
            padding: 18px 22px;
            border-radius: 16px;
            margin: 18px 0;
            border-left: 6px solid #3b82f6;
            background: #eff6ff;
            color: #1e3a8a;
            font-size: 16px;
        }

        .quick-card {
            padding: 18px 20px;
            border-radius: 18px;
            border: 1px solid #e5e7eb;
            background: #ffffff;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
            margin-bottom: 10px;
        }

        .quick-card-title {
            font-size: 19px;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .quick-card-body {
            color: #475569;
            font-size: 15px;
        }

        .api-status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 9px 14px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 800;
            margin-bottom: 14px;
            border: 1px solid #d1fae5;
            background: #ecfdf5;
            color: #047857;
        }

        .api-status-badge.offline {
            border-color: #fed7aa;
            background: #fff7ed;
            color: #c2410c;
        }

        .api-dot {
            width: 9px;
            height: 9px;
            border-radius: 999px;
            background: #10b981;
            display: inline-block;
        }

        .api-status-badge.offline .api-dot {
            background: #f97316;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def first_state_value(keys: List[str], default: Any = None) -> Any:
    for key in keys:
        if key in st.session_state and st.session_state[key] is not None:
            value = st.session_state[key]

            if isinstance(value, pd.DataFrame) and value.empty:
                continue

            if isinstance(value, dict) and not value:
                continue

            return value

    return default


def dataframe_to_records(value: Any, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if value is None:
        return []

    if isinstance(value, pd.DataFrame):
        df = value.copy()

        if limit is not None:
            df = df.head(limit)

        return df.where(pd.notnull(df), None).to_dict(orient="records")

    if isinstance(value, list):
        return value[:limit] if limit else value

    if isinstance(value, dict):
        return [value]

    return []


def extract_dataset_context() -> Dict[str, Any]:
    df = first_state_value(
        [
            "df",
            "uploaded_df",
            "current_df",
            "dataset_df",
            "dataframe",
        ]
    )

    file_name = first_state_value(
        [
            "file_name",
            "uploaded_file_name",
            "dataset_name",
            "current_file_name",
        ],
        "N/A",
    )

    file_type = first_state_value(
        [
            "file_type",
            "uploaded_file_type",
            "dataset_file_type",
        ],
        "CSV",
    )

    if isinstance(df, pd.DataFrame):
        total_rows = int(df.shape[0])
        total_columns = int(df.shape[1])
        total_cells = int(total_rows * total_columns)
        missing_cells = int(df.isna().sum().sum())
        duplicate_rows = int(df.duplicated().sum())
        columns = list(df.columns)
    else:
        total_rows = first_state_value(["total_rows"], "N/A")
        total_columns = first_state_value(["total_columns"], "N/A")
        total_cells = first_state_value(["total_cells"], "N/A")
        missing_cells = first_state_value(["missing_cells"], "N/A")
        duplicate_rows = first_state_value(["duplicate_rows"], "N/A")
        columns = []

    return {
        "file_name": file_name,
        "file_type": file_type,
        "total_rows": total_rows,
        "total_columns": total_columns,
        "total_cells": total_cells,
        "missing_cells": missing_cells,
        "duplicate_rows": duplicate_rows,
        "columns": columns,
    }


def extract_quality_context() -> Dict[str, Any]:
    quality_report = first_state_value(
        [
            "current_quality_report",
            "quality_report",
            "quality_summary",
            "quality_result",
            "quality_results",
            "quality_overview",
        ],
        {},
    )

    result: Dict[str, Any] = {}

    if isinstance(quality_report, dict):
        summary = quality_report.get("summary", {})
        issues_df = quality_report.get("issues_df")

        if isinstance(summary, dict):
            result.update(summary)

        issues = dataframe_to_records(issues_df)

        if issues:
            result["issues"] = issues
            result.setdefault("total_issues", len(issues))

        return result

    return result


def extract_trust_context() -> Dict[str, Any]:
    trust_report = first_state_value(
        [
            "current_trust_score_report",
            "trust_score_report",
            "trust_score_result",
            "score_result",
            "trust_result",
            "data_trust_score",
        ],
        {},
    )

    result: Dict[str, Any] = {}

    if isinstance(trust_report, dict):
        result.update(
            {
                "overall_score": trust_report.get("overall_score"),
                "risk_level": trust_report.get("risk_level"),
                "ai_readiness": trust_report.get("ai_readiness"),
                "conclusion": trust_report.get("conclusion"),
                "recommendation": trust_report.get("recommendation")
                or trust_report.get("conclusion"),
            }
        )

        breakdown_df = trust_report.get("breakdown_df")
        components = dataframe_to_records(breakdown_df)

        normalized_components: List[Dict[str, Any]] = []

        for item in components:
            if not isinstance(item, dict):
                continue

            normalized_item = dict(item)

            if "raw_value" not in normalized_item:
                normalized_item["raw_value"] = normalized_item.get("raw_value (%)")

            if "weighted_score" not in normalized_item:
                normalized_item["weighted_score"] = normalized_item.get("weighted_score")

            normalized_components.append(normalized_item)

        if normalized_components:
            result["components"] = normalized_components

        return result

    return result


def extract_anomaly_context() -> Dict[str, Any]:
    anomaly_report = first_state_value(
        [
            "current_anomaly_report",
            "anomaly_report",
            "anomaly_result",
            "anomaly_results",
            "anomaly_summary",
        ],
        {},
    )

    result: Dict[str, Any] = {}

    if isinstance(anomaly_report, dict):
        summary = anomaly_report.get("summary", {})
        summary_df = anomaly_report.get("summary_df")

        if isinstance(summary, dict):
            result.update(
                {
                    "total_rows": summary.get("total_rows"),
                    "total_anomaly_rows": summary.get("total_anomaly_rows"),
                    "anomaly_rate": summary.get("anomaly_rate (%)")
                    or summary.get("anomaly_rate"),
                    "anomaly_score": summary.get("anomaly_score"),
                    "risk_level": summary.get("risk_level"),
                }
            )

        summary_records = dataframe_to_records(summary_df)

        if summary_records:
            result["method_summary"] = summary_records

        return result

    return result


def extract_privacy_context() -> Dict[str, Any]:
    privacy_report = first_state_value(
        [
            "current_privacy_report",
            "privacy_report",
            "privacy_result",
            "privacy_results",
            "privacy_summary",
        ],
        {},
    )

    result: Dict[str, Any] = {}

    if isinstance(privacy_report, dict):
        summary = privacy_report.get("summary", {})
        findings_df = privacy_report.get("findings_df")

        if isinstance(summary, dict):
            result.update(
                {
                    "total_rows": summary.get("total_rows"),
                    "total_columns": summary.get("total_columns"),
                    "total_cells": summary.get("total_cells"),
                    "pii_columns": summary.get("pii_columns"),
                    "pii_cells": summary.get("pii_cells"),
                    "pii_cell_rate": summary.get("pii_cell_rate (%)")
                    or summary.get("pii_cell_rate"),
                    "privacy_safety_score": summary.get("privacy_safety_score"),
                    "risk_level": summary.get("risk_level"),
                    "high_risk_findings": summary.get("high_risk_findings"),
                }
            )

        findings = dataframe_to_records(findings_df)

        if findings:
            result["findings"] = findings

        return result

    return result


def extract_drift_context() -> Dict[str, Any]:
    drift_report = first_state_value(
        [
            "current_drift_report",
            "drift_report",
            "drift_result",
            "drift_results",
            "drift_summary",
        ],
        {},
    )

    result: Dict[str, Any] = {}

    if not isinstance(drift_report, dict):
        return result

    summary = drift_report.get("summary", {})
    all_drift_df = drift_report.get("all_drift_df")
    numeric_drift_df = drift_report.get("numeric_drift_df")
    categorical_drift_df = drift_report.get("categorical_drift_df")
    schema_drift_df = drift_report.get("schema_drift_df")

    if isinstance(summary, dict):
        drift_score = summary.get("drift_score")

        if drift_score is None and summary.get("overall_drift_level") == "None":
            drift_score = 100.0

        if drift_score is None and summary.get("overall_drift_level") in [
            "No significant drift",
            "Low",
            "Low drift",
        ]:
            drift_score = 100.0

        result.update(
            {
                "baseline_rows": summary.get("baseline_rows"),
                "current_rows": summary.get("current_rows"),
                "baseline_columns": summary.get("baseline_columns"),
                "current_columns": summary.get("current_columns"),
                "checked_common_columns": summary.get("checked_common_columns"),
                "schema_drift_count": summary.get("schema_drift_count"),
                "drifted_columns": summary.get("drifted_columns"),
                "high_drift_columns": summary.get("high_drift_columns"),
                "moderate_drift_columns": summary.get("moderate_drift_columns"),
                "drift_rate": summary.get("drift_rate (%)")
                or summary.get("drift_rate"),
                "overall_drift_level": summary.get("overall_drift_level"),
                "drift_score": drift_score,
            }
        )

    drifted_records = dataframe_to_records(all_drift_df)

    if not drifted_records:
        numeric_records = dataframe_to_records(numeric_drift_df)
        categorical_records = dataframe_to_records(categorical_drift_df)
        drifted_records = numeric_records + categorical_records

    if drifted_records:
        result["drifted_columns_detail"] = [
            item
            for item in drifted_records
            if isinstance(item, dict)
            and item.get("drift_level") not in [
                None,
                "No significant drift",
                "None",
                "N/A",
            ]
        ]

    schema_records = dataframe_to_records(schema_drift_df)

    if schema_records:
        result["schema_drift_detail"] = schema_records

    return result


def build_scan_context() -> Dict[str, Any]:
    context = {
        "dataset": extract_dataset_context(),
        "profile": first_state_value(["profile_result", "profile_results"], {}),
        "quality": extract_quality_context(),
        "trust_score": extract_trust_context(),
        "anomaly": extract_anomaly_context(),
        "privacy": extract_privacy_context(),
        "drift": extract_drift_context(),
    }

    st.session_state["assistant_scan_context"] = context
    return context


def render_metric_card(label: str, value: str, help_text: str = "", kind: str = "") -> None:
    class_name = f"metric-card {kind}".strip()

    st.markdown(
        f"""
        <div class="{class_name}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_api_status_badge(is_connected: bool) -> None:
    if is_connected:
        label = "FastAPI connected"
        class_name = "api-status-badge"
    else:
        label = "FastAPI offline — Copilot unavailable"
        class_name = "api-status-badge offline"

    st.markdown(
        f"""
        <div class="{class_name}">
            <span class="api-dot"></span>
            <span>{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_message(
    role: str,
    message: str,
    copilot_meta: Dict[str, Any] | None = None,
) -> None:
    if role == "user":
        with st.chat_message(
            "user",
            avatar="🧑",
        ):
            st.markdown(message)

        return

    with st.chat_message(
        "assistant",
        avatar="🤖",
    ):
        st.markdown(message)

        if not isinstance(
            copilot_meta,
            dict,
        ):
            return

        if not copilot_meta.get(
            "ok",
            False,
        ):
            st.caption(
                "Copilot unavailable"
            )
            return

        overall_state = str(
            copilot_meta.get(
                "overall_state"
            )
            or "UNKNOWN"
        )

        provider = str(
            copilot_meta.get(
                "provider"
            )
            or "unknown"
        )

        grounded = bool(
            copilot_meta.get(
                "grounded",
                False,
            )
        )

        used_llm = bool(
            copilot_meta.get(
                "used_llm",
                False,
            )
        )

        execution_label = (
            provider
            if used_llm
            else "deterministic fallback"
        )

        grounding_label = (
            "grounded"
            if grounded
            else "not grounded"
        )

        st.caption(
            f"{overall_state} · "
            f"{execution_label} · "
            f"{grounding_label}"
        )

        with st.expander(
            "Evidence & provider details",
            expanded=False,
        ):
            st.write(
                "**Catalog ID:**",
                copilot_meta.get(
                    "catalog_id"
                ),
            )

            st.write(
                "**Latest version ID:**",
                copilot_meta.get(
                    "latest_version_id"
                ),
            )

            st.write(
                "**Provider:**",
                provider,
            )

            st.write(
                "**Model:**",
                copilot_meta.get(
                    "model"
                )
                or "N/A",
            )

            st.write(
                "**LLM used:**",
                used_llm,
            )

            fallback_reason = (
                copilot_meta.get(
                    "fallback_reason"
                )
            )

            if fallback_reason:
                st.write(
                    "**Fallback reason:**",
                    fallback_reason,
                )

            error_type = copilot_meta.get(
                "error_type"
            )

            if error_type:
                st.write(
                    "**Provider error type:**",
                    error_type,
                )

            finding_codes = (
                copilot_meta.get(
                    "source_finding_codes",
                    [],
                )
                or []
            )

            action_codes = (
                copilot_meta.get(
                    "source_action_codes",
                    [],
                )
                or []
            )

            st.write(
                "**Finding codes:**",
                (
                    ", ".join(
                        str(code)
                        for code in finding_codes
                    )
                    if finding_codes
                    else "None"
                ),
            )

            st.write(
                "**Action codes:**",
                (
                    ", ".join(
                        str(code)
                        for code in action_codes
                    )
                    if action_codes
                    else "None"
                ),
            )


def build_copilot_chat_message(
    answer: str,
    backend_result: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "role": "assistant",
        "content": answer,
        "copilot_meta": {
            "ok": backend_result.get(
                "ok",
                False,
            ),
            "source": backend_result.get(
                "source"
            ),
            "catalog_id": backend_result.get(
                "catalog_id"
            ),
            "latest_version_id": (
                backend_result.get(
                    "latest_version_id"
                )
            ),
            "overall_state": backend_result.get(
                "overall_state"
            ),
            "grounded": backend_result.get(
                "grounded"
            ),
            "provider": backend_result.get(
                "provider"
            ),
            "model": backend_result.get(
                "model"
            ),
            "used_llm": backend_result.get(
                "used_llm"
            ),
            "fallback_reason": backend_result.get(
                "fallback_reason"
            ),
            "error_type": backend_result.get(
                "error_type"
            ),
            "source_finding_codes": (
                backend_result.get(
                    "source_finding_codes",
                    [],
                )
            ),
            "source_action_codes": (
                backend_result.get(
                    "source_action_codes",
                    [],
                )
            ),
        },
    }


def get_question_options() -> List[str]:
    return [
        "Tóm tắt trạng thái Data Trust hiện tại",
        "Dataset hiện tại đang ở trạng thái nào?",
        "Vấn đề quan trọng nhất hiện tại là gì?",
        "Mình nên xử lý việc gì trước?",
        "Có action nào cần thực hiện không?",
        "Validation hiện tại có vấn đề gì không?",
        "Governance hiện tại đang ở trạng thái nào?",
        "Lifecycle của dataset hiện tại ra sao?",
        "Freshness của dataset có cần chú ý không?",
        "Volume hiện tại có dấu hiệu bất thường không?",
        "Pipeline gần nhất có vấn đề gì không?",
        "Evidence nào dẫn tới kết luận hiện tại?",
    ]


def get_current_catalog_id() -> int | None:
    registration = st.session_state.get(
        "current_catalog_registration"
    )

    if not isinstance(
        registration,
        dict,
    ):
        return None

    raw_catalog_id = registration.get(
        "catalog_id"
    )

    if raw_catalog_id is None:
        return None

    try:
        catalog_id = int(
            raw_catalog_id
        )
    except (
        TypeError,
        ValueError,
    ):
        return None

    if catalog_id <= 0:
        return None

    return catalog_id


def get_current_version_id() -> int | None:
    registration = st.session_state.get(
        "current_catalog_registration"
    )

    if not isinstance(
        registration,
        dict,
    ):
        return None

    raw_version_id = registration.get(
        "version_id"
    )

    if raw_version_id is None:
        return None

    try:
        version_id = int(
            raw_version_id
        )
    except (
        TypeError,
        ValueError,
    ):
        return None

    if version_id <= 0:
        return None

    return version_id


def build_copilot_history(
    messages: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    start_index = 0

    first_message = (
        messages[0]
        if messages
        else None
    )

    if (
        isinstance(
            first_message,
            dict,
        )
        and first_message.get(
            "role"
        )
        == "assistant"
        and "copilot_meta"
        not in first_message
    ):
        start_index = 1

    history: List[
        Dict[str, str]
    ] = []

    for message in messages[
        start_index:
    ]:
        if not isinstance(
            message,
            dict,
        ):
            continue

        role = str(
            message.get(
                "role",
                "",
            )
            or ""
        ).strip().lower()

        if role not in {
            "user",
            "assistant",
        }:
            continue

        content = str(
            message.get(
                "content",
                "",
            )
            or ""
        ).strip()

        if not content:
            continue

        history.append(
            {
                "role": role,
                "content": content[:2000],
            }
        )

    return history[-10:]


def ask_assistant_backend(
    question: str,
    catalog_id: int | None,
    history: List[
        Dict[str, str]
    ]
    | None = None,
) -> Dict[str, Any]:
    if catalog_id is None:
        return {
            "ok": False,
            "answer": (
                "Grounded Copilot cần một dataset "
                "đã được đăng ký trong Dataset Catalog. "
                "Hãy upload dataset và hoàn tất "
                "dataset workflow trước."
            ),
            "source": "Copilot unavailable",
        }

    try:
        data = ask_catalog_copilot(
            catalog_id=catalog_id,
            question=question,
            history=history,
        )

    except AssistantApiError:
        return {
            "ok": False,
            "answer": (
                "Không gọi được Grounded Copilot backend. "
                "Hãy kiểm tra FastAPI/Uvicorn "
                "và thử lại."
            ),
            "source": "Copilot unavailable",
        }

    answer = data.get(
        "answer"
    )

    return {
        "ok": True,
        "answer": (
            str(answer)
            if answer
            else "Backend không trả về answer."
        ),
        "source": "FastAPI Copilot",
        "catalog_id": data.get(
            "catalog_id"
        ),
        "latest_version_id": data.get(
            "latest_version_id"
        ),
        "overall_state": data.get(
            "overall_state"
        ),
        "grounded": data.get(
            "grounded",
            True,
        ),
        "provider": data.get(
            "provider"
        ),
        "model": data.get(
            "model"
        ),
        "used_llm": bool(
            data.get(
                "used_llm",
                False,
            )
        ),
        "fallback_reason": data.get(
            "fallback_reason"
        ),
        "error_type": data.get(
            "error_type"
        ),
        "source_finding_codes": list(
            data.get(
                "source_finding_codes",
                [],
            )
            or []
        ),
        "source_action_codes": list(
            data.get(
                "source_action_codes",
                [],
            )
            or []
        ),
    }


def main() -> None:
    inject_chat_css()

    st.markdown(
        """
        <div class="assistant-page-title">🤖 Grounded Data Trust Copilot</div>
        <div class="assistant-subtitle">
            Copilot trả lời câu hỏi dựa trên trusted platform evidence và deterministic reasoning của dataset hiện tại.
        </div>
        """,
        unsafe_allow_html=True,
    )

    context = build_scan_context()
    available = build_available_result_names(context)
    missing = build_missing_result_names(context)

    dataset = context.get("dataset", {}) or {}
    trust = context.get("trust_score", {}) or {}

    catalog_id = get_current_catalog_id()
    version_id = get_current_version_id()

    assistant_dataset_binding = (
        catalog_id,
        version_id,
    )

    st.subheader("1. Assistant grounding status")

    api_connected = False

    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        api_connected = health_response.status_code == 200
    except Exception:
        api_connected = False

    render_api_status_badge(api_connected)

    if not api_connected:
        st.caption(
            "FastAPI backend chưa chạy. Muốn dùng backend thật, mở terminal riêng và chạy: "
            "`uvicorn api.main:app --reload --port 8000`"
        )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_metric_card(
            "Dataset",
            str(dataset.get("file_name", "N/A")),
            f"{dataset.get('total_rows', 'N/A')} rows × {dataset.get('total_columns', 'N/A')} columns",
        )

    with c2:
        render_metric_card(
            "Available Results",
            str(len(available)),
            ", ".join(available) if available else "No scan results",
            "good",
        )

    with c3:
        render_metric_card(
            "Missing Results",
            str(len(missing)),
            ", ".join(missing) if missing else "All required results available",
            "warn" if missing else "good",
        )

    with c4:
        render_metric_card(
            "Trust Score",
            str(trust.get("overall_score", "N/A")),
            trust.get("ai_readiness", "Chưa chạy Trust Score"),
            "warn" if not trust else "good",
        )

    st.markdown(
        f"""
        <div class="notice-box">
            {build_grounding_notice(context)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="info-box">
            Phần Smart diagnosis và Quick insights dùng kết quả scan trong session để hiển thị nhanh.
            Phần Grounded Copilot gửi câu hỏi, Catalog ID và bounded conversation history tới backend; backend luôn tự dựng lại trusted platform evidence. Conversation history chỉ là untrusted context, không phải platform evidence.
            Deterministic reasoning vẫn là nguồn kết luận có thẩm quyền.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("2. Smart diagnosis")

    diag_col, action_col = st.columns(2)

    with diag_col:
        with st.container(border=True):
            st.markdown(smart_diagnosis(context))

    with action_col:
        with st.container(border=True):
            st.markdown(priority_action_plan(context))

    st.subheader("3. Quick insights")

    tabs = st.tabs(
        [
            "Dataset",
            "Trust Score",
            "Quality",
            "Anomaly",
            "Privacy",
            "Drift",
            "AI Readiness",
            "Recommendations",
        ]
    )

    tab_topics = [
        "dataset",
        "trust score",
        "quality",
        "anomaly",
        "privacy",
        "drift",
        "ai readiness",
        "recommendations",
    ]

    for tab, topic in zip(tabs, tab_topics):
        with tab:
            st.markdown(generate_quick_insight(topic, context))

    st.subheader("4. Ask the Grounded Copilot")

    if (
        "assistant_messages"
        not in st.session_state
        or st.session_state.get(
            "assistant_dataset_binding"
        )
        != assistant_dataset_binding
    ):
        st.session_state[
            "assistant_dataset_binding"
        ] = assistant_dataset_binding

        st.session_state["assistant_messages"] = [
            {
                "role": "assistant",
                "content": (
                    (
                        "Mình là Grounded Data Trust Copilot. "
                        "Mình trả lời dựa trên platform evidence "
                        "được backend dựng cho dataset hiện tại. "
                        "Nếu evidence không đủ để trả lời một câu hỏi, "
                        "mình sẽ nói rõ giới hạn đó."
                    )
                ),
            }
        ]

    q_col, btn_col = st.columns([4, 1])

    with q_col:
        selected_question = st.selectbox(
            "Chọn câu hỏi mẫu",
            get_question_options(),
        )

    with btn_col:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        ask_sample = st.button("Ask", use_container_width=True)

    if ask_sample:
        question_to_answer = selected_question

        conversation_history = (
            build_copilot_history(
                st.session_state[
                    "assistant_messages"
                ]
            )
        )

        st.session_state["assistant_messages"].append(
            {
                "role": "user",
                "content": question_to_answer,
            }
        )

        backend_result = ask_assistant_backend(
            question_to_answer,
            catalog_id,
            history=conversation_history,
        )
        answer = backend_result["answer"]

        st.session_state["assistant_messages"].append(
            build_copilot_chat_message(
                answer,
                backend_result,
            )
        )

    for message in st.session_state["assistant_messages"]:
        role = message.get(
            "role",
            "assistant",
        )

        content = message.get(
            "content",
            "",
        )

        copilot_meta = message.get(
            "copilot_meta"
        )

        render_chat_message(
            role,
            content,
            copilot_meta,
        )

    manual_question = st.chat_input(
        "Hỏi Copilot về dataset hiện tại..."
    )

    if manual_question:
        conversation_history = (
            build_copilot_history(
                st.session_state[
                    "assistant_messages"
                ]
            )
        )
        st.session_state["assistant_messages"].append(
            {
                "role": "user",
                "content": manual_question,
            }
        )

        backend_result = ask_assistant_backend(
            manual_question,
            catalog_id,
            history=conversation_history,
        )
        answer = backend_result["answer"]

        st.session_state["assistant_messages"].append(
            build_copilot_chat_message(
                answer,
                backend_result,
            )
        )

        st.rerun()

    DEBUG_MODE = False

    if DEBUG_MODE:
        show_debug = st.checkbox("Show debug context", value=False)

        if show_debug:
            with st.expander("Debug: assistant context", expanded=False):
                st.json(context)


if __name__ == "__main__":
    main()