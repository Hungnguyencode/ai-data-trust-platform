import ast
from pathlib import Path

SOURCE = Path("app/views/2_data_profile.py")


def test_data_profile_has_seven_bordered_cards():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
    bordered = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.With):
            continue

        for item in node.items:
            call = item.context_expr
            if not isinstance(call, ast.Call):
                continue
            if not isinstance(call.func, ast.Attribute):
                continue
            if call.func.attr != "container":
                continue

            has_border = any(
                kw.arg == "border"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is True
                for kw in call.keywords
            )

            if has_border:
                bordered.add(ast.unparse(call.func.value))

    expected = {
        "col1", "col2", "col3",
        "info_col1", "info_col2", "info_col3", "info_col4",
    }
    assert expected.issubset(bordered)


def test_filename_uses_readable_text_instead_of_metric():
    source = SOURCE.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)

    assert any(
        isinstance(node, ast.Call)
        and ast.unparse(node.func) == "st.write"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "file_name"
        for node in ast.walk(tree)
    )


def test_filename_caption_has_correct_vietnamese():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
    assert any(
        isinstance(node, ast.Call)
        and ast.unparse(node.func) == "st.caption"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "T\u00ean file"
        for node in ast.walk(tree)
    )
