from pathlib import Path


def test_upload_page_displays_core_journey():
    source = Path(
        "app/views/1_upload_dataset.py"
    ).read_text(encoding="utf-8-sig")

    assert "build_journey_html" in source
    assert 'active_step="Upload Dataset"' in source
    assert source.index("build_journey_html(") < source.index(
        "st.file_uploader("
    )
