import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _page_config_calls(path: Path) -> list[ast.Call]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))

    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "st"
        and node.func.attr == "set_page_config"
    ]


def test_page_configuration_is_owned_by_entrypoint():
    entrypoint = PROJECT_ROOT / "app" / "streamlit_app.py"
    dashboard = PROJECT_ROOT / "app" / "dashboard.py"

    assert len(_page_config_calls(entrypoint)) == 1
    assert not _page_config_calls(dashboard)

    page_files = sorted(
        (PROJECT_ROOT / "app" / "views").glob("*.py")
    )
    assert len(page_files) == 14

    offenders = [
        path.name
        for path in page_files
        if _page_config_calls(path)
    ]

    assert not offenders, (
        "Pages still configure Streamlit independently: "
        + ", ".join(offenders)
    )
