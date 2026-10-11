import ast
from pathlib import Path


def test_entrypoint_is_a_navigation_router():
    project_root = Path(__file__).resolve().parents[1]
    entrypoint = project_root / "app" / "streamlit_app.py"

    tree = ast.parse(
        entrypoint.read_text(encoding="utf-8-sig")
    )

    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }

    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }

    assert "st.set_page_config" in calls
    assert "st.navigation" in calls
    assert "st.Page" in calls
    assert "page.run" in calls

    assert "HOME_PAGE" in names
    assert "PAGE_GROUPS" in names

    # Dashboard logic belongs in app/dashboard.py, not the router.
    assert "run_quality_checks" not in calls
    assert "calculate_data_trust_score" not in calls
    assert "render_metric_card" not in calls
    assert "st.stop" not in calls
