import ast
from pathlib import Path


def get_header_title(path):
    source = Path(path).read_text(encoding="utf-8-sig")
    tree = ast.parse(source)

    headers = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "render_page_header"
    ]

    assert len(headers) == 1
    return ast.literal_eval(headers[0].args[0])


def test_quality_issues_enterprise_header():
    assert get_header_title(
        "app/views/3_quality_issues.py"
    ) == "Quality Issues"


def test_trust_score_enterprise_header():
    assert get_header_title(
        "app/views/4_trust_score.py"
    ) == "Data Trust Score"
