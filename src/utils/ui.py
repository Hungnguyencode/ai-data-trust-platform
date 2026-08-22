from __future__ import annotations

import streamlit as st


def inject_custom_css() -> None:
    """
    CSS dùng chung cho toàn bộ Streamlit app.
    Giúp giao diện nhìn giống dashboard sản phẩm hơn.
    """
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.6rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
            color: #1f2937;
        }

        .subtitle {
            font-size: 1rem;
            color: #6b7280;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 1.45rem;
            font-weight: 750;
            color: #111827;
            margin-top: 1.2rem;
            margin-bottom: 0.8rem;
        }

        .metric-card {
            padding: 1.2rem 1.3rem;
            border-radius: 1.1rem;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e5e7eb;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            min-height: 120px;
        }

        .metric-label {
            color: #6b7280;
            font-size: 0.92rem;
            margin-bottom: 0.35rem;
            font-weight: 600;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 800;
            color: #111827;
            line-height: 1.15;
            word-break: break-word;
        }

        .metric-help {
            margin-top: 0.5rem;
            color: #6b7280;
            font-size: 0.85rem;
        }

        .status-low {
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 1px solid #a7f3d0;
        }

        .status-medium {
            background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
            border: 1px solid #fde68a;
        }

        .status-high {
            background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%);
            border: 1px solid #fdba74;
        }

        .status-critical {
            background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
            border: 1px solid #fca5a5;
        }

        .recommendation-box {
            padding: 1rem 1.2rem;
            border-radius: 1rem;
            background: #eff6ff;
            border-left: 6px solid #2563eb;
            color: #1e3a8a;
            margin-top: 0.7rem;
            margin-bottom: 1rem;
        }

        .warning-box {
            padding: 1rem 1.2rem;
            border-radius: 1rem;
            background: #fff7ed;
            border-left: 6px solid #f97316;
            color: #7c2d12;
            margin-top: 0.7rem;
            margin-bottom: 1rem;
        }

        .success-box {
            padding: 1rem 1.2rem;
            border-radius: 1rem;
            background: #ecfdf5;
            border-left: 6px solid #10b981;
            color: #064e3b;
            margin-top: 0.7rem;
            margin-bottom: 1rem;
        }

        .danger-box {
            padding: 1rem 1.2rem;
            border-radius: 1rem;
            background: #fef2f2;
            border-left: 6px solid #ef4444;
            color: #7f1d1d;
            margin-top: 0.7rem;
            margin-bottom: 1rem;
        }

        .small-muted {
            color: #6b7280;
            font-size: 0.9rem;
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            padding: 1rem;
            border-radius: 1rem;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(
    label: str,
    value: str,
    help_text: str = "",
    status: str | None = None,
) -> None:
    """
    Card metric đẹp hơn st.metric, không bị cắt chữ dài.
    status: low | medium | high | critical | None
    """
    status_class = ""

    if status == "low":
        status_class = "status-low"
    elif status == "medium":
        status_class = "status-medium"
    elif status == "high":
        status_class = "status-high"
    elif status == "critical":
        status_class = "status-critical"

    st.markdown(
        f"""
        <div class="metric-card {status_class}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recommendation_box(message: str, level: str = "info") -> None:
    """
    Box nhận xét/khuyến nghị.
    level: info | success | warning | danger
    """
    css_class = "recommendation-box"

    if level == "success":
        css_class = "success-box"
    elif level == "warning":
        css_class = "warning-box"
    elif level == "danger":
        css_class = "danger-box"

    st.markdown(
        f"""
        <div class="{css_class}">
            {message}
        </div>
        """,
        unsafe_allow_html=True,
    )