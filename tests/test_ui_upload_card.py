import ast
from pathlib import Path


def test_upload_widget_is_inside_bordered_card():
    source = Path(
        "app/views/1_upload_dataset.py"
    ).read_text(encoding="utf-8-sig")

    tree = ast.parse(source)

    assert any(
        isinstance(node, ast.With)
        and ast.unparse(node.items[0].context_expr)
        == "st.container(border=True)"
        and any(
            isinstance(child, ast.Call)
            and ast.unparse(child.func) == "st.file_uploader"
            for child in ast.walk(node)
        )
        for node in ast.walk(tree)
    )

def test_upload_dropzone_has_enterprise_styling():
    from app.ui.theme import build_theme_css

    css = build_theme_css()

    assert '[data-testid="stFileUploaderDropzone"]' in css
    assert "border: 2px dashed #93C5FD !important;" in css
    assert "background-color: #F0F6FF !important;" in css
    assert "min-height: 160px;" in css

def test_upload_browse_button_uses_brand_style():
    from app.ui.theme import build_theme_css

    css = build_theme_css()

    assert '[data-testid="stFileUploaderDropzone"] button {' in css
    assert "background-color: #2563EB !important;" in css
    assert "color: #FFFFFF !important;" in css
    assert '[data-testid="stFileUploaderDropzone"] button:hover {' in css
