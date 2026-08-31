from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}

FILE_TYPES = {
    ".csv": "CSV",
    ".xlsx": "Excel",
    ".xls": "Excel",
    ".json": "JSON",
}


def validate_file_extension(file_name: str) -> None:
    suffix = Path(file_name).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Định dạng file '{suffix}' chưa được hỗ trợ. "
            f"Các định dạng hợp lệ: {supported}"
        )


def get_file_type(file_name: str) -> str:
    validate_file_extension(file_name)
    return FILE_TYPES[Path(file_name).suffix.lower()]


def read_source_bytes(
    source: str | Path | BinaryIO,
) -> tuple[bytes, str, str]:
    """
    Normalize different input sources into raw bytes.

    Supported sources:
    - filesystem path
    - Streamlit UploadedFile
    - generic binary file-like object
    """
    if source is None:
        raise ValueError("Chưa có nguồn dữ liệu.")

    if isinstance(source, (str, Path)):
        path = Path(source)

        if not path.exists():
            raise ValueError(f"Không tìm thấy file: {path}")

        if not path.is_file():
            raise ValueError(f"Nguồn dữ liệu không phải file: {path}")

        file_name = path.name
        source_type = "filesystem"
        content = path.read_bytes()

    else:
        file_name = Path(
            str(getattr(source, "name", "uploaded_dataset.csv"))
        ).name
        source_type = "upload"

        if hasattr(source, "getvalue"):
            content = source.getvalue()

        elif hasattr(source, "read"):
            original_position = None

            if hasattr(source, "tell"):
                try:
                    original_position = source.tell()
                except Exception:
                    original_position = None

            content = source.read()

            if original_position is not None and hasattr(source, "seek"):
                try:
                    source.seek(original_position)
                except Exception:
                    pass

        else:
            raise ValueError(
                "Nguồn dữ liệu không hỗ trợ đọc binary."
            )

    if isinstance(content, str):
        content = content.encode("utf-8")

    if not isinstance(content, bytes):
        content = bytes(content)

    if not content:
        raise ValueError("File rỗng.")

    validate_file_extension(file_name)

    return content, file_name, source_type


def load_dataset_from_bytes(
    content: bytes,
    file_name: str,
) -> tuple[pd.DataFrame, str]:
    validate_file_extension(file_name)

    suffix = Path(file_name).suffix.lower()
    file_type = get_file_type(file_name)
    buffer = BytesIO(content)

    try:
        if suffix == ".csv":
            df = pd.read_csv(buffer)

        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(buffer)

        elif suffix == ".json":
            df = pd.read_json(buffer)

        else:
            raise ValueError(
                f"Định dạng file không hợp lệ: {suffix}"
            )

    except Exception as exc:
        raise ValueError(
            f"Không thể đọc file '{file_name}'. "
            f"Chi tiết lỗi: {exc}"
        ) from exc

    if df.empty:
        raise ValueError(
            "Dataset rỗng. Vui lòng cung cấp file có dữ liệu."
        )

    return df, file_type


def load_dataset(
    source: str | Path | BinaryIO,
) -> tuple[pd.DataFrame, str]:
    """
    Backward-compatible loader.

    Existing Streamlit pages can continue using:

        df, file_type = load_dataset(uploaded_file)

    while the ingestion service uses the lower-level byte functions.
    """
    content, file_name, _ = read_source_bytes(source)

    return load_dataset_from_bytes(
        content=content,
        file_name=file_name,
    )