from app.ui.theme import build_theme_css


def test_sidebar_navigation_text_has_readable_contrast():
    css = build_theme_css()

    assert '[data-testid="stSidebarNavLink"] span' in css
    assert "color: #D8E5F5 !important;" in css


def test_selected_navigation_uses_primary_blue():
    from app.ui.theme import build_selected_nav_css

    css = build_selected_nav_css("trust_score")

    assert (
        '[data-testid="stSidebarNavLink"]'
        '[href$="/trust_score"]'
    ) in css

    assert (
        "background-color: var(--adt-primary) !important;"
        in css
    )
    assert "color: #FFFFFF !important;" in css

    home_css = build_selected_nav_css("")
    assert '[href$="/"]' in home_css
