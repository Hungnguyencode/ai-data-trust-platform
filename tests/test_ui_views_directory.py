from pathlib import Path

from app.ui.navigation import PAGE_GROUPS, PAGE_METADATA


def test_explicit_navigation_uses_views_directory():
    project_root = Path(__file__).resolve().parents[1]
    views_dir = project_root / "app" / "views"
    legacy_dir = project_root / "app" / "pages"

    assert views_dir.is_dir(), "Expected app/views directory"
    assert not legacy_dir.exists(), "Legacy app/pages still exists"

    registered = [
        path
        for paths in PAGE_GROUPS.values()
        for path in paths
    ]

    assert len(registered) == len(set(registered)) == 14
    assert all(path.startswith("app/views/") for path in registered)
    assert set(PAGE_METADATA) == set(registered)

    actual = {
        path.relative_to(project_root).as_posix()
        for path in views_dir.glob("*.py")
    }

    assert actual == set(registered)
