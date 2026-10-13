import ast
from pathlib import Path


def test_upload_uses_shared_enterprise_header():
    source = Path(
        "app/views/1_upload_dataset.py"
    ).read_text(encoding="utf-8")

    assert any(
        isinstance(node, ast.ImportFrom)
        and node.module == "app.ui.layout"
        and any(alias.name == "render_page_header" for alias in node.names)
        for node in ast.walk(ast.parse(source))
    )
    assert "render_page_header(" in source
    assert 'st.title("📤 Upload Dataset")' not in source

    # Keep the existing upload functionality.
    assert "st.file_uploader(" in source
    assert "ingest_dataset(" in source
