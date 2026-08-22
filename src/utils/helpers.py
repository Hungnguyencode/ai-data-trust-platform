from __future__ import annotations

from pathlib import Path


def get_project_root() -> Path:
    """
    Trả về đường dẫn gốc của project.
    """
    return Path(__file__).resolve().parents[2]


def ensure_directory(path: Path) -> None:
    """
    Tạo thư mục nếu chưa tồn tại.
    """
    path.mkdir(parents=True, exist_ok=True)