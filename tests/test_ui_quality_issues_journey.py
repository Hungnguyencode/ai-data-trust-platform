from pathlib import Path


def test_quality_issues_shows_journey():
    source = Path(
        "app/views/3_quality_issues.py"
    ).read_text(encoding="utf-8-sig")

    assert "build_journey_html" in source
    assert 'active_step="Quality Issues"' in source
