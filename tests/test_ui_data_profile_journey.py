from pathlib import Path


def test_data_profile_shows_journey():
    source = Path(
        "app/views/2_data_profile.py"
    ).read_text(encoding="utf-8-sig")

    assert "build_journey_html" in source
    assert 'active_step="Data Profile"' in source
