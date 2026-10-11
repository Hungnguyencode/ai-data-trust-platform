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
