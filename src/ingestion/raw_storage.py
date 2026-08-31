from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_ROOT = PROJECT_ROOT / "data" / "raw"


def sanitize_file_name(file_name: str) -> str:
    """
    Strip both POSIX and Windows directory components from
    an externally supplied file name.

    Examples:
        ../../customers.csv -> customers.csv
        ..\\..\\customers.csv -> customers.csv
    """
    raw_name = str(file_name).strip()

    posix_name = PurePosixPath(raw_name).name
    safe_name = PureWindowsPath(posix_name).name.strip()

    if not safe_name or safe_name in {".", ".."}:
        raise ValueError("Tên file không hợp lệ.")

    return safe_name


def build_raw_artifact_path(
    file_name: str,
    content_sha256: str,
    raw_root: Path | str = DEFAULT_RAW_ROOT,
) -> Path:
    safe_name = sanitize_file_name(file_name)
    root = Path(raw_root)

    return root / content_sha256[:2] / content_sha256 / safe_name


def store_raw_artifact(
    content: bytes,
    file_name: str,
    content_sha256: str,
    raw_root: Path | str = DEFAULT_RAW_ROOT,
) -> Path:
    """
    Store the original source bytes without transforming them.

    Content-addressed storage makes the raw path deterministic for
    identical file content.
    """
    destination = build_raw_artifact_path(
        file_name=file_name,
        content_sha256=content_sha256,
        raw_root=raw_root,
    )

    destination.parent.mkdir(parents=True, exist_ok=True)

    if not destination.exists():
        destination.write_bytes(content)

    return destination