from app.ui.theme import build_theme_css


def test_sidebar_uses_subtle_enterprise_gradient():
    css = build_theme_css()

    assert '[data-testid="stSidebar"]' in css
    assert "background-image: linear-gradient(" in css

    # Keep the established navy palette.
    assert "#203955" in css
    assert "#172A44" in css
    assert "#13243C" in css

    # Preserve the existing design-token fallback.
    assert "var(--adt-sidebar-background)" in css


def test_material_navigation_icons_match_enterprise_sample():
    css = build_theme_css()

    assert (
        '[data-testid="stSidebarNavLink"] '
        '[data-testid="stIconMaterial"]'
    ) in css

    assert "color: #93C5FD !important;" in css
    assert "font-size: 21px !important;" in css
    assert '"wght" 450' in css


def test_active_material_icon_remains_white():
    from app.ui.theme import build_selected_nav_css

    css = build_selected_nav_css("trust_score")

    assert '[data-testid="stIconMaterial"]' in css
    assert "color: #FFFFFF !important;" in css
