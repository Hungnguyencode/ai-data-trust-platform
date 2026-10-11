import ast
from pathlib import Path


def test_extracted_dashboard_preserves_existing_behavior():
    project_root = Path(__file__).resolve().parents[1]
    dashboard_path = project_root / "app" / "dashboard.py"

    source = dashboard_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)

    calls = {
        ast.unparse(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }

    required_calls = {
        "st.stop",
        "render_metric_card",
        "render_recommendation_box",
        "run_quality_checks",
        "calculate_data_trust_score",
    }

    assert required_calls <= calls
    assert "st.set_page_config" not in calls

    string_constants = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    }

    required_state_keys = {
        "current_df",
        "current_quality_report",
        "current_trust_score_report",
    }

    assert required_state_keys <= string_constants

    for section in (
        "Data Profiling",
        "Quality Checking",
        "Trust Scoring",
        "Dashboard Overview",
        "Quick Diagnostics",
        "Recommendation",
    ):
        assert section in source
