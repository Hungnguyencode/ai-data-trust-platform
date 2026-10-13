from pathlib import Path


def test_trust_score_shows_journey():
    source = Path(
        "app/views/4_trust_score.py"
    ).read_text(encoding="utf-8-sig")

    assert "build_journey_html" in source
    assert 'active_step="Trust Score"' in source
