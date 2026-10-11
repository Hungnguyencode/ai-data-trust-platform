def test_page_header_escapes_dynamic_html(monkeypatch):
    from app.ui import layout

    rendered = []

    monkeypatch.setattr(
        layout.st,
        "markdown",
        lambda body, **kwargs: rendered.append(body),
    )

    layout.render_page_header(
        "Trust <Score>",
        "Dataset <script>alert(1)</script>",
    )

    html = "\n".join(rendered)

    assert "<h1" in html
    assert "Trust &lt;Score&gt;" in html
    assert "&lt;script&gt;" in html
    assert "<script>" not in html



def test_page_header_omits_empty_subtitle(monkeypatch):
    from app.ui import layout

    rendered = []

    monkeypatch.setattr(
        layout.st,
        "markdown",
        lambda body, **kwargs: rendered.append(body),
    )

    layout.render_page_header(
        "Upload Dataset",
        "",
    )

    html = "\n".join(rendered)

    assert '<h1 class="adt-page-title">Upload Dataset</h1>' in html
    assert 'class="adt-page-subtitle"' not in html
