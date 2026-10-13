from __future__ import annotations

from html import escape

import streamlit as st


def render_page_header(
    title: str,
    subtitle: str,
) -> None:
    """Render a safe, reusable page header."""
    safe_title = escape(title, quote=True)
    safe_subtitle = escape(subtitle, quote=True)

    subtitle_html = (
        f'<p class="adt-page-subtitle">{safe_subtitle}</p>'
        if subtitle
        else ""
    )

    st.markdown(
        f"""
        <div class="adt-page-header">
            <h1 class="adt-page-title">{safe_title}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

JOURNEY_STEPS = (
    "Upload Dataset",
    "Data Profile",
    "Quality Issues",
    "Trust Score",
)


def build_journey_html(active_step: str) -> str:
    """Build a navigation journey without fake completion states."""
    if active_step not in JOURNEY_STEPS:
        raise ValueError("Unknown journey step")

    items = []

    for number, title in enumerate(JOURNEY_STEPS, start=1):
        active = title == active_step
        css_class = (
            "adt-journey-step is-active"
            if active
            else "adt-journey-step"
        )
        current = ' aria-current="step"' if active else ""

        items.append(
            f'<div class="{css_class}"{current}>'
            f'<span class="adt-journey-number">{number}</span>'
            f'<span class="adt-journey-label">{escape(title)}</span>'
            "</div>"
        )

    return (
        '<nav class="adt-journey" aria-label="Dataset journey">'
        + "".join(items)
        + "</nav>"
    )
