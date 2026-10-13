from pathlib import Path


def test_data_profile_uses_enterprise_header():
    source = Path(
        "app/views/2_data_profile.py"
    ).read_text(encoding="utf-8-sig")

    assert "render_page_header(" in source
    assert "st.title(" not in source
    assert 'active_step="Data Profile"' in source
