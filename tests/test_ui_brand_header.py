from app.ui.theme import build_theme_css


def test_sidebar_brand_header_matches_enterprise_sample():
    css = build_theme_css()

    # Separate dark branding region.
    assert '[data-testid="stSidebarHeader"]' in css
    assert "background-color: #102039;" in css

    # Enlarge the existing Streamlit logo.
    assert 'img[data-testid="stLogo"]' in css
    assert "height: 44px" in css
