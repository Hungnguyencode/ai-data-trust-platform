def test_theme_colors_match_design_system():
    from app.ui.theme import COLORS

    assert COLORS["sidebar_background"] == "#172A44"
    assert COLORS["workspace_background"] == "#F7F9FC"
    assert COLORS["surface_background"] == "#FFFFFF"
    assert COLORS["primary"] == "#2563EB"



def test_build_theme_css_exposes_design_tokens():
    from app.ui.theme import COLORS, build_theme_css

    css = build_theme_css()

    for name, color in COLORS.items():
        css_variable = (
            f"--adt-{name.replace('_', '-')}: {color};"
        )
        assert css_variable in css

    assert ".adt-page-header" in css
    assert ".adt-page-title" in css
    assert ".adt-page-subtitle" in css


def test_inject_theme_css_renders_stylesheet(monkeypatch):
    import streamlit as st

    from app.ui.theme import (
        build_theme_css,
        inject_theme_css,
    )

    calls = []

    def fake_markdown(body, **kwargs):
        calls.append((body, kwargs))

    monkeypatch.setattr(st, "markdown", fake_markdown)

    inject_theme_css()

    assert len(calls) == 1

    html, kwargs = calls[0]

    assert html.startswith("<style>")
    assert html.endswith("</style>")
    assert build_theme_css() in html
    assert kwargs["unsafe_allow_html"] is True
