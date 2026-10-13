def test_core_journey_shows_four_steps():
    from app.ui.layout import build_journey_html

    html = build_journey_html(
        active_step="Upload Dataset"
    )

    for title in (
        "Upload Dataset",
        "Data Profile",
        "Quality Issues",
        "Trust Score",
    ):
        assert title in html

    assert html.count('aria-current="step"') == 1
    assert "Completed" not in html


def test_core_journey_has_enterprise_styling():
    from app.ui.theme import build_theme_css

    css = build_theme_css()

    assert ".adt-journey {" in css
    assert ".adt-journey-step {" in css
    assert ".adt-journey-number {" in css
    assert ".adt-journey-step.is-active" in css
    assert "flex-wrap: wrap;" in css
