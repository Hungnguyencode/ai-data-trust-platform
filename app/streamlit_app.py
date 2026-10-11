from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ui.navigation import HOME_PAGE, PAGE_GROUPS, PAGE_METADATA  # noqa: E402
from app.ui.theme import build_selected_nav_css, inject_theme_css  # noqa: E402

st.set_page_config(
    page_title="AI Data Trust Platform",
    page_icon="🧠",
    layout="wide",
)

st.logo(
    str(PROJECT_ROOT / "app" / "assets" / "brand_wordmark.svg"),
    icon_image=str(PROJECT_ROOT / "app" / "assets" / "brand_icon.svg"),
    size="large",
)


pages = {
    "HOME": [
        st.Page(
            PROJECT_ROOT / HOME_PAGE,
            title="Dashboard",
            icon=":material/home:",
            default=True,
        ),
    ],
}

for group, paths in PAGE_GROUPS.items():
    pages[group] = [
        st.Page(
            PROJECT_ROOT / path,
            title=PAGE_METADATA[path][0],
            icon=PAGE_METADATA[path][1],
        )
        for path in paths
    ]

page = st.navigation(pages, expanded=True)
inject_theme_css()
st.markdown(
    f"<style>{build_selected_nav_css(page.url_path)}</style>",
    unsafe_allow_html=True,
)
page.run()
