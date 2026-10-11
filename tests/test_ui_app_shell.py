import ast
from pathlib import Path

from app.ui.theme import build_theme_css


def test_router_injects_global_theme_before_page_run():
    root = Path(__file__).resolve().parents[1]
    source = (root / "app" / "streamlit_app.py").read_text(
        encoding="utf-8-sig"
    )
    tree = ast.parse(source)

    theme_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "app.ui.theme"
    ]

    assert len(theme_imports) == 1
    assert any(
        alias.name == "inject_theme_css"
        for alias in theme_imports[0].names
    )

    calls = {
        ast.unparse(node.func): node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }

    assert (
        calls["st.navigation"]
        < calls["inject_theme_css"]
        < calls["page.run"]
    )


def test_theme_css_styles_sidebar_and_workspace():
    css = build_theme_css()

    assert '[data-testid="stSidebar"]' in css
    assert '[data-testid="stAppViewContainer"]' in css

    assert "var(--adt-sidebar-background)" in css
    assert "var(--adt-workspace-background)" in css
