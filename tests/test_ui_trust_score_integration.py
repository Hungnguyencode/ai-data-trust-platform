from __future__ import annotations

import ast
from pathlib import Path

TRUST_SCORE_PAGE = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "views"
    / "4_trust_score.py"
)


def test_trust_score_injects_theme_after_legacy_css():
    source = TRUST_SCORE_PAGE.read_text(
        encoding="utf-8-sig",
    )
    tree = ast.parse(source)

    theme_imported = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "app.ui.theme"
        and any(
            alias.name == "inject_theme_css"
            for alias in node.names
        )
        for node in tree.body
    )

    assert theme_imported

    css_calls = [
        node.value.func.id
        for node in tree.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id
        in {"inject_custom_css", "inject_theme_css"}
    ]

    assert css_calls == [
        "inject_custom_css",
        "inject_theme_css",
    ]



def test_trust_score_uses_shared_page_header():
    source = TRUST_SCORE_PAGE.read_text(
        encoding="utf-8-sig",
    )
    tree = ast.parse(source)

    header_imported = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "app.ui.layout"
        and any(
            alias.name == "render_page_header"
            for alias in node.names
        )
        for node in tree.body
    )

    assert header_imported

    header_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "render_page_header"
    ]

    assert len(header_calls) == 1

    header_call = header_calls[0]

    assert len(header_call.args) == 2
    assert isinstance(header_call.args[0], ast.Constant)
    assert header_call.args[0].value == "Data Trust Score"

    assert isinstance(header_call.args[1], ast.Constant)
    assert "dataset" in header_call.args[1].value

    legacy_header_exists = any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and '<div class="main-title">' in node.value
        for node in ast.walk(tree)
    )

    assert not legacy_header_exists
