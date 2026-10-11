from __future__ import annotations

COLORS = {
    "sidebar_background": "#172A44",
    "workspace_background": "#F7F9FC",
    "surface_background": "#FFFFFF",
    "primary": "#2563EB",
}



def build_theme_css() -> str:
    """Build reusable presentation CSS from design tokens."""
    tokens = "\n".join(
        f"    --adt-{name.replace('_', '-')}: {color};"
        for name, color in COLORS.items()
    )

    return f"""
:root {{
{tokens}
}}

/* Enterprise App Shell: light workspace */
[data-testid="stAppViewContainer"] {{
    background-color: var(--adt-workspace-background);
}}

[data-testid="stHeader"] {{
    background-color: var(--adt-workspace-background);
}}

/* Enterprise App Shell: dark navy sidebar */
[data-testid="stSidebar"] {{
    background-color: var(--adt-sidebar-background);
    background-image: linear-gradient(
        180deg,
        #203955 0%,
        #172A44 55%,
        #13243C 100%
    );
    border-right: 1px solid #29415F;
}}

[data-testid="stSidebar"] [data-testid="stSidebarContent"],
[data-testid="stSidebar"] [data-testid="stSidebarNav"] {{
    background-color: transparent;
}}

/* Enterprise branding header */
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{
    background-color: #102039;
    min-height: 76px;
    padding: 14px 24px;
    box-sizing: border-box;
    align-items: center;
}}

[data-testid="stSidebar"] [data-testid="stSidebarHeader"] img[data-testid="stLogo"] {{
    height: 44px !important;
    width: auto !important;
    object-fit: contain;
    margin: 0 8px 0 0;
}}

/* Navigation links */
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{
    color: #D8E5F5;
    border-radius: 0.5rem;
    margin: 0.125rem 0.5rem;
    transition: background-color 120ms ease;
}}

[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {{
    color: #FFFFFF;
    background-color: #29476C;
}}

/* Readable navigation text and icons */
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span {{
    color: #D8E5F5 !important;
}}

[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] svg {{
    color: #D8E5F5 !important;
}}

/* Enterprise Material Symbols */
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] [data-testid="stIconMaterial"] {{
    color: #93C5FD !important;
    font-size: 21px !important;
    font-variation-settings: "FILL" 0, "wght" 450, "GRAD" 0, "opsz" 24 !important;
    line-height: 1;
}}

/* Selected navigation item */
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {{
    color: #FFFFFF;
    background-color: var(--adt-primary);
    font-weight: 650;
}}

[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] * {{
    color: inherit;
}}

/* Group labels */
[data-testid="stSidebar"] [data-testid="stSidebarNav"] [data-testid="stNavSectionHeader"] {{
    color: #93C5FD;
    font-weight: 700;
    letter-spacing: 0.06em;
}}

.adt-page-header {{
    margin-bottom: 1.5rem;
}}

.adt-page-title {{
    color: var(--adt-sidebar-background);
    font-size: 2rem;
    font-weight: 750;
    line-height: 1.2;
    margin: 0;
}}

.adt-page-subtitle {{
    color: var(--adt-sidebar-background);
    opacity: 0.72;
    font-size: 0.95rem;
    line-height: 1.6;
    margin-top: 0.5rem;
}}
""".strip()


def inject_theme_css() -> None:
    """Inject the shared design system stylesheet."""
    import streamlit as st

    st.markdown(
        f"<style>{build_theme_css()}</style>",
        unsafe_allow_html=True,
    )

def build_selected_nav_css(url_path: str) -> str:
    """Build safe CSS for the active navigation link."""
    slug = url_path.strip("/")

    allowed = set(
        "abcdefghijklmnopqrstuvwxyz0123456789_-/"
    )

    if "//" in slug or any(
        char not in allowed for char in slug
    ):
        raise ValueError("Invalid navigation URL path")

    selector = (
        '[data-testid="stSidebarNavLink"]'
        f'[href$="/{slug}"]'
    )

    return f"""
[data-testid="stSidebar"] {selector} {{
    background-color: var(--adt-primary) !important;
}}

[data-testid="stSidebar"] {selector},
[data-testid="stSidebar"] {selector} span,
[data-testid="stSidebar"] {selector} svg {{
    color: #FFFFFF !important;
}}

[data-testid="stSidebar"] {selector} [data-testid="stIconMaterial"] {{
    color: #FFFFFF !important;
}}
""".strip()
