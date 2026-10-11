import ast
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


def test_router_registers_brand_logo():
    source = (ROOT / "app" / "streamlit_app.py").read_text(
        encoding="utf-8-sig"
    )
    tree = ast.parse(source)

    calls = {
        ast.unparse(node.func): node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }

    assert "st.logo" in calls

    logo = calls["st.logo"]
    keywords = {
        item.arg: item.value
        for item in logo.keywords
    }

    assert "icon_image" in keywords
    assert isinstance(keywords.get("size"), ast.Constant)
    assert keywords["size"].value == "large"

    assert (
        calls["st.set_page_config"].lineno
        < logo.lineno
        < calls["st.navigation"].lineno
    )

    assert "brand_wordmark.svg" in source
    assert "brand_icon.svg" in source


def test_brand_logo_assets_are_valid_svg():
    assets = ROOT / "app" / "assets"

    for filename in ("brand_wordmark.svg", "brand_icon.svg"):
        path = assets / filename
        assert path.is_file(), f"Missing logo asset: {filename}"

        svg = ElementTree.parse(path).getroot()
        assert svg.tag.endswith("svg")
        assert svg.attrib.get("viewBox")

    wordmark = (
        assets / "brand_wordmark.svg"
    ).read_text(encoding="utf-8")

    assert "AI Data Trust" in wordmark
    assert "Platform" in wordmark


def test_brand_wordmark_uses_available_logo_height():
    path = ROOT / "app" / "assets" / "brand_wordmark.svg"
    svg = ElementTree.parse(path).getroot()

    view_box = [
        float(value)
        for value in svg.attrib["viewBox"].split()
    ]

    assert view_box == [0, 0, 240, 48]

    text_group = next(
        node
        for node in svg.iter()
        if node.attrib.get("font-family")
    )

    assert float(text_group.attrib["font-size"]) >= 20
